# 总体架构

> 本文把《数据库建立》里的架构图落成可运行的实现，并记录每一个偏离原稿的决定及其理由。
> 同目录有：`01_SCHEMA.md`（ER 图，自动生成）、`02_DATA_DICTIONARY.md`（数据字典，自动生成）、
> `03_RUNBOOK.md`（运维手册）、`04_QUERY_COOKBOOK.md`（查询手册）、
> `05_MATERIALS_PROJECT.md`（与 Materials Project 的对照）、`06_QUALITY.md`（质量报告）。
> 同目录另有 [`00_ARCHITECTURE_PLAIN.md`](00_ARCHITECTURE_PLAIN.md)（白话版）：同一套架构，
> 写给没有数据库背景的读者，用类比解释每个决定与代价。本文与其结论一致，只是用工程语言表述。

---

## 1. 四层结构

```
┌──────────────────────────────────────────────────────────────────────┐
│ [消费层]  浏览界面 / REST API / RAG Agent / 分析看板 / 训练数据导出    │
│          06_db/api/steeldig_api  ·  UI 与 /api 同源部署                │
│          schema: api.*（只读视图与函数）                               │
├──────────────────────────────────────────────────────────────────────┤
│ [检索层]  精确/面聚合: PG 列 + GIN     语义: pgvector HNSW(384d)      │
│          全文: tsvector(simple+jieba)  模糊: pg_trgm  成分: 区间+距离  │
│          search.document · search.hybrid() · api.alloy_composition    │
├──────────────────────────────────────────────────────────────────────┤
│ [事实源]  PostgreSQL 16                                               │
│          实体表(列) + JSONB(保真) + trace                              │
│          core.*  ops.*  canon.*                                       │
├──────────────────────────────────────────────────────────────────────┤
│ [资产湖]  内容寻址对象存储（本地 FS，可平移 MinIO/S3/OSS）             │
│          lake.object / lake.object_ref —— 原始 JSON + 图片，不可变    │
└──────────────────────────────────────────────────────────────────────┘
         ▲ 只读、可重建                      ▲ 内容寻址写入，永不修改
```

**关键思想**（与文档一致）：文件是"湖"（immutable，可重建一切），数据库是"仓"
（为查询组织，可随时从湖重建）。湖里的每个 JSON/图片按 `sha256` 落盘，
DB 只存"结构化的可查询投影 + 保真 JSONB"。因此任何列级 bug 都能从湖重放修复，
不需要回头重新跑提取。

### 1.1 与原稿四层逐层对照

| 层 | 原稿（2026.10） | 当前实现 | 差异 |
|---|---|---|---|
| 消费层 | 查询 API / RAG Agent / 分析看板 / 下游训练数据导出 | 网页 10 页 + REST 22 个接口 + `search.document` 语料 + 看板 3 张 | **训练数据导出未做** |
| 检索层 | 精确/面聚合：PG 列 + GIN；语义：pgvector(HNSW)；全文：tsvector（可升级 OpenSearch） | B-tree + GIN + pg_trgm + pgvector HNSW(384d)；中文走 jieba 分词 | OpenSearch 未上（规模未到） |
| 事实源 | PostgreSQL —— 实体表(列) + JSONB(保真) + trace | 36 表 + 12 视图 / 7 schema；`payload` 存原文；trace 68,944 条 | 无 |
| 资产湖 | 对象存储(MinIO/S3/OSS) —— 原始 JSON + 图片 | 本地 FS + sha256 内容寻址：6,667 对象 / 148 MB；写路径已按 S3 key 布局 | 后端仍为本地磁盘 |

四层均已落地。未做的两项性质不同：训练数据导出是**排期**问题，OpenSearch 是**规模**问题——
后者到量再换，不影响其他三层。

### 1.2 设计逻辑：一个数据库要回答的五个问题

存储、增、删、改、查，是数据库的基本盘；企业级文献库再加一条**可审计**。
这些能力落到五组设施：

