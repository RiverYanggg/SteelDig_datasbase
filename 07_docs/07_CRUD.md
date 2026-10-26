# 增删改查（CRUD）

> 结论先说：**查**是完备的；**增 / 改 / 删**都能做，但不走"直接改表"，
> 而是走 `curate.change` 这一层。原因是事实层可被重跑重建——直接改会被覆盖。
> 这不是能力缺失，是写模型的选择；下面给出原因、用法和边界。

---

## 1. 为什么不能直接 UPDATE

`core.*` 是 ETL 从资产湖重放的产物。入库一篇论文 = `DELETE` 本篇全部行 + 按外键顺序重新 `COPY`。

实测：

```sql
-- 人工把 685 改成 999
UPDATE core.property_value SET value_canonical = 999 WHERE ... ;
-- 结果：999 ✓
```

```bash
python -m steeldig_db ingest --papers 10.1002_srin.202100643
# 结果：又变回 685 ✗
```

所以"直接改表"在这个架构里**不是持久操作**。正确做法是把人的修正记录成一条**增量**，
在每次入库结束后重放——这样既保留湖的权威性，又让人工校订持久化。

---

## 2. 三层写入模型

```
┌─────────────────────────────────────────────────────────────┐
│ 资产湖 05_lake（不可变）  ← 唯一权威来源，只增不改           │
│   哈希寻址，ETL 可完整重建 core                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ ingest（整篇重建，幂等）
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 事实层 core.*（可重建）  ← 不要直接写，会被下一次 ingest 覆盖│
└───────────────────────▲─────────────────────────────────────┘
                        │ apply（每次 ingest 后自动重放）
┌───────────────────────┴─────────────────────────────────────┐
│ 校订层 curate.change（人写，持久）                            │
│   记录 op / 目标行 / 字段 / 旧值 / 新值 / 作者 / 说明 / 状态  │
└─────────────────────────────────────────────────────────────┘
```

| 能力 | 路径 | 持久? | 审计? |
|---|---|---|---|
| **查** | SQL / REST `/api/*` / 浏览界面 | — | — |
| **改** | `curate.change` op=update | ✅ 重跑后重新应用 | ✅ 记录前后值 |
| **增** | 新增论文走 ETL；新增样品走 `op=create` | ✅ | ✅ |
| **删** | `op=delete`（物理删 core 行，重跑后再删一次） | ✅ | ✅ 可撤销 |
| ~~直接改表~~ | `UPDATE core.*` | ❌ 下次 ingest 被覆盖 | ❌ |

---

## 3. 用法

### 3.1 REST API

```bash
# 可写白名单（前端据此渲染表单）
curl http://127.0.0.1:8011/api/curate/schema

# 修正一条性能值
curl -X POST http://127.0.0.1:8011/api/curate/changes \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <key，若配置了 STEELDIG_WRITE_KEY>' \
  -d '{
    "op": "update",
    "target_table": "core.property_value",
    "target_key": {
      "paper_id": "10.1002_srin.202100643",
      "sample_id": "sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac",
      "run_id": "run_0915_pro",
      "path": "$.properties[0].mechanical.tensile_properties.yield_strength[0]"
    },
    "field": "value_canonical",
    "new_value": 690,
    "note": "原文 Table 2 为 690 MPa",
    "author": "zhang"
  }'

# 新增一个文献里漏抽的样品
curl -X POST .../api/curate/changes -d '{
    "op": "create",
    "target_table": "core.sample",
    "target_key": {"paper_id": "...", "sample_id": "sample_x__as-cast",
                   "alloy_id": "alloy_x", "process_id": "proc_as-cast"},
    "new_value": {"paper_id": "...", "sample_id": "sample_x__as-cast",
                  "alloy_id": "alloy_x", "process_id": "proc_as-cast",
                  "label": "人工补充", "aliases": []},
    "note": "图 3 中提到但未抽出"}'

# 删除一条脏数据
curl -X POST .../api/curate/changes -d '{
    "op": "delete", "target_table": "core.property_value",
    "target_key": {...}, "note": "重复抽取"}'

# 撤销
curl -X POST .../api/curate/changes/42/revert

# 审计
curl '.../api/curate/changes?paper_id=10.1002_srin.202100643'
```

### 3.2 界面

样品详情页底部有 **人工校订** 卡片：选一条性能 → 填新值 / 依据 / 校订人 → 提交；
下方列出该样品全部校订记录，可一键撤销。

### 3.3 命令行

```bash
python -m steeldig_db curate list           # 最近的校订流水
python -m steeldig_db curate apply          # 手动重放（ingest 已自动做）
python -m steeldig_db curate revert 42      # 撤销
```

---

## 4. 可写白名单

只有登记过的表/列能改，避免 API 退化成任意 SQL 执行器（`etl/steeldig_db/curate.py::REGISTRY`）。

| 表 | 主键 | 可改列 | 可新增 | 可删除 |
|---|---|---|---|---|
| `core.paper` | paper_id | title / doi / journal / year / abstract / keywords … | — | — |
| `core.alloy` | paper_id, alloy_id | name / family_key / formula / chemsys / aliases | ✅ | — |
| `core.sample` | paper_id, sample_id | label / aliases | ✅ | ✅ |
| `core.property_value` | …, run_id, path | value_canonical / value_raw / unit / block_status … | — | ✅ |
| `core.phase` | …, microstructure_id, idx | phase_name / phase_key / volume_fraction_pct / grain_size_um | — | — |
| `core.figure` | paper_id, figure_id | label / description / image_type | — | — |
| `core.figure_observation` | …, idx | observation / source | — | ✅ |
| `core.equation` | paper_id, equation_id | purpose / latex / applicability | — | — |
| `core.characterization` | …, idx | technique / technique_key / findings | — | — |
| `core.unmapped_finding` | …, idx | text | — | ✅ |

新增样品时，若 `alloy_id` / `process_id` 不存在，会自动补 `is_stub=true` 的占位行，保证外键完整。

---

## 5. 语义保证

| 保证 | 实现 |
|---|---|
| 重跑不丢人工修改 | `ingest` 末尾自动 `apply_changes()` |
| 单条校订失败不污染整批 | 每条用 `SAVEPOINT`，失败标记 `status='failed'` 并记录 error |
| 可追溯 | 记录 `old_value` / `new_value` / `author` / `note` / 时间 |
| 可撤销 | update 写回旧值；create 删除新行；delete 需重跑该篇（API 返回 `need_reingest`） |
| 幂等 | 重复应用同一条 update 结果一致；create 用 `ON CONFLICT DO NOTHING` |
| 类型安全 | 按 `information_schema` 的列类型适配 jsonb / 数组 / 标量 |

---

## 6. 已知边界

1. **并发**：没有乐观锁。两个人同时改同一行，后提交的覆盖先提交的（记录都在，可人工比对）。
   规模上来后建议加 `version` 列或 `updated_at` 校验。
2. **批量导入**：目前只能逐条 POST。若要从 Excel 批量导入，建议提供一个 CSV → `curate.change`
   的导入脚本（结构已具备，缺一个 loader）。
3. **审批流**：校订立即生效，无"待审"状态。`status` 字段已预留，可扩展为
   `pending / approved / rejected`。
4. **删除论文**：`core.paper` 不可删（级联会带走全部事实）。要下架一篇，应该在
   `ops.run` / 湖层面处理，而不是删事实行。
5. **不要手工 `DELETE FROM curate.change`**：删掉记录等于丢掉"该行应被删/应被改"的意图，
   已生效的删除会残留到下次 ingest。要撤销请用 `revert`。
