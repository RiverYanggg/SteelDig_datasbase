# 数据字典

> 本文件由 `06_db/ops/gen_docs.py` 从 `information_schema` 自动生成，
> 与数据库实现保持一致。修改表结构后请重新生成。

## 治理层 ops

### `ops.block_id_resolution` — 12,793 行

> 每个原始 evidence id 的对齐结果。method=direct 表示原文即 bNNNN 且真实存在；figure_group 表示通过 image_groups 的 caption/citation 列表还原；unresolved 表示无法还原（值保留、标记弱溯源）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `ingest_id` | `bigint` | 否 | ✔ |  |  |
| `paper_id` | `text` | 否 | ✔ |  |  |
| `src_table` | `text` | 否 | ✔ |  |  |
| `src_id` | `text` | 否 | ✔ |  |  |
| `raw_id` | `text` | 否 | ✔ |  |  |
| `method` | `text` | 否 |  |  |  |
| `confidence` | `numeric(3,2)` | 否 |  |  |  |
| `resolved_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `note` | `text` | 是 |  |  |  |

### `ops.ingest_log` — 895 行

> 逐篇入库结果；失败不影响其他篇，可单独重跑

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `ingest_id` | `bigint` | 否 | ✔ |  |  |
| `paper_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 是 |  |  |  |
| `status` | `text` | 否 |  |  |  |
| `rows` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `objects` | `integer` | 否 |  | `0` |  |
| `duration_ms` | `integer` | 是 |  |  |  |
| `error` | `text` | 是 |  |  |  |

### `ops.ingest_run` — 91 行

> 每次 ETL 执行一行；stats 记录各表最终行数，便于回归对比

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `ingest_id` | `bigint` | 否 | ✔ | `nextval('ops.ingest_run_ingest_id_seq'::regclass)` |  |
| `label` | `text` | 是 |  |  |  |
| `status` | `text` | 否 |  | `'running'::text` |  |
| `started_at` | `timestamp with time zone` | 否 |  | `now()` |  |
| `finished_at` | `timestamp with time zone` | 是 |  |  |  |
| `params` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `stats` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `tool_version` | `text` | 是 |  |  |  |
| `host` | `text` | 是 |  | `(inet_client_addr())::text` |  |

### `ops.qa_issue` — 844 行

> 当前质量问题快照：按 (rule_code, paper_id, subject) 唯一，重跑更新而非追加

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `issue_id` | `bigint` | 否 | ✔ | `nextval('ops.qa_issue_issue_id_seq'::regclass)` |  |
| `ingest_id` | `bigint` | 是 |  |  |  |
| `rule_code` | `text` | 否 |  |  |  |
| `severity` | `text` | 否 |  |  |  |
| `paper_id` | `text` | 否 |  | `''::text` |  |
| `subject` | `text` | 否 |  | `''::text` |  |
| `message` | `text` | 否 |  |  |  |
| `detail` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

### `ops.qa_rule` — 12 行

> 质量规则目录；规则实现见 etl/steeldig_db/qa.py

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `rule_code` | `text` | 否 | ✔ |  |  |
| `severity` | `text` | 否 |  |  |  |
| `title` | `text` | 否 |  |  |  |
| `description` | `text` | 是 |  |  |  |

### `ops.run` — 4 行

> 一次"提取批次×模型"的产物版本；core 表的事实均通过 run_id 归属到这里

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `run_id` | `text` | 否 | ✔ |  |  |
| `label` | `text` | 否 |  |  |  |
| `extractor` | `text` | 否 |  | `'agentic-extractor-2.0'::text` |  |
| `model` | `text` | 是 |  |  |  |
| `source_batch` | `text` | 是 |  |  |  |
| `dataset_version` | `text` | 否 |  |  |  |
| `schema_versions` | `jsonb` | 否 |  | `'{}'::jsonb` | 该 run 内各产物 schema_version 的去重集合，如 {"sample":"sample-rich-v1"} |
| `paper_count` | `integer` | 否 |  | `0` |  |
| `is_current` | `boolean` | 否 |  | `true` | 当前权威版本。多 run 并存时历史仍可查，API 默认只读 is_current=true |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

### `ops.schema_migration` — 14 行

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `filename` | `text` | 否 | ✔ |  |  |
| `checksum` | `text` | 否 |  |  |  |
| `applied_at` | `timestamp with time zone` | 否 |  | `now()` |  |
| `duration_ms` | `integer` | 是 |  |  |  |