| # | 能力 | 架构落点 | 证据 |
|---|---|---|---|
| 1 | 存得住 | 湖（只增、内容寻址）+ 事实源（可重建）+ `run` 版本 | 6,667 对象 / 148 MB；30 s 重灌；4 个 run |
| 2 | 查得到 | 列（只提升过滤维度）+ 单位归一 + 三种索引 | 1,508 条性能，1,304 条可数值查询 |
| 3 | 改得动 | `curate.change` 叠加层，ingest 后自动重放 | 直接 `UPDATE` 会被下一次 ingest 覆盖（实测） |
| 4 | 说得清 | `sample_trace` + 审计字段 + `is_latest` | 68,944 条指针 100% 命中；1,133 条（75%）挂到段落，其余标记 `insufficient` |
| 5 | 用得上 | 10 个页面 + 22 个接口 + 检索语料 | 界面 / REST / 导出 |

"说得清"不是对"抽取会出错"的补救，而是文献数据的举证要求：每条记录都要能回答
"谁、在哪篇、哪句说的；后来谁改过"。抽取的三类已知错法（漏、串、补）因此被当作
**风险清单**，对应测试、质量门禁、弱溯源标记三道防线，而不是架构的前提。

四层结构是这五条能力的落点：1 落在湖与事实源，2 落在检索层，3、4 横跨事实源与校订层，
5 是消费层。若压成"一个 MongoDB"或"直接让模型读 PDF"，丢掉的不是组件，
而是溯源、版本、修订与重放这四项能力。

> 面向非技术读者的展开（含反例与代价）见 [`00_ARCHITECTURE_PLAIN.md`](00_ARCHITECTURE_PLAIN.md) 第 4 节。

---

## 2. 四条设计原则的落地

| 原则 | 落地方式 | 证据 |
|---|---|---|
| **1. 只提升身份/外键/过滤维度为列** | 实体表只暴露 `*_id`、外键、以及会被 `WHERE` 用的维度（强度、温度、相分数、年份、元素、合金族）；完整产物一律进 `payload jsonb`。 | `core.sample_data.payload` 保存 `*.data.json` 原文；`core.property_value` 才是数值投影 |
| **2. data / trace 分离** | `core.sample_data`（科学事实）与 `core.sample_trace`（证据溯源）两张表，靠 `(paper_id, sample_id, path)` 关联，`path` 是 JSON Pointer。 | `tests/test_integrity.py::test_trace_paths_resolve` 逐条验证 path 能在 payload 上命中 |
| **3. 多 run / 多模型内建版本** | 每条事实带 `run_id`；`core.sample_data` 主键含 `run_id`，并有 `is_latest` 部分唯一索引；`ops.run` 记录 extractor/model/batch/dataset_version。 | 68 篇分属 4 个 run：`run_0915_pro`(13) `run_0917_pro`(4) `run_0919_pro`(4) `run_1009_flash`(47) |
| **4. 两级身份** | paper 内实体一律复合键 `(paper_id, entity_id)`；跨论文的"同一合金/同一相"不强行合并，只提供 `canon.*` 受控词表 + `core.alloy.family_key` / `core.phase.phase_key` 两个可空挂载点。 | `canon.alloy_family` 有 20 条层级规则；`core.alloy.family_key` 由规则引擎赋值，NULL 表示未分类 |

---

## 3. 与原稿的四处主动增强

原稿是"资产梳理 + 依赖选型"，落地时补了四件事，否则它只是一个 JSON 转存库：

### 3.1 数值归一化层（`core.property_value`）

原文的字段值是自由字符串：`"427–513 MPa"`、`"~350-450"`、`"up to 950 MPa"`、
`"3.5 μm"`、`"1050 °C"`、`"not less than 40%"`。若原样入库，只能 `LIKE`。

`etl/steeldig_db/quantity.py` 把它们解析成
`(value_kind, value_low, value_high, unit_canonical, value_canonical)`：

