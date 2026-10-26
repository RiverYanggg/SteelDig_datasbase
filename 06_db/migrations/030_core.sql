-- ============================================================================
-- 030 事实层 core —— 实体表(列) + JSONB(保真) + trace
-- ----------------------------------------------------------------------------
-- 设计原则 1：只把「身份 + 外键 + 会被 WHERE 过滤的维度」提升为列，
--             其余整体 JSONB 保真。拍平 100+ 字段会碎成一堆半空表；
--             全 JSONB 又没法过滤。
-- 设计原则 2：保留 data / trace 分离。科学事实（sample_data）与
--             证据溯源（sample_trace）两张表，通过 (paper_id, sample_id, path) 关联。
-- 设计原则 4：paper 内实体一律复合键 (paper_id, entity_id)。
--
-- 每张"事实表"都保留 payload jsonb = 产物原文，列只是它的可查询投影。
-- 因此任何列级 bug 都可以从 lake + payload 重建，不会丢数据。
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 论文
-- ---------------------------------------------------------------------------
CREATE TABLE core.paper (
    paper_id        text PRIMARY KEY,
    doi             text UNIQUE,
    title           text NOT NULL,
    abstract        text,
    journal         text,
    year            integer,
    research_type   text,                               -- experimental | computational | review | ...
    domain          text DEFAULT 'materials',
    keywords        text[] NOT NULL DEFAULT '{}',
    authors         text[] NOT NULL DEFAULT '{}',
    paper_scope     text,
    page_count      integer,
    block_count     integer,
    figure_count    integer,
    section_headings jsonb,
    run_id          text REFERENCES ops.run(run_id),
    source_dir      text,                               -- 湖内原始目录（可回溯到提取批次）
    qa_flags        text[] NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON core.paper (year);
CREATE INDEX ON core.paper USING gin (keywords);
CREATE INDEX ON core.paper USING gin (title gin_trgm_ops);
COMMENT ON TABLE  core.paper IS '论文级实体：一行一篇，是全部下游实体的根';
COMMENT ON COLUMN core.paper.qa_flags IS '质量门禁命中的 warn 级标记（error 级会阻断入库），见 ops.qa_issue';

-- ---------------------------------------------------------------------------
-- 证据块（全库地基，所有下游 block_id 回指这里）
-- ---------------------------------------------------------------------------
CREATE TABLE core.evidence_block (
    paper_id        text   NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    block_id        text   NOT NULL,
    ordinal         integer NOT NULL,
    kind            text   NOT NULL,      -- heading | text | caption | table | equation | reference
    page_idx        integer,
    section         text,
    text            text   NOT NULL,
    char_len        integer NOT NULL,
    in_reading_view boolean NOT NULL DEFAULT true,
    content_sha256  text   NOT NULL,
    tsv             tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(text,''))) STORED,
    PRIMARY KEY (paper_id, block_id)
);
CREATE INDEX ON core.evidence_block (paper_id, ordinal);
CREATE INDEX ON core.evidence_block (paper_id, kind);
CREATE INDEX ON core.evidence_block USING gin (tsv);
CREATE INDEX ON core.evidence_block (content_sha256);
COMMENT ON TABLE core.evidence_block IS
  'MinerU/预处理切分出的证据块，b0001…bNNNN。全库唯一的溯源起点：'
  'core.sample_trace.block_ids / core.figure_observation.block_ids 都必须能在这里命中';

-- ---------------------------------------------------------------------------
-- 合金（成分的结构化来源）
-- ---------------------------------------------------------------------------
CREATE TABLE core.alloy (
    paper_id         text NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    alloy_id         text NOT NULL,
    name             text,
    base_element     text,
    elements         text[] NOT NULL DEFAULT '{}',      -- 参与成分的元素符号（不含 Bal.）
    formula          text,                              -- 按质量分数排序的化学式 Fe28Mn10Al0.8C
    formula_alpha    text,                              -- 按字母序 Fe28Mn10Al0.8C → Al0.8CFe28Mn10
    chemsys          text,                              -- 字母序元素体系 Al-C-Fe-Mn（仿 Materials Project）
    n_elements       integer,
    aliases          text[] NOT NULL DEFAULT '{}',
    description      text,
    notes            text,
    family_key       text REFERENCES canon.alloy_family(family_key),
    source_block_ids text[] NOT NULL DEFAULT '{}',
    is_stub          boolean NOT NULL DEFAULT false,    -- 由 sample 引用反推出来的占位合金
    payload          jsonb NOT NULL,
    PRIMARY KEY (paper_id, alloy_id)
);
CREATE INDEX ON core.alloy USING gin (elements);
CREATE INDEX ON core.alloy (chemsys);
CREATE INDEX ON core.alloy (family_key);
CREATE INDEX ON core.alloy USING gin (name gin_trgm_ops);
COMMENT ON TABLE  core.alloy IS '论文内合金：名义成分的结构化来源，建库时把 wt%/at% 提升为 core.alloy_element';
COMMENT ON COLUMN core.alloy.is_stub IS 'true 表示 discover 未声明该合金、但被 sample 引用，为保持外键完整性补建的空壳';