## 资产湖 lake

### `lake.object` — 6,667 行

> 内容寻址对象表：object_id = sha256(bytes)。写入后永不修改，只增不删

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `object_id` | `text` | 否 | ✔ |  |  |
| `bytes` | `bigint` | 否 |  |  |  |
| `media_type` | `text` | 否 |  |  |  |
| `kind` | `text` | 否 |  |  |  |
| `uri` | `text` | 否 |  |  | 存储后端 URI；本地开发为 05_lake/objects/sha256/xx/yy/<hash>.<ext>，生产可平移到 S3/MinIO |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

### `lake.object_ref` — 6,695 行

> 逻辑路径 → 物理对象。同一字节被多篇引用时自动去重（image 复用很常见）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `object_id` | `text` | 否 |  |  |  |
| `paper_id` | `text` | 否 | ✔ |  |  |
| `rel_path` | `text` | 否 | ✔ |  |  |
| `role` | `text` | 否 |  |  |  |

### `lake.paper_manifest` — 68 行

> 单篇的湖内清单（≈ preprocess/manifest.json 的超集），用于按篇校验与增量重建

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 是 |  |  |  |
| `object_count` | `integer` | 否 |  |  |  |
| `total_bytes` | `bigint` | 否 |  |  |  |
| `manifest` | `jsonb` | 否 |  |  |  |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

## 事实层 core

### `core.alloy` — 250 行

> 论文内合金：名义成分的结构化来源，建库时把 wt%/at% 提升为 core.alloy_element

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `alloy_id` | `text` | 否 | ✔ |  |  |
| `name` | `text` | 是 |  |  |  |
| `base_element` | `text` | 是 |  |  |  |
| `elements` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `formula` | `text` | 是 |  |  |  |
| `formula_alpha` | `text` | 是 |  |  |  |
| `chemsys` | `text` | 是 |  |  |  |
| `n_elements` | `integer` | 是 |  |  |  |
| `aliases` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `description` | `text` | 是 |  |  |  |
| `notes` | `text` | 是 |  |  |  |
| `family_key` | `text` | 是 |  |  |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `is_stub` | `boolean` | 否 |  | `false` | true 表示 discover 未声明该合金、但被 sample 引用，为保持外键完整性补建的空壳 |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.alloy_element` — 986 行

> 成分长表（元素维度）：支持"含 Al ≥ 8 wt% 的所有钢"这类仿 MP 的元素过滤与 chemsys 聚合

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `alloy_id` | `text` | 否 | ✔ |  |  |
| `element` | `text` | 否 | ✔ |  |  |
| `weight_pct` | `numeric(9,4)` | 是 |  |  |  |
| `atomic_pct` | `numeric(9,4)` | 是 |  |  |  |
| `raw_wt` | `text` | 是 |  |  |  |
| `is_balance` | `boolean` | 否 |  | `false` |  |

### `core.characterization` — 2,183 行

> 表征手段（SEM/EBSD/XRD/拉伸…），支撑"哪些样品做过 EBSD"式过滤

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `idx` | `integer` | 否 | ✔ |  |  |
| `char_id` | `text` | 是 |  |  |  |
| `technique` | `text` | 是 |  |  |  |
| `technique_key` | `text` | 是 |  |  |  |
| `instrument` | `text` | 是 |  |  |  |
| `conditions` | `text` | 是 |  |  |  |
| `purpose` | `text` | 是 |  |  |  |
| `key_findings` | `text` | 是 |  |  |  |
| `payload` | `jsonb` | 是 |  |  |  |

### `core.equation` — 396 行

> 公式：latex + 符号表。后期可对 latex 归一化后做全库去重（同一条公式跨论文复用很常见）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `equation_id` | `text` | 否 | ✔ |  |  |
| `block_id` | `text` | 是 |  |  |  |
| `equation_number` | `text` | 是 |  |  |  |
| `is_image` | `boolean` | 否 |  | `false` |  |
| `latex` | `text` | 是 |  |  |  |
| `latex_hint` | `text` | 是 |  |  |  |
| `purpose` | `text` | 是 |  |  |  |
| `applicability` | `text` | 是 |  |  |  |
| `symbols` | `jsonb` | 否 |  | `'[]'::jsonb` |  |
| `n_symbols` | `integer` | 否 |  | `0` |  |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.evidence_block` — 10,316 行