| 原文 | kind | 归一化结果 |
|---|---|---|
| `685` + unit `MPa` | numeric | 685 MPa |
| `427–513 MPa` | range | [427, 513] MPa，中点 470 |
| `~350-450` | range | [350, 450] MPa |
| `up to 950 MPa` | open_high | ≤ 950 MPa |
| `not less than 40%` | open_low | ≥ 40 % |
| `1 GPa` | numeric | 1000 MPa |
| `1050 °C` | numeric | 1323.15 K |
| `2 h` | numeric | 7200 s |
| `increases with Al content in the range 2–11 wt.%` | **qualitative** | 保留原文，不臆造数值 |

规范单位：应力→MPa、尺寸→μm、温度→K、分数→%、时间→s、密度→g/cm³。
这一步把"能看"的库变成"能查"的库：`WHERE yield_strength_mpa BETWEEN 600 AND 900`
现在是真查询，不是字符串匹配。

当前 1,508 条属性量中 1,304 条已数值化（86%）；其余 204 条中，172 条为定性描述
（"increases with…"），32 条为单位缺失或非常规、无法安全换算，均保留原文并显式标记，而不是丢弃。
硬度额外保留 `unit_canonical` 作为标尺（HV/HRC/HB/MPa），因为三种标尺之间是非线性的、不可互换。

### 3.2 block_id 对齐（`ops.block_id_resolution`）

原稿 2.5 已指出：`figure/*.json` 的 `observation.evidence[].id` 用了合成 id
（`b_caption_002`、`b_citing_2`、`caption_figure_003`…），而 `evidence_blocks.json`
里的真实 id 只有 `bNNNN`。实测 12,405 条观察项，原始 id 形态超过 200 种。

`etl/steeldig_db/blockresolve.py` 做三级还原，全部留痕：

| 方法 | 说明 | 本次结果 |
|---|---|---|
| `direct` | 本身就是 `bNNNN`（含 `b013 → b0013` 补零） | 989 |
| `figure_group` | 由"角色 + 图表序号"回查 `image_groups` 的 caption/citation 列表；无序号时用所在图组上下文兜底；trace 里误写的 `figure_00X` 也走这条 | 11,796 |
| `unresolved` | 无法还原，值保留、标记弱溯源 | 8（合计 12,793 条证据 id，可解析率 99.94%） |

对齐后 12,405 条观察项中 4,016 条 `ok`、1 条 `partial`、7,637 条 `visual_only`
（纯视觉描述本就没有文字证据，不算缺陷）、751 条 `unresolved`（所在图组没有题注块）。

### 3.3 中英文检索（jieba + tsvector + pg_trgm + pgvector）

PostgreSQL 原生没有中文分词。本方案在 **ETL 侧**用 jieba 把中文切成空格分隔的
`content_seg` 写入 `search.document`，DB 侧用 `simple` 配置建 GIN 索引。
查询时 API 用同一套 jieba 切分，保证索引与查询的 token 一致。

三路召回用 RRF（k=60）融合，无需归一化不同信号的分数量纲：

| 信号 | 实现 | 适用 |
|---|---|---|
| 全文 | `ts_rank_cd` + GIN | 精确术语（"κ-碳化物"、"TWIP"） |
| 模糊 | `similarity` + `word_similarity` + pg_trgm | 拼写差异、长中文查询 |
| 语义 | pgvector HNSW（`paraphrase-multilingual-MiniLM-L12-v2`, 384d） | 概念检索（"为什么加铝能降密度"） |

升级路径：若引入 zhparser/pg_bigm，可把 `content_seg` 退化为原文；
若检索量级到千万级，`search.document` 可整体外迁 OpenSearch，DB 仍是事实源。

---

### 3.4 成分检索（周期表 → 区间 → 距离）

研究者的真实入口是"给我一个 Fe-28Mn-10Al-0.8C 附近的钢"，而不是关键词。