CREATE TABLE core.alloy_element (
    paper_id    text NOT NULL,
    alloy_id    text NOT NULL,
    element     text NOT NULL,                          -- 元素符号，可为未收录元素
    weight_pct  numeric(9,4),
    atomic_pct  numeric(9,4),
    raw_wt      text,                                   -- 原文写法："28" / "Bal." / "~10"
    is_balance  boolean NOT NULL DEFAULT false,
    PRIMARY KEY (paper_id, alloy_id, element),
    FOREIGN KEY (paper_id, alloy_id) REFERENCES core.alloy(paper_id, alloy_id) ON DELETE CASCADE
);
CREATE INDEX ON core.alloy_element (element) WHERE weight_pct IS NOT NULL;
CREATE INDEX ON core.alloy_element (element, weight_pct);
COMMENT ON TABLE core.alloy_element IS
  '成分长表（元素维度）：支持"含 Al ≥ 8 wt% 的所有钢"这类仿 MP 的元素过滤与 chemsys 聚合';

-- ---------------------------------------------------------------------------
-- 工艺（含工艺谱系 DAG）
-- ---------------------------------------------------------------------------
CREATE TABLE core.process (
    paper_id         text NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    process_id       text NOT NULL,
    name             text,
    state_label      text,
    aliases          text[] NOT NULL DEFAULT '{}',
    description      text,
    notes            text,
    source_block_ids text[] NOT NULL DEFAULT '{}',
    is_stub          boolean NOT NULL DEFAULT false,
    payload          jsonb NOT NULL,
    PRIMARY KEY (paper_id, process_id)
);
CREATE INDEX ON core.process USING gin (aliases);
COMMENT ON TABLE core.process IS '论文内工艺路线（状态态）：discover.processes 的投影；工艺步骤链见 core.processing_step';

CREATE TABLE core.process_edge (
    paper_id          text NOT NULL,
    child_process_id  text NOT NULL,
    parent_process_id text NOT NULL,
    PRIMARY KEY (paper_id, child_process_id, parent_process_id),
    FOREIGN KEY (paper_id, child_process_id)  REFERENCES core.process(paper_id, process_id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id, parent_process_id) REFERENCES core.process(paper_id, process_id) ON DELETE CASCADE
);
COMMENT ON TABLE core.process_edge IS '工艺谱系树/DAG 的边（discover.processes[].parent_process_ids），可递归查询前驱工序';

-- ---------------------------------------------------------------------------
-- 样品（研究对象）
-- ---------------------------------------------------------------------------
CREATE TABLE core.sample (
    paper_id         text NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    sample_id        text NOT NULL,                      -- alloy_id + "__" + process_id
    alloy_id         text NOT NULL,
    process_id       text NOT NULL,
    label            text,                               -- LN / HN / A1 …
    aliases          text[] NOT NULL DEFAULT '{}',
    source_block_ids text[] NOT NULL DEFAULT '{}',
    payload          jsonb NOT NULL,
    PRIMARY KEY (paper_id, sample_id),
    FOREIGN KEY (paper_id, alloy_id)   REFERENCES core.alloy(paper_id, alloy_id),
    FOREIGN KEY (paper_id, process_id) REFERENCES core.process(paper_id, process_id)
);
CREATE INDEX ON core.sample (alloy_id);
CREATE INDEX ON core.sample (process_id);
COMMENT ON TABLE core.sample IS '样品 = 合金 × 工艺（sample_id = alloy_id + "__" + process_id），是性能/组织/证据的挂载点';