> MinerU/预处理切分出的证据块，b0001…bNNNN。全库唯一的溯源起点：core.sample_trace.block_ids / core.figure_observation.block_ids 都必须能在这里命中

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `block_id` | `text` | 否 | ✔ |  |  |
| `ordinal` | `integer` | 否 |  |  |  |
| `kind` | `text` | 否 |  |  |  |
| `page_idx` | `integer` | 是 |  |  |  |
| `section` | `text` | 是 |  |  |  |
| `text` | `text` | 否 |  |  |  |
| `char_len` | `integer` | 否 |  |  |  |
| `in_reading_view` | `boolean` | 否 |  | `true` |  |
| `content_sha256` | `text` | 否 |  |  |  |
| `tsv` | `tsvector` | 是 |  | `to_tsvector('english'::regconfig, COALESCE(text, ''::text))` |  |

### `core.figure` — 1,041 行

> 图片与表格：figure_id 来自 preprocess/image_groups.json，block_ids 已做过合成 id → 真实 block 的对齐

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `figure_id` | `text` | 否 | ✔ |  |  |
| `kind` | `text` | 否 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `family` | `text` | 是 |  |  |  |
| `image_type` | `text` | 是 |  |  |  |
| `description` | `text` | 是 |  |  |  |
| `confidence` | `numeric(3,2)` | 是 |  |  |  |
| `n_subfigures` | `integer` | 否 |  | `0` |  |
| `n_observations` | `integer` | 否 |  | `0` |  |
| `n_measured` | `integer` | 否 |  | `0` |  |
| `measured_quantities` | `jsonb` | 是 |  |  |  |
| `sample_hints` | `jsonb` | 是 |  |  |  |
| `image_paths` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `page_idx` | `integer` | 是 |  |  |  |
| `ordinal` | `integer` | 是 |  |  |  |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.figure_observation` — 12,405 行

> 单图观察项。evidence_raw 保留产物原样，block_ids 是对齐结果，对齐过程见 ops.block_id_resolution

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `figure_id` | `text` | 否 | ✔ |  |  |
| `idx` | `integer` | 否 | ✔ |  |  |
| `observation` | `text` | 否 |  |  |  |
| `source` | `text` | 是 |  |  |  |
| `confidence` | `numeric(3,2)` | 是 |  |  |  |
| `evidence_raw` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `block_status` | `text` | 否 |  | `'unresolved'::text` |  |

### `core.figure_panel` — 3,406 行

> 组图的子图（panel）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `figure_id` | `text` | 否 | ✔ |  |  |
| `idx` | `integer` | 否 | ✔ |  |  |
| `panel` | `text` | 是 |  |  |  |
| `description` | `text` | 是 |  |  |  |

### `core.paper` — 68 行

> 论文级实体：一行一篇，是全部下游实体的根

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `doi` | `text` | 是 |  |  |  |
| `title` | `text` | 否 |  |  |  |
| `abstract` | `text` | 是 |  |  |  |
| `journal` | `text` | 是 |  |  |  |
| `year` | `integer` | 是 |  |  |  |
| `research_type` | `text` | 是 |  |  |  |
| `domain` | `text` | 是 |  | `'materials'::text` |  |
| `keywords` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `authors` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `paper_scope` | `text` | 是 |  |  |  |
| `page_count` | `integer` | 是 |  |  |  |
| `block_count` | `integer` | 是 |  |  |  |
| `figure_count` | `integer` | 是 |  |  |  |
| `section_headings` | `jsonb` | 是 |  |  |  |
| `run_id` | `text` | 是 |  |  |  |
| `source_dir` | `text` | 是 |  |  |  |
| `qa_flags` | `text[]` | 否 |  | `'{}'::text[]` | 质量门禁命中的 warn 级标记（error 级会阻断入库），见 ops.qa_issue |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

### `core.performance` — 294 行

> 对比性能（benchmark 对照），常用于"相对提升 X%"这类表述

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `perf_id` | `text` | 否 | ✔ |  |  |
| `benchmark_sample` | `text` | 是 |  |  |  |
| `benchmark_alloy` | `text` | 是 |  |  |  |
| `comparison_metric` | `text` | 是 |  |  |  |
| `improvement` | `text` | 是 |  |  |  |
| `service_conditions` | `text` | 是 |  |  |  |
| `lifetime` | `text` | 是 |  |  |  |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.phase` — 1,493 行

