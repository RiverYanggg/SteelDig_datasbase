# 与 Materials Project 的对照

> Materials Project（MP）是材料数据库的事实标准：以 **material_id** 为中心，
> 把结构、弹性、电子、热力学等性质挂在其下，用 **chemsys / formula / elements**
> 做分面，并提供 summary 文档与 REST API。
>
> 本文说明本库借鉴了什么、哪些不适用、以及为什么。

---

## 1. 对齐关系

| Materials Project | SteelDig 知识库 | 说明 |
|---|---|---|
| `material_id`（mp-149） | `paper_id:sample_id` | 本库的"材料"是**实验样品**，不是晶体结构。同一成分不同工艺 = 不同样品，必须分开 |
| `formula` / `chemsys` / `elements` | `core.alloy.formula` / `chemsys` / `elements` | 完全对齐，且做了 wt% 系数的化学式（`FeMn28Al10C0.8`） |
| 周期表选元素 + 区间筛选 | `/composition` 页面 + `api.alloy_composition` | 最接近 MP 的交互：点元素设上下限，无匹配时给最近邻 |
| `structure`（晶体结构 CIF） | `core.phase` + `crystal_structure` | 文献里多数只给相名与形貌，不给完整晶格；不强行伪造 CIF |
| `elasticity` / `band_gap` / `formation_energy` | `core.property_value`（长表） | MP 是计算值、字段固定；本库是文献值、字段自由 → 必须用长表 + 单位归一 |
| `task_id` / `origins`（计算来源） | `run_id` + `lake.object_ref` | 本库要溯源到**原文段落**（evidence block），比 MP 的 provenance 更强 |
| summary document（`/materials/{id}`） | `api.material_document()` | 同构：一次返回成分/性质/来源，可直接进下游 |
| `materials/{id}/tasks` | `core.sample_trace`（68,944 条） | 每条事实值 → 证据块 |
| MPContribs（外部贡献） | `canon.*` 受控词表 + `ops.qa_issue` | 本库把"人工校正"建模为词表与 QA 工单 |
| `mp-api` Python 客户端 | `steeldig_api` REST + SQL 视图 | |

## 2. 关键差异

### 2.1 实验样品 ≠ 晶体结构

MP 的 `material_id` 指向一个**晶体结构**，同一成分的不同相是不同的 mp-id。
文献里的"样品"是 **成分 × 工艺** 的产物，组织可能是多相混合。
因此本库的主键是 `(paper_id, sample_id)`，`sample_id = alloy_id + "__" + process_id`，
相信息放在 `core.phase`（一对多）。

这带来一个 MP 没有的维度：**工艺**。`core.processing_step`（2,610 行）与
`core.process_edge`（195 条 DAG 边）让"退火温度 → 相分数 → 强度"这类链条可查询。

### 2.2 数值不规整，所以需要归一化层

MP 的性质是计算输出，单位与量纲固定（eV/atom、GPa）。
文献值是 `"427–513 MPa"`、`"~350-450"`、`"up to 950 MPa"`。
本库用 `core.property_value` 的
`value_kind / value_low / value_high / unit_canonical / value_canonical`
表达"区间、开区间、定性"，而不是把噪声硬塞进一个 `float` 列。

### 2.3 溯源粒度到段落

MP 的 provenance 是"哪个计算任务、哪个数据库条目"。
本库的 provenance 是"哪一段原文"：`core.evidence_block`（10,316 块）+
`core.sample_trace`（68,944 条 JSON Pointer 级溯源）+
`ops.block_id_resolution`（12,793 条 id 对齐审计）。

这让库不仅能回答"是什么"，还能回答"哪句话说的"，可直接支撑
带引用的 RAG 与人工复核。

### 2.4 七维总表

PPT 第 19 页把上述差异连同版本、校订、存储、检索、schema 演进一起压成一张表：

| 维度 | 主流材料库 | 本项目 | 为什么必须不同 |
|---|---|---|---|
| 主键与身份 | 全局材料 id，按结构去重 | `(paper_id, sample_id)`：合金 × 工艺 | 同一成分、不同工艺是两个样品 |
| 溯源粒度 | 指向计算任务或 DOI，记录级 | JSON Pointer → block_id → 段落与图 | 抽取会错，必须能回到原句 |
| 版本 | 按发布整体刷新，无单条历史 | `run_id` + `is_latest`，4 个 run 并存 | 换模型、重跑不能丢历史 |
| 数值 | eV / Å 等计算单位，天生统一 | `value_kind` + 规范单位 + 保留原文 | 作者会写「~350-450」和「1 GPa」 |
| 修正 | 以重算为准，不设校订层 | `curate.change` 叠加层，入库后重放 | 人工修正必须活过重跑 |
| 存储布局 | 一个库 + 一个文件服务 | 内容寻址湖 + 关系仓 + 库内检索 | 要能从原始字节重放事实 |
| 检索 | 化学式、元素、结构相似度 | 中文全文 + 模糊 + 语义 + 成分区间 | 用户用中文问「为什么加铝降密度」 |
| schema 演进 | 固定 schema，重算即可 | 14 个迁移 + 从湖重放 | 上游字段命名会漂移 |

一句话：**他们在记录"结果"，我们在记录"声明 + 声明的出处 + 出处的修订史"。**

## 3. 可复用的 MP 使用姿势

```sql
-- MP 风格：按元素体系找材料
SELECT * FROM api.sample_summary WHERE chemsys = 'Al-C-Fe-Mn';

-- MP 风格：按成分范围筛选
SELECT DISTINCT a.paper_id, a.alloy_id, a.formula
FROM core.alloy a
JOIN core.alloy_element e ON e.paper_id = a.paper_id AND e.alloy_id = a.alloy_id
WHERE e.element = 'Al' AND e.weight_pct BETWEEN 8 AND 11;

-- MP 风格：summary 文档
SELECT api.material_document(paper_id, sample_id) FROM core.sample LIMIT 1;
```

## 4. 不打算照搬的部分

| MP 特性 | 本库取舍 | 理由 |
|---|---|---|
| 全量晶体结构（CIF） | 不做 | 文献不提供，生成即造假 |
| 计算性质（DFT） | 不做 | 与实验文献库正交，可作为外部关联表接入 |
| 全局 material_id 命名空间 | 改用 `paper_id:sample_id` + 后期 canonical 消解 | 68 篇内强行合并同一合金会引入错误；留待规模上来后做 |