但原始成分数据有两个坑：`Fe` 常写成 `Bal.`（`weight_pct` 为 NULL），
另有 65 个合金根本没列 Fe、32 个列了但值为空。250 个合金里只有 4 个给了 Fe 的具体数字，
149 个写 `Bal.` / `balance`。直接按"Fe 有数值"查，只剩 4 个可用。

`api.alloy_composition` 因此做了一次**有标记的补全**：

```
余量元素 / 基体元素 → 100 − Σ其余元素，is_inferred = true
```

`/composition` 页面把周期表做成筛选器：点元素、设 wt% 上下限；
`/api/composition/search` 先返回**完全匹配**，没有匹配时按
"到区间的最短距离（wt% 点）"排序返回最接近的，并给出「Al 低 7.4」这种差异说明。
未指定的元素只作为排序的次要因素，不影响"是否精确"。

> 推断值一律带 `*` 展示，原始值仍在 `core.alloy_element.weight_pct` 里。

## 4. 数据流

```
02_extraction/<paper_id>/           01_raw/mineru_source/<paper_id>/
   preprocess/*.json  ──┐              images/*.jpg
   output/discover/     │                 │
   output/sample/       │                 │
   output/sample_trace/ ├── PaperIngest ──┤
   output/wiki/         │   (etl)         │
   output/figure/       │                 │
   output/equation/     │                 ▼
   timing.json ─────────┘            05_lake/objects/sha256/xx/yy/<hash>.*
                                          │  (lake.object / object_ref)
                                          ▼
                            PostgreSQL  core.*  canon.*  search.*
                                          │
                                          ▼
                                   api.*  →  REST API
```

一篇论文的 ETL 是**单事务**的：先 `DELETE FROM core.paper`（级联清子表），
再按外键顺序 `COPY` 写入。因此重跑任意篇都是幂等的，不需要手工清库。

失败隔离：单篇异常 → `ROLLBACK` + `ops.ingest_log.status='failed'`，其余篇继续。

### 4.1 产物 → 表

"48 张表"不是先设计再找数据，而是从手中 5 类产物倒推出来的：

| 产物（`02_extraction/<paper>/`） | 入库落点 | 规模 |
|---|---|---|
| `preprocess/evidence_blocks.json` | `core.evidence_block` | 10,316 |
| `output/discover/*.json` | `core.paper` + `payload` | 68 |
| `output/sample/*.json` | `core.sample` / `alloy` / `phase` / `property_value` / `processing_step` | 638 / 250 / 1,493 / 1,508 / 2,610 |
| `output/sample_trace/*.json` | `core.sample_trace` | 68,944 |
| `output/figure/*.json` | `core.figure` / `core.figure_observation` | 1,041 / 12,405 |
| `preprocess/image_groups.json` | 题注与引用，用于 `block_id` 对齐 | 12,793 条解析记录 |
| `preprocess/multimodal_evidence_index.json` | **不建表**（与 `image_groups` 90% 重复），仅 `lake.object_ref` 留档 | — |
| `timing.json` | `ops.ingest_run`（耗时 / token / 模型） | 68 |

操作规则沿用原稿：入库只读 `output/`（被覆盖的当前态），不读 `_monitor/`（只增的历史态）；
`sample` 的 rich 版只用于对照，入库的是 data 版。


---

## 5. 规模与成本

| 项 | 数值 |
|---|---|
| 论文 | 68 |
| 合金 / 样品 | 250 / 638 |
| 证据块 | 10,316（377 万字符） |
| 性能量 | 1,508（其中 1,304 可数值化：numeric 1,243 / range 81 / open 12） |
| 相记录 | 1,493 |
| 工艺步骤 | 2,610 |
| 图 / 表 | 1,041（含 121 个表） |
| 图观察项 | 12,405 |
| 公式 | 396 |
| 未归类发现 | 2,956 |
| 溯源记录 | 68,944 |
| 检索文档 | 5,099（全部已向量化） |
| 湖对象 | 6,667 个 / 148 MB（去重后） |
| 全量入库耗时 | 约 30 s（单机） |
| DB 体积 | 332 MB（含 HNSW 索引与全文 GIN） |
| 迁移 / 表 / 视图 | 14 个迁移 · 36 表 + 12 视图（7 schema） |