> 组织中的相：相名 + 体积分数 + 晶粒尺寸，是"相"维度的可过滤列（对应下阶段计划第 2 条）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `microstructure_id` | `text` | 否 | ✔ |  |  |
| `idx` | `integer` | 否 | ✔ |  |  |
| `phase_name` | `text` | 否 |  |  |  |
| `phase_key` | `text` | 是 |  |  |  |
| `crystal_structure` | `text` | 是 |  |  |  |
| `volume_fraction_raw` | `text` | 是 |  |  |  |
| `volume_fraction_pct` | `numeric(7,4)` | 是 |  |  |  |
| `morphology` | `text` | 是 |  |  |  |
| `grain_size_raw` | `text` | 是 |  |  |  |
| `grain_size_um` | `numeric` | 是 |  |  |  |
| `texture` | `text` | 是 |  |  |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `payload` | `jsonb` | 是 |  |  |  |

### `core.process` — 382 行

> 论文内工艺路线（状态态）：discover.processes 的投影；工艺步骤链见 core.processing_step

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `process_id` | `text` | 否 | ✔ |  |  |
| `name` | `text` | 是 |  |  |  |
| `state_label` | `text` | 是 |  |  |  |
| `aliases` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `description` | `text` | 是 |  |  |  |
| `notes` | `text` | 是 |  |  |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `is_stub` | `boolean` | 否 |  | `false` |  |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.process_edge` — 195 行

> 工艺谱系树/DAG 的边（discover.processes[].parent_process_ids），可递归查询前驱工序

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `child_process_id` | `text` | 否 | ✔ |  |  |
| `parent_process_id` | `text` | 否 | ✔ |  |  |

### `core.processing_step` — 2,610 行

> 工艺链的逐步展开（熔炼→锻造→均匀化→…→退火），是"可结构化过滤"的工艺维度

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `seq` | `integer` | 否 | ✔ |  |  |
| `step_id` | `text` | 是 |  |  |  |
| `step_type` | `text` | 是 |  |  |  |
| `method` | `text` | 是 |  |  |  |
| `temperature_raw` | `text` | 是 |  |  |  |
| `temperature_k` | `numeric` | 是 |  |  |  |
| `duration_raw` | `text` | 是 |  |  |  |
| `duration_s` | `numeric` | 是 |  |  |  |
| `atmosphere` | `text` | 是 |  |  |  |
| `cooling_medium` | `text` | 是 |  |  |  |
| `heating_rate` | `text` | 是 |  |  |  |
| `reduction_ratio` | `text` | 是 |  |  |  |
| `notes` | `text` | 是 |  |  |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |

### `core.property_value` — 1,508 行

> 性能量长表：一个标量一行。value_kind 区分数值/区间/开区间/定性，value_canonical 已做单位换算（应力→MPa、尺寸→μm、温度→K、分数→%），可跨论文直接比较

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 否 | ✔ |  |  |
| `path` | `text` | 否 | ✔ |  | 与 core.sample_trace.path 同一命名空间，二者可 JOIN 做"值-证据"联查 |
| `section` | `text` | 否 |  |  |  |
| `group_path` | `text` | 是 |  |  |  |
| `metric` | `text` | 否 |  |  |  |
| `idx` | `integer` | 否 |  | `0` |  |
| `value_raw` | `text` | 是 |  |  |  |
| `value_kind` | `text` | 否 |  |  |  |
| `value_num` | `numeric` | 是 |  |  |  |
| `value_low` | `numeric` | 是 |  |  |  |
| `value_high` | `numeric` | 是 |  |  |  |
| `value_unit` | `text` | 是 |  |  |  |
| `unit_canonical` | `text` | 是 |  |  |  |
| `value_canonical` | `numeric` | 是 |  |  |  |
| `value_low_canonical` | `numeric` | 是 |  |  |  |
| `value_high_canonical` | `numeric` | 是 |  |  |  |
| `qualifier` | `text` | 是 |  |  |  |
| `uncertainty_raw` | `text` | 是 |  |  |  |
| `direction` | `text` | 是 |  |  |  |
| `block_status` | `text` | 是 |  |  |  |
| `conditions` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |

### `core.sample` — 638 行

> 样品 = 合金 × 工艺（sample_id = alloy_id + "__" + process_id），是性能/组织/证据的挂载点

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `alloy_id` | `text` | 否 |  |  |  |
| `process_id` | `text` | 否 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `aliases` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `payload` | `jsonb` | 否 |  |  |  |

### `core.sample_data` — 638 行

> 科学事实层（保真 JSONB）。多 run 并存时靠 is_latest 一键取当前版；历史版永不覆盖

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 否 | ✔ |  |  |
| `payload` | `jsonb` | 否 |  |  |  |
| `payload_bytes` | `integer` | 是 |  |  |  |
| `sha256` | `text` | 否 |  |  |  |
| `is_latest` | `boolean` | 否 |  | `true` |  |
| `loaded_at` | `timestamp with time zone` | 否 |  | `now()` |  |

### `core.sample_trace` — 68,944 行

> 证据溯源层：每个标量叶子一条。与 sample_data 通过 (paper_id, sample_id, path) 关联，path 即 JSON Pointer，可直接在 payload 上定位到原始值（校验见 tests/test_integrity.py）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 否 | ✔ |  |  |
| `path` | `text` | 否 | ✔ |  |  |
| `reason` | `text` | 是 |  |  |  |
| `block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `status` | `text` | 否 |  |  |  |
| `depth` | `integer` | 是 |  |  |  |