-- ---------------------------------------------------------------------------
-- 科学事实层（纯数据版）与溯源层（trace）—— 原则 2
-- ---------------------------------------------------------------------------
CREATE TABLE core.sample_data (
    paper_id      text   NOT NULL,
    sample_id     text   NOT NULL,
    run_id        text   NOT NULL REFERENCES ops.run(run_id),
    payload       jsonb  NOT NULL,                       -- <sample_id>.data.json 原文
    payload_bytes integer,
    sha256        text   NOT NULL,
    is_latest     boolean NOT NULL DEFAULT true,
    loaded_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (paper_id, sample_id, run_id),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX ON core.sample_data (paper_id, sample_id) WHERE is_latest;
COMMENT ON TABLE core.sample_data IS
  '科学事实层（保真 JSONB）。多 run 并存时靠 is_latest 一键取当前版；历史版永不覆盖';

CREATE TABLE core.sample_trace (
    paper_id   text NOT NULL,
    sample_id  text NOT NULL,
    run_id     text NOT NULL REFERENCES ops.run(run_id),
    path       text NOT NULL,                            -- JSON Pointer：$.processing_steps[1].temperature
    reason     text,
    block_ids  text[] NOT NULL DEFAULT '{}',
    status     text NOT NULL CHECK (status IN ('ok','insufficient')),
    depth      integer,
    PRIMARY KEY (paper_id, sample_id, run_id, path),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE INDEX ON core.sample_trace USING gin (block_ids);
CREATE INDEX ON core.sample_trace (paper_id, sample_id, status);
COMMENT ON TABLE core.sample_trace IS
  '证据溯源层：每个标量叶子一条。与 sample_data 通过 (paper_id, sample_id, path) 关联，'
  'path 即 JSON Pointer，可直接在 payload 上定位到原始值（校验见 tests/test_integrity.py）';

-- ---------------------------------------------------------------------------
-- 研究对象词条（人读向，RAG 语料）
-- ---------------------------------------------------------------------------
CREATE TABLE core.sample_wiki (
    paper_id       text NOT NULL,
    sample_id      text NOT NULL,
    run_id         text NOT NULL REFERENCES ops.run(run_id),
    summary        text,
    mechanisms     text[] NOT NULL DEFAULT '{}',
    n_mechanisms   integer,
    conclusions    text,
    payload        jsonb NOT NULL,
    content        text,                                 -- 全部自然语言段拼接（原文）
    content_seg    text,                                 -- 供检索的分词文本（jieba）
    PRIMARY KEY (paper_id, sample_id, run_id),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
COMMENT ON TABLE core.sample_wiki IS '全中文词条：语义检索/RAG 的核心语料；"可查询维度"不放这里，放 property_value';

-- ---------------------------------------------------------------------------
-- 工艺步骤链（可过滤的工艺维度）
-- ---------------------------------------------------------------------------
CREATE TABLE core.processing_step (
    paper_id       text NOT NULL,
    sample_id      text NOT NULL,
    seq            integer NOT NULL,
    step_id        text,
    step_type      text,                                 -- heat treatment / deformation / cooling …
    method         text,
    temperature_raw text,
    temperature_k  numeric,                              -- 归一化到 K
    duration_raw   text,
    duration_s     numeric,                              -- 归一化到 s
    atmosphere     text,
    cooling_medium text,
    heating_rate   text,
    reduction_ratio text,
    notes          text,
    source_block_ids text[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (paper_id, sample_id, seq),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE INDEX ON core.processing_step (step_type);
CREATE INDEX ON core.processing_step (temperature_k);
COMMENT ON TABLE core.processing_step IS '工艺链的逐步展开（熔炼→锻造→均匀化→…→退火），是"可结构化过滤"的工艺维度';

-- ---------------------------------------------------------------------------
-- 相/组织（phases_present 结构化）
-- ---------------------------------------------------------------------------
CREATE TABLE core.phase (
    paper_id             text NOT NULL,
    sample_id            text NOT NULL,
    microstructure_id    text NOT NULL,
    idx                  integer NOT NULL,
    phase_name           text NOT NULL,
    phase_key            text REFERENCES canon.phase(phase_key),
    crystal_structure    text,
    volume_fraction_raw  text,
    volume_fraction_pct  numeric(7,4),
    morphology           text,
    grain_size_raw       text,
    grain_size_um        numeric,
    texture              text,
    source_block_ids     text[] NOT NULL DEFAULT '{}',
    payload              jsonb,
    PRIMARY KEY (paper_id, sample_id, microstructure_id, idx),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE INDEX ON core.phase (phase_key);
CREATE INDEX ON core.phase (volume_fraction_pct);
CREATE INDEX ON core.phase USING gin (phase_name gin_trgm_ops);
COMMENT ON TABLE core.phase IS '组织中的相：相名 + 体积分数 + 晶粒尺寸，是"相"维度的可过滤列（对应下阶段计划第 2 条）';

-- ---------------------------------------------------------------------------
-- 性能量（科学事实的数值投影）—— 全库最重要的可查询表
-- ----------------------------------------------------------------------------
-- 把 "427–513 MPa" / "3.5 μm" / "1050 °C" / "56.9%" 解析为
-- {value_kind, value_low, value_high, unit_canonical, value_canonical}，
-- 从而支持真正的数值区间查询（而不是字符串 LIKE）。
-- ---------------------------------------------------------------------------
CREATE TABLE core.property_value (
    paper_id            text NOT NULL,
    sample_id           text NOT NULL,
    run_id              text NOT NULL REFERENCES ops.run(run_id),
    path                text NOT NULL,                   -- JSON Pointer into sample_data.payload
    section             text NOT NULL,                   -- mechanical / physical / chemical / radiation_properties / other
    group_path          text,                            -- tensile_properties.yield_strength
    metric              text NOT NULL,                   -- yield_strength
    idx                 integer NOT NULL DEFAULT 0,
    value_raw           text,
    value_kind          text NOT NULL CHECK (value_kind IN
                          ('numeric','range','open_low','open_high','qualitative','text',
                           'boolean','missing')),
    value_num           numeric,
    value_low           numeric,
    value_high          numeric,
    value_unit          text,                            -- 原文单位
    unit_canonical      text,                            -- 归一化单位
    value_canonical     numeric,                         -- 单值/中点（归一化后）
    value_low_canonical numeric,
    value_high_canonical numeric,
    qualifier           text,                            -- ~ / ≈ / up to / not less than …
    uncertainty_raw     text,
    direction           text,
    block_status        text,                            -- ok | insufficient（回指 trace）
    conditions          jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_block_ids    text[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (paper_id, sample_id, run_id, path),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE INDEX ON core.property_value (metric, value_canonical);
CREATE INDEX ON core.property_value (metric) WHERE value_canonical IS NOT NULL;
CREATE INDEX ON core.property_value (paper_id, sample_id);
CREATE INDEX ON core.property_value (unit_canonical, metric);
COMMENT ON TABLE  core.property_value IS
  '性能量长表：一个标量一行。value_kind 区分数值/区间/开区间/定性，'
  'value_canonical 已做单位换算（应力→MPa、尺寸→μm、温度→K、分数→%），可跨论文直接比较';
COMMENT ON COLUMN core.property_value.path IS '与 core.sample_trace.path 同一命名空间，二者可 JOIN 做"值-证据"联查';

-- ---------------------------------------------------------------------------
-- 对比性能 / 表征 / 未归类发现
-- ---------------------------------------------------------------------------
CREATE TABLE core.performance (
    paper_id          text NOT NULL,
    sample_id         text NOT NULL,
    perf_id           text,
    benchmark_sample  text,
    benchmark_alloy   text,
    comparison_metric text,
    improvement       text,
    service_conditions text,
    lifetime          text,
    payload           jsonb NOT NULL,
    PRIMARY KEY (paper_id, sample_id, perf_id),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
COMMENT ON TABLE core.performance IS '对比性能（benchmark 对照），常用于"相对提升 X%"这类表述';

CREATE TABLE core.characterization (
    paper_id     text NOT NULL,
    sample_id    text NOT NULL,
    idx          integer NOT NULL,
    char_id      text,
    technique    text,
    technique_key text REFERENCES canon.characterization_technique(technique_key),
    instrument   text,
    conditions   text,
    purpose      text,
    key_findings text,
    payload      jsonb,
    PRIMARY KEY (paper_id, sample_id, idx),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
CREATE INDEX ON core.characterization (technique_key);
COMMENT ON TABLE core.characterization IS '表征手段（SEM/EBSD/XRD/拉伸…），支撑"哪些样品做过 EBSD"式过滤';

CREATE TABLE core.unmapped_finding (
    paper_id         text NOT NULL,
    sample_id        text NOT NULL,
    idx              integer NOT NULL,
    text             text NOT NULL,
    source_block_ids text[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (paper_id, sample_id, idx),
    FOREIGN KEY (paper_id, sample_id) REFERENCES core.sample(paper_id, sample_id) ON DELETE CASCADE
);
COMMENT ON TABLE core.unmapped_finding IS '无法归入既有 schema 的发现：既是知识残渣，也是 schema 迭代的输入信号';

-- ---------------------------------------------------------------------------
-- 图表（figure / table 合并建模，用 kind 区分）
-- ---------------------------------------------------------------------------
CREATE TABLE core.figure (
    paper_id        text NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    figure_id       text NOT NULL,                       -- figure_001 | table_001
    kind            text NOT NULL CHECK (kind IN ('figure','table')),
    label           text,                                -- 题注原文
    family          text,
    image_type      text,
    description     text,                                -- 120–220 词视觉描述（语义检索语料）
    confidence      numeric(3,2),
    n_subfigures    integer NOT NULL DEFAULT 0,
    n_observations  integer NOT NULL DEFAULT 0,
    n_measured      integer NOT NULL DEFAULT 0,
    measured_quantities jsonb,
    sample_hints    jsonb,
    image_paths     text[] NOT NULL DEFAULT '{}',
    block_ids       text[] NOT NULL DEFAULT '{}',         -- 对齐后的 caption + citation 真实 block
    page_idx        integer,
    ordinal         integer,
    payload         jsonb NOT NULL,
    PRIMARY KEY (paper_id, figure_id)
);
CREATE INDEX ON core.figure (kind);
CREATE INDEX ON core.figure USING gin (block_ids);
CREATE INDEX ON core.figure USING gin (description gin_trgm_ops);
COMMENT ON TABLE core.figure IS '图片与表格：figure_id 来自 preprocess/image_groups.json，block_ids 已做过合成 id → 真实 block 的对齐';

CREATE TABLE core.figure_panel (
    paper_id   text NOT NULL,
    figure_id  text NOT NULL,
    idx        integer NOT NULL,
    panel      text,
    description text,
    PRIMARY KEY (paper_id, figure_id, idx),
    FOREIGN KEY (paper_id, figure_id) REFERENCES core.figure(paper_id, figure_id) ON DELETE CASCADE
);
COMMENT ON TABLE core.figure_panel IS '组图的子图（panel）';

CREATE TABLE core.figure_observation (
    paper_id       text NOT NULL,
    figure_id      text NOT NULL,
    idx            integer NOT NULL,
    observation    text NOT NULL,
    source         text,                                 -- visual | caption | citation
    confidence     numeric(3,2),
    evidence_raw   text[] NOT NULL DEFAULT '{}',          -- 产物原始 id（可能为合成 id）
    block_ids      text[] NOT NULL DEFAULT '{}',          -- 对齐后的真实 block
    block_status   text NOT NULL DEFAULT 'unresolved',    -- ok | partial | unresolved
    PRIMARY KEY (paper_id, figure_id, idx),
    FOREIGN KEY (paper_id, figure_id) REFERENCES core.figure(paper_id, figure_id) ON DELETE CASCADE
);
CREATE INDEX ON core.figure_observation USING gin (block_ids);
CREATE INDEX ON core.figure_observation (block_status);
COMMENT ON TABLE core.figure_observation IS
  '单图观察项。evidence_raw 保留产物原样，block_ids 是对齐结果，对齐过程见 ops.block_id_resolution';

-- ---------------------------------------------------------------------------
-- 公式
-- ---------------------------------------------------------------------------
CREATE TABLE core.equation (
    paper_id      text NOT NULL REFERENCES core.paper(paper_id) ON DELETE CASCADE,
    equation_id   text NOT NULL,
    block_id      text,                                  -- 真实 block，可精确回指正文
    equation_number text,
    is_image      boolean NOT NULL DEFAULT false,
    latex         text,
    latex_hint    text,
    purpose       text,
    applicability text,
    symbols       jsonb NOT NULL DEFAULT '[]'::jsonb,
    n_symbols     integer NOT NULL DEFAULT 0,
    payload       jsonb NOT NULL,
    PRIMARY KEY (paper_id, equation_id)
);
CREATE INDEX ON core.equation (paper_id, block_id);
COMMENT ON TABLE core.equation IS '公式：latex + 符号表。后期可对 latex 归一化后做全库去重（同一条公式跨论文复用很常见）';