按此推算到 1 万篇：湖约 20 GB（图片占大头，PDF 不入湖）、DB 约 40 GB、
入库约 75 分钟（可并行到 8 进程压到 12 分钟）。

---

## 6. 关键决策记录（ADR）

**ADR-1 为什么 PDF 不入湖？**
PDF 共 703 MB，占 `01_raw` 的 73%。它是"输入"而非"派生资产"，
且 MinerU 的 `content_list.json` + `full.md` 已足够重建证据链。
湖只存 JSON 与图片（148 MB），需要时从 `01_raw` 按 DOI 取回。
开关：`lake.py` 预留 `--include-pdf`。

**ADR-2 为什么 `_monitor/` 不入库？**
原稿已判定：`output/` 是被覆盖的当前态，`_monitor/` 是只增的历史态。
它是审计材料（1.1 GB），不是权威事实。入库只从 `output/` 读。

**ADR-3 为什么 `image_groups.json` 与 `multimodal_evidence_index.json` 取其一？**
两者 90% 重叠。ETL 以 `image_groups` 为准（题注/引用块是原稿两个文件的交集），
`multimodal_evidence_index` 只通过 `lake.object_ref` 留档，不单独建模。

**ADR-4 为什么 `canon.phase` 不做自动合并？**
68 篇里"ferrite"有 30+ 种写法（α、delta ferrite、bcc ferrite…）。
强行自动归一会污染；正确做法是保留原文 `phase_name` + 可空 `phase_key`，
把消解留给后续人工/规则迭代。`canon.phase` 已内置 40 条常见相与别名。

**ADR-5 为什么用复合主键而不是全局自增 id？**
`(paper_id, sample_id)` 本身就是业务主键，且天然支持分片与按篇重放。
引入代理键只会多一次 join。

**ADR-6 为什么 `run_id` 放在事实表而不是只在 `paper` 上？**
同一篇论文未来会有 pro/flash/qwen 多次提取结果并存对比。
`core.sample_data` 主键 `(paper_id, sample_id, run_id)` + `is_latest` 部分唯一索引，
让"取当前版"只需 `WHERE is_latest`，"看历史"只需去掉该条件。

**ADR-7 为什么是 PostgreSQL，而不是 MySQL / MongoDB / Neo4j / Elasticsearch？**
选型标准不是"哪项最强"，而是"最少拼装"——每多一个组件，就多一套备份、权限与故障面。
这批数据同时需要四种能力：区间过滤（强度、成分）、JSON 保真（原文）、中文全文、语义检索。
PostgreSQL 一个库全有；MySQL 缺 JSONB 的 GIN 与 pgvector，窗口函数也弱；
MongoDB 的行内聚合与区间比较慢；Neo4j 只需要 68,944 条三列溯源，不值得单开；
Elasticsearch 的数值过滤要与 PG 二次 join，一致性只能靠补偿。
代价是单机、无分布式、HNSW 吃内存——到千万级文档时把检索层外迁即可，事实层不动。


---

## 7. 扩展路线

1. **多 run 对比**：把 `out_*/flash`、`qwen` 也灌入，新增 run_id 即可；
   `api.sample_summary` 加 `run_id` 过滤做模型间一致性分析。
2. **canonical 消解**：`canon.alloy_family` 已是数据驱动规则表，
   新增钢种只需 INSERT；跨论文"同一合金"可用成分向量聚类后回填 `canon` 层。
3. **公式去重**：`core.equation.latex` 归一化（去空格/统一宏）后做全库指纹。
4. **对象存储**：`lake.py` 的写路径已按 S3 key 布局设计，
   替换 `_put()` 为 boto3 `put_object` 即可，DB 侧零改动。
5. **权限**：当前 `api` schema 只读；生产建议为 API 建只读角色，
   ETL 用独立写角色，并对 `ops` 做审计日志。