### `core.sample_wiki` — 638 行

> 全中文词条：语义检索/RAG 的核心语料；"可查询维度"不放这里，放 property_value

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `run_id` | `text` | 否 | ✔ |  |  |
| `summary` | `text` | 是 |  |  |  |
| `mechanisms` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `n_mechanisms` | `integer` | 是 |  |  |  |
| `conclusions` | `text` | 是 |  |  |  |
| `payload` | `jsonb` | 否 |  |  |  |
| `content` | `text` | 是 |  |  |  |
| `content_seg` | `text` | 是 |  |  |  |

### `core.unmapped_finding` — 2,956 行

> 无法归入既有 schema 的发现：既是知识残渣，也是 schema 迭代的输入信号

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 否 | ✔ |  |  |
| `sample_id` | `text` | 否 | ✔ |  |  |
| `idx` | `integer` | 否 | ✔ |  |  |
| `text` | `text` | 否 |  |  |  |
| `source_block_ids` | `text[]` | 否 |  | `'{}'::text[]` |  |

## 规范化层 canon

### `canon.alloy_family` — 23 行

> 合金族/钢种分类（可多层）。core.alloy.family_key 由规则引擎赋值，NULL 表示未分类，可人工回填

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `family_key` | `text` | 否 | ✔ |  |  |
| `name` | `text` | 否 |  |  |  |
| `name_zh` | `text` | 是 |  |  |  |
| `description` | `text` | 是 |  |  |  |
| `rule` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `parent_key` | `text` | 是 |  |  |  |

### `canon.characterization_technique` — 21 行

> 表征手段受控词表，用于"哪些样品做过 EBSD"这类过滤

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `technique_key` | `text` | 否 | ✔ |  |  |
| `name` | `text` | 否 |  |  |  |
| `abbreviation` | `text` | 是 |  |  |  |
| `category` | `text` | 是 |  |  |  |
| `aliases` | `text[]` | 否 |  | `'{}'::text[]` |  |

### `canon.element` — 83 行

> 元素周期表子集，用于成分解析、chemsys 计算与元素维度过滤

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `symbol` | `text` | 否 | ✔ |  |  |
| `name_en` | `text` | 否 |  |  |  |
| `name_zh` | `text` | 是 |  |  |  |
| `atomic_number` | `integer` | 否 |  |  |  |
| `atomic_mass` | `numeric(9,4)` | 否 |  |  |  |
| `category` | `text` | 是 |  |  |  |
| `is_steel_relevant` | `boolean` | 否 |  | `false` |  |

### `canon.phase` — 41 行

