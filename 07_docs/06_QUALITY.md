# 数据质量与门禁

> 完整数字见 `04_reports/qa_report.md`（自动生成）。本文说明**规则设计**与**已知缺陷**。
> 门禁的硬性检查同时以 pytest 形式固化：`06_db/tests/` 共 95 项全部通过
> （`test_integrity.py` 16 / `test_api.py` 12 / `test_web.py` 16 / `test_curate.py` 14 /
> `test_composition.py` 16 / `test_units.py` 19 / `test_evidence.py` 2）。

---

## 1. 三级质量模型

| 级别 | 含义 | 处置 |
|---|---|---|
| `error` | 破坏可信性：溯源断链、路径失效、外键悬空 | **阻断该篇发布**，必须修 ETL 或数据 |
| `warn` | 数据脏但可修：合成 id、章节名泄漏、缺题注 | 入库但打 `qa_flags`，进工单 |
| `info` | 覆盖率信号：空分区、不可解析值、未分类合金 | 只做统计，驱动 schema 迭代 |

规则目录在 `ops.qa_rule`，问题实例在 `ops.qa_issue`（可按 `rule_code`、`paper_id` 聚合）。

## 2. 当前结果

| 规则 | 级别 | 数量 | 说明 |
|---|---|---:|---|
| `BLOCK_ID_UNRESOLVED` | warn | 15 | 上游把 `figure_XXX` 写进了 `block_id`，且该图组无题注块，无法还原 |
| `FIGURE_EVIDENCE_EMPTY` | warn | 821 | 非视觉观察项缺 `evidence` 字段（`source=caption/citation` 却没有引用） |
| `WIKI_SECTION_LEAK` | warn | 8 | LLM 把下一个键名（`conclusions`）写进了 `mechanisms` 数组，ETL 已剔除 |
| `TRACE_PATH_MISSING` | error | 0 | 68,944 条 JSON Pointer 全部能在 payload 上命中 |
| `BLOCK_ID_DANGLING` | error | 0 | 全部 `block_ids` 均指向真实证据块（trace 里的 `figure_00X` 已按图组还原） |
| `DUPLICATE_TITLE` | warn | 0 | 标题两两相似度均 ≤ 0.92 |

`error` 级为 0，说明 68 篇**全部达到可发布标准**。

## 3. block_id 对齐结果

原始 evidence id 有 200+ 种形态（`b_caption_002`、`b_citing_2`、`caption_figure_003`、
`fig7_caption`、`Fig. 4` …），真实证据块只有 `bNNNN` 一种。

| 方法 | 数量 | 含义 |
|---|---:|---|
| `figure_group` | 11,796 | 按"角色 + 图表序号"回查 `image_groups`，或用所在图组上下文兜底（含 trace 里误写的 `figure_00X`） |
| `direct` | 989 | 原文即是真实 block id（含 `b013 → b0013` 补零） |
| `unresolved` | 8 | 无法还原，保留原样、标记弱溯源（不臆造）；可解析率 99.94% |

对齐后 12,405 条图观察项：4,016 `ok`、1 `partial`、7,637 `visual_only`、751 `unresolved`。
`visual_only` 是纯视觉描述（本就没有文字证据），不计入缺陷。

## 4. 已知缺陷（需要上游提取环节改进）

1. **27% 的样品没有结构化性能**（174/638）。抽查确认部分论文的 `properties` 数组本身为空，
   而正文/图表里其实有性能数据 —— 这是提取阶段的漏抽，不是建库的问题。
   建议在提取 Agent 增加"性能必填"检查。
2. **硬度口径混杂**：329 条硬度中，一部分以 HV/HRC 报告、一部分以 MPa 报告。
   已用 `unit_canonical` 区分（HV/HRC/HB/MPa），查询时必须带标尺条件。
3. **图和正文的对齐依赖 `image_groups`**：没有题注块的图组（751 条观察项）无法溯源，
   只能依靠视觉描述本身。
4. **`hardness` 的极端值**（最高 16,500 MPa）来自"以 MPa 报告的硬度"，
   物理上成立但容易被误当作强度，已在视图中拆成 `hardness` + `hardness_scale` 两列。
5. **成分完整性不齐**（做成分检索时暴露）：250 个合金里，149 个写 `Fe Bal.` / `balance`，
   4 个给了 Fe 的具体数字，32 个有 Fe 行但值为空或 `x (variable)`，65 个完全没列 Fe。
   已用 `api.alloy_composition` 按余量补全：243 个 Fe 基合金中 239 条为推断值（`is_inferred`），
   但**推断值不能当原始数据引用**——引用时应说明"由余量推算"。

## 5. 复现方式

```bash
cd database/06_db
.venv/bin/python -m steeldig_db qa        # 跑规则，写 ops.qa_issue
.venv/bin/python -m steeldig_db report    # 生成 04_reports/qa_report.md
.venv/bin/python -m pytest tests -q       # 95 项硬性断言
```

任何一项 `error` 级规则或 pytest 失败，都视为**不可发布**。
