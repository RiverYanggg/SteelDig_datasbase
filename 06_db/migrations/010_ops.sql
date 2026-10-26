-- ============================================================================
-- 010 治理层 ops —— 版本、入库日志、质量门禁、溯源对齐审计
-- ----------------------------------------------------------------------------
-- 设计原则 3：多 run / 多模型是常态，必须内建版本。
--   每条事实带 run_id，历史可查、当前可一键取。
-- run 的粒度 = (提取批次 × 模型)，与 68 篇资产的真实来源一一对应：
--   run_0915_pro / run_0917_pro / run_0919_pro / run_1009_flash
-- ============================================================================

CREATE TABLE ops.run (
    run_id          text PRIMARY KEY,
    label           text NOT NULL,
    extractor       text NOT NULL DEFAULT 'agentic-extractor-2.0',
    model           text,
    source_batch    text,
    dataset_version text NOT NULL,
    schema_versions jsonb NOT NULL DEFAULT '{}'::jsonb,
    paper_count     integer NOT NULL DEFAULT 0,
    is_current      boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE  ops.run IS '一次"提取批次×模型"的产物版本；core 表的事实均通过 run_id 归属到这里';
COMMENT ON COLUMN ops.run.schema_versions IS '该 run 内各产物 schema_version 的去重集合，如 {"sample":"sample-rich-v1"}';
COMMENT ON COLUMN ops.run.is_current IS '当前权威版本。多 run 并存时历史仍可查，API 默认只读 is_current=true';

-- ---------------------------------------------------------------------------
-- 入库执行记录（可重放、可对比）
-- ---------------------------------------------------------------------------
CREATE TABLE ops.ingest_run (
    ingest_id    bigserial PRIMARY KEY,
    label        text,
    status       text NOT NULL DEFAULT 'running',      -- running | success | failed
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    params       jsonb NOT NULL DEFAULT '{}'::jsonb,   -- 命令行参数快照
    stats        jsonb NOT NULL DEFAULT '{}'::jsonb,   -- 各表行数
    tool_version text,
    host         text DEFAULT inet_client_addr()::text
);
COMMENT ON TABLE ops.ingest_run IS '每次 ETL 执行一行；stats 记录各表最终行数，便于回归对比';

CREATE TABLE ops.ingest_log (
    ingest_id   bigint NOT NULL REFERENCES ops.ingest_run(ingest_id) ON DELETE CASCADE,
    paper_id    text   NOT NULL,
    run_id      text   REFERENCES ops.run(run_id),
    status      text   NOT NULL,                        -- loaded | skipped | failed
    rows        jsonb  NOT NULL DEFAULT '{}'::jsonb,    -- 本篇写入各表行数
    objects     integer NOT NULL DEFAULT 0,             -- 落湖对象数
    duration_ms integer,
    error       text,
    PRIMARY KEY (ingest_id, paper_id)
);
COMMENT ON TABLE ops.ingest_log IS '逐篇入库结果；失败不影响其他篇，可单独重跑';

-- ---------------------------------------------------------------------------
-- 质量门禁：规则目录 + 问题实例
-- ---------------------------------------------------------------------------
CREATE TABLE ops.qa_rule (
    rule_code   text PRIMARY KEY,
    severity    text NOT NULL CHECK (severity IN ('error','warn','info')),
    title       text NOT NULL,
    description text
);
COMMENT ON TABLE ops.qa_rule IS '质量规则目录；规则实现见 etl/steeldig_db/qa.py';

CREATE TABLE ops.qa_issue (
    issue_id   bigserial PRIMARY KEY,
    ingest_id  bigint REFERENCES ops.ingest_run(ingest_id) ON DELETE CASCADE,
    rule_code  text   NOT NULL REFERENCES ops.qa_rule(rule_code),
    severity   text   NOT NULL,
    paper_id   text,
    subject    text,                                   -- 具体对象：sample_id / figure_001 / 字段路径
    message    text NOT NULL,
    detail     jsonb  NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON ops.qa_issue (paper_id);
CREATE INDEX ON ops.qa_issue (rule_code, severity);
COMMENT ON TABLE ops.qa_issue IS '每条质量问题一行；error 级问题阻断该篇发布，warn 级仅提示';

-- ---------------------------------------------------------------------------
-- block_id 对齐审计（对应《数据库建立》2.5 的"溯源命名不一致"）
-- ----------------------------------------------------------------------------
-- figure 的 observation.evidence.id 里存在大量合成 id
-- （b_caption_002 / b_citing_002 / caption_figure_003 …），而 evidence_blocks
-- 里的真实 id 只有 bNNNN 一种形态。入库前必须做一次对齐，对齐过程全量留痕。
-- ---------------------------------------------------------------------------
CREATE TABLE ops.block_id_resolution (
    ingest_id         bigint NOT NULL REFERENCES ops.ingest_run(ingest_id) ON DELETE CASCADE,
    paper_id          text   NOT NULL,
    src_table         text   NOT NULL,          -- core.figure_observation / core.sample_trace ...
    src_id            text   NOT NULL,          -- figure_002#obs3 / $.processing_steps[0]
    raw_id            text   NOT NULL,          -- 产物里写的原始 id
    method            text   NOT NULL,          -- direct | figure_group | fuzzy | unresolved
    confidence        numeric(3,2) NOT NULL,
    resolved_block_ids text[] NOT NULL DEFAULT '{}',
    note              text,
    PRIMARY KEY (ingest_id, paper_id, src_table, src_id, raw_id)
);
CREATE INDEX ON ops.block_id_resolution (paper_id, method);
COMMENT ON TABLE ops.block_id_resolution IS
  '每个原始 evidence id 的对齐结果。method=direct 表示原文即 bNNNN 且真实存在；'
  'figure_group 表示通过 image_groups 的 caption/citation 列表还原；unresolved 表示无法还原（值保留、标记弱溯源）';