> 相/组织的受控词表；core.phase.phase_key 由名称+别名+形貌规则匹配得到

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `phase_key` | `text` | 否 | ✔ |  |  |
| `name` | `text` | 否 |  |  |  |
| `name_zh` | `text` | 是 |  |  |  |
| `formula` | `text` | 是 |  |  |  |
| `crystal_structure` | `text` | 是 |  |  |  |
| `family` | `text` | 是 |  |  |  |
| `aliases` | `text[]` | 否 |  | `'{}'::text[]` |  |
| `notes` | `text` | 是 |  |  |  |

## 校订层 curate

### `curate.active_change`

> 当前生效的校订，供 UI 与报表使用

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `change_id` | `bigint` | 是 |  |  |  |
| `op` | `text` | 是 |  |  |  |
| `target_table` | `text` | 是 |  |  |  |
| `target_key` | `jsonb` | 是 |  |  |  |
| `field` | `text` | 是 |  |  |  |
| `old_value` | `jsonb` | 是 |  |  |  |
| `new_value` | `jsonb` | 是 |  |  |  |
| `status` | `text` | 是 |  |  |  |
| `error` | `text` | 是 |  |  |  |
| `note` | `text` | 是 |  |  |  |
| `author` | `text` | 是 |  |  |  |
| `source` | `text` | 是 |  |  |  |
| `created_at` | `timestamp with time zone` | 是 |  |  |  |
| `applied_at` | `timestamp with time zone` | 是 |  |  |  |
| `paper_id` | `text` | 是 |  |  |  |

### `curate.change` — 0 行

> 人工校订流水：每一次增删改一行。ingest 结束后由 curate.apply 重新应用，因此不会被重跑覆盖

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `change_id` | `bigint` | 否 | ✔ | `nextval('curate.change_change_id_seq'::regclass)` |  |
| `op` | `text` | 否 |  |  |  |
| `target_table` | `text` | 否 |  |  |  |
| `target_key` | `jsonb` | 否 |  |  |  |
| `field` | `text` | 是 |  |  |  |
| `old_value` | `jsonb` | 是 |  |  |  |
| `new_value` | `jsonb` | 是 |  |  |  |
| `status` | `text` | 否 |  | `'applied'::text` |  |
| `error` | `text` | 是 |  |  |  |
| `note` | `text` | 是 |  |  |  |
| `author` | `text` | 否 |  | `'anonymous'::text` |  |
| `source` | `text` | 否 |  | `'api'::text` |  |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |
| `applied_at` | `timestamp with time zone` | 是 |  |  |  |

### `curate.paper_change_count`

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `n` | `bigint` | 是 |  |  |  |
| `n_active` | `bigint` | 是 |  |  |  |
| `last_change` | `timestamp with time zone` | 是 |  |  |  |

## 检索层 search

### `search.document` — 5,099 行

> 统一检索文档：一张表覆盖论文摘要/wiki/图/表/公式/未归类发现，支持全文+模糊+向量三路召回

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `doc_id` | `text` | 否 | ✔ |  |  |
| `doc_type` | `text` | 否 |  |  |  |
| `paper_id` | `text` | 否 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `ref_id` | `text` | 是 |  |  |  |
| `title` | `text` | 是 |  |  |  |
| `body` | `text` | 否 |  |  |  |
| `content_seg` | `text` | 否 |  |  | 预分词文本。中文由 ETL 侧 jieba 切分后写入；迁移到 zhparser 后可退化为原文 |
| `lang` | `text` | 是 |  |  |  |
| `tsv` | `tsvector` | 是 |  | `to_tsvector('simple'::regconfig, COALESCE(content_seg, ''::text))` |  |
| `embed` | `vector(384)` | 是 |  |  |  |
| `embed_model` | `text` | 是 |  |  |  |
| `meta` | `jsonb` | 否 |  | `'{}'::jsonb` |  |
| `created_at` | `timestamp with time zone` | 否 |  | `now()` |  |

## 消费层 api（视图/函数）

### `api.alloy_composition`

> 有效成分（wt%）：余量元素与基体元素按 100−Σ其余 推断，is_inferred 标记推断值；reported 保留原始上报值（可能为 NULL）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `alloy_id` | `text` | 是 |  |  |  |
| `element` | `text` | 是 |  |  |  |
| `weight_pct` | `numeric` | 是 |  |  |  |
| `reported` | `numeric` | 是 |  |  |  |
| `is_inferred` | `boolean` | 是 |  |  |  |
| `raw_wt` | `text` | 是 |  |  |  |
| `is_balance` | `boolean` | 是 |  |  |  |

### `api.equation`

> 公式视图：附带所在段落原文，便于人工核验

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `equation_id` | `text` | 是 |  |  |  |
| `block_id` | `text` | 是 |  |  |  |
| `equation_number` | `text` | 是 |  |  |  |
| `latex` | `text` | 是 |  |  |  |
| `purpose` | `text` | 是 |  |  |  |
| `applicability` | `text` | 是 |  |  |  |
| `symbols` | `jsonb` | 是 |  |  |  |
| `n_symbols` | `integer` | 是 |  |  |  |
| `source_text` | `text` | 是 |  |  |  |

### `api.figure`

> 图表视图：描述 + 题注原文（已按对齐后的真实 block 拼回）

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `figure_id` | `text` | 是 |  |  |  |
| `kind` | `text` | 是 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `image_type` | `text` | 是 |  |  |  |
| `description` | `text` | 是 |  |  |  |
| `confidence` | `numeric(3,2)` | 是 |  |  |  |
| `n_subfigures` | `integer` | 是 |  |  |  |
| `n_observations` | `integer` | 是 |  |  |  |
| `n_measured` | `integer` | 是 |  |  |  |
| `image_paths` | `text[]` | 是 |  |  |  |
| `block_ids` | `text[]` | 是 |  |  |  |
| `page_idx` | `integer` | 是 |  |  |  |
| `ordinal` | `integer` | 是 |  |  |  |
| `caption_text` | `text` | 是 |  |  |  |
| `n_observations_traced` | `bigint` | 是 |  |  |  |

### `api.paper`

> 论文列表/详情：带各实体计数，避免 N+1 查询

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `doi` | `text` | 是 |  |  |  |
| `title` | `text` | 是 |  |  |  |
| `journal` | `text` | 是 |  |  |  |
| `year` | `integer` | 是 |  |  |  |
| `research_type` | `text` | 是 |  |  |  |
| `authors` | `text[]` | 是 |  |  |  |
| `keywords` | `text[]` | 是 |  |  |  |
| `paper_scope` | `text` | 是 |  |  |  |
| `page_count` | `integer` | 是 |  |  |  |
| `block_count` | `integer` | 是 |  |  |  |
| `figure_count` | `integer` | 是 |  |  |  |
| `section_headings` | `jsonb` | 是 |  |  |  |
| `run_id` | `text` | 是 |  |  |  |
| `qa_flags` | `text[]` | 是 |  |  |  |
| `n_samples` | `bigint` | 是 |  |  |  |
| `n_alloys` | `bigint` | 是 |  |  |  |
| `n_figures` | `bigint` | 是 |  |  |  |
| `n_equations` | `bigint` | 是 |  |  |  |

### `api.process_chain`

> 工艺链折叠视图，用于列表展示与"含退火/含淬火"式过滤

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `chain_text` | `text` | 是 |  |  |  |
| `step_types` | `text[]` | 是 |  |  |  |
| `max_temperature_k` | `numeric` | 是 |  |  |  |
| `total_duration_s` | `numeric` | 是 |  |  |  |
| `n_steps` | `bigint` | 是 |  |  |  |

### `api.property`

> 性能量（含原文、数值、单位归一、溯源状态），供过滤与导出

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `formula` | `text` | 是 |  |  |  |
| `chemsys` | `text` | 是 |  |  |  |
| `family_key` | `text` | 是 |  |  |  |
| `section` | `text` | 是 |  |  |  |
| `group_path` | `text` | 是 |  |  |  |
| `metric` | `text` | 是 |  |  |  |
| `path` | `text` | 是 |  |  |  |
| `value_raw` | `text` | 是 |  |  |  |
| `value_kind` | `text` | 是 |  |  |  |
| `value_num` | `numeric` | 是 |  |  |  |
| `value_low` | `numeric` | 是 |  |  |  |
| `value_high` | `numeric` | 是 |  |  |  |
| `value_unit` | `text` | 是 |  |  |  |
| `unit_canonical` | `text` | 是 |  |  |  |
| `value_canonical` | `numeric` | 是 |  |  |  |
| `value_low_canonical` | `numeric` | 是 |  |  |  |
| `value_high_canonical` | `numeric` | 是 |  |  |  |
| `qualifier` | `text` | 是 |  |  |  |
| `uncertainty_raw` | `text` | 是 |  |  |  |
| `direction` | `text` | 是 |  |  |  |
| `block_status` | `text` | 是 |  |  |  |
| `conditions` | `jsonb` | 是 |  |  |  |
| `source_block_ids` | `text[]` | 是 |  |  |  |

### `api.sample`

> 样品主视图：合金成分、体系、合金族、工艺、论文元数据一次取齐

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `alloy_id` | `text` | 是 |  |  |  |
| `process_id` | `text` | 是 |  |  |  |
| `alloy_name` | `text` | 是 |  |  |  |
| `formula` | `text` | 是 |  |  |  |
| `formula_alpha` | `text` | 是 |  |  |  |
| `chemsys` | `text` | 是 |  |  |  |
| `elements` | `text[]` | 是 |  |  |  |
| `n_elements` | `integer` | 是 |  |  |  |
| `family_key` | `text` | 是 |  |  |  |
| `family_name_zh` | `text` | 是 |  |  |  |
| `process_name` | `text` | 是 |  |  |  |
| `state_label` | `text` | 是 |  |  |  |
| `paper_title` | `text` | 是 |  |  |  |
| `doi` | `text` | 是 |  |  |  |
| `year` | `integer` | 是 |  |  |  |
| `journal` | `text` | 是 |  |  |  |
| `run_id` | `text` | 是 |  |  |  |
| `n_properties` | `bigint` | 是 |  |  |  |
| `n_phases` | `bigint` | 是 |  |  |  |
| `n_steps` | `bigint` | 是 |  |  |  |

### `api.sample_summary`

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `alloy_id` | `text` | 是 |  |  |  |
| `label` | `text` | 是 |  |  |  |
| `formula` | `text` | 是 |  |  |  |
| `chemsys` | `text` | 是 |  |  |  |
| `family_key` | `text` | 是 |  |  |  |
| `elements` | `text[]` | 是 |  |  |  |
| `year` | `integer` | 是 |  |  |  |
| `paper_title` | `text` | 是 |  |  |  |
| `yield_strength_mpa` | `numeric` | 是 |  |  |  |
| `tensile_strength_mpa` | `numeric` | 是 |  |  |  |
| `elongation_pct` | `numeric` | 是 |  |  |  |
| `reduction_of_area_pct` | `numeric` | 是 |  |  |  |
| `hardness` | `numeric` | 是 |  |  |  |
| `hardness_scale` | `text` | 是 |  |  |  |
| `density_g_cm3` | `numeric` | 是 |  |  |  |
| `youngs_modulus_gpa` | `numeric` | 是 |  |  |  |
| `ferrite_pct` | `numeric` | 是 |  |  |  |
| `austenite_pct` | `numeric` | 是 |  |  |  |
| `grain_size_um` | `numeric` | 是 |  |  |  |
| `n_numeric_properties` | `bigint` | 是 |  |  |  |

### `api.stats`

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `papers` | `bigint` | 是 |  |  |  |
| `alloys` | `bigint` | 是 |  |  |  |
| `samples` | `bigint` | 是 |  |  |  |
| `properties` | `bigint` | 是 |  |  |  |
| `numeric_properties` | `bigint` | 是 |  |  |  |
| `phases` | `bigint` | 是 |  |  |  |
| `processing_steps` | `bigint` | 是 |  |  |  |
| `figures` | `bigint` | 是 |  |  |  |
| `equations` | `bigint` | 是 |  |  |  |
| `evidence_blocks` | `bigint` | 是 |  |  |  |
| `search_documents` | `bigint` | 是 |  |  |  |
| `embedded_documents` | `bigint` | 是 |  |  |  |
| `lake_objects` | `bigint` | 是 |  |  |  |
| `lake_bytes` | `numeric` | 是 |  |  |  |

### `api.trace`

> 溯源明细：每条事实值的证据块与原文，可直接喂给 RAG 做"带引用回答"

| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |
|---|---|:---:|:---:|---|---|
| `paper_id` | `text` | 是 |  |  |  |
| `sample_id` | `text` | 是 |  |  |  |
| `path` | `text` | 是 |  |  |  |
| `status` | `text` | 是 |  |  |  |
| `block_ids` | `text[]` | 是 |  |  |  |
| `reason` | `text` | 是 |  |  |  |
| `evidence_text` | `text` | 是 |  |  |  |
