# 本地试用指南

> 照着从上往下敲即可。每一步都给了「预期结果」，对不上就跳到最后一节排障。
> 全部命令在 macOS + Docker Desktop 上验证过。

---

## 0. 先确认服务在跑

```bash
cd /Users/mac/Desktop/SteelDig/database

# 容器
docker compose -f 06_db/docker-compose.yml ps

# API
curl -s http://127.0.0.1:8011/api/health
```

预期：

```
NAME          IMAGE                    STATUS
steeldig-db   pgvector/pgvector:pg16   Up (healthy)

{"status":"ok","db":true,"ts":"..."}
```

如果这里是 `Connection refused`，看第 8 节。

---

## 1. 浏览器（最直观，先看这个）

| 打开 | 看什么 |
|---|---|
| <http://127.0.0.1:8011/> | 总览：KPI、强度-塑性散点、合金族构成 |
| <http://127.0.0.1:8011/browse?ys_min=800> | 样品库：筛出屈服强度 ≥ 800 的 66 个样品 |
| <http://127.0.0.1:8011/papers/10.1002_srin.202100643> | 一篇文献：2 个合金、2 个样品、15 张图表 |
| <http://127.0.0.1:8011/search?q=κ-碳化物> | 检索（中文可以用） |
| <http://127.0.0.1:8011/quality> | 质量门禁：0 error / 844 warn |
| <http://127.0.0.1:8011/docs> | API 文档，可以直接点 “Try it out” |

**建议先点这一条**：样品详情页（从 `/browse` 随便点一个样品名）——
看右侧每个性能值后面的 `◈ N 条证据`，那是指向原文段落的链接。

---

## 2. 用 HTTP 查（适合写脚本）

```bash
# 规模
curl -s http://127.0.0.1:8011/api/stats | jq '{papers,samples,numeric_properties}'

# 取 3 个高强度样品
curl -s "http://127.0.0.1:8011/api/samples?min_ys=800&limit=3" \
  | jq -r '.items[] | "\(.sample_id)\t\(.yield_strength_mpa) MPa\t\(.family_key)"'

# 中文语义检索（注意 --data-urlencode，否则中文会被截断）
curl -s --get http://127.0.0.1:8011/api/search \
  --data-urlencode "q=为什么加铝能降低钢的密度" \
  --data "k=3" | jq '{n, items: [.items[] | {doc_type, doc_id}]}'

# 一个样品的完整档案（成分/工艺/相/性能/叙述/溯源）
curl -s "http://127.0.0.1:8011/api/samples/10.1002_srin.202100643/sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac" \
  | jq '{material_id, composition, properties: [.properties[] | {metric, value, unit}]}'
```

预期：第一条返回 `{"papers":68,"samples":638,"numeric_properties":1304}`。

> 没有 `jq` 就把 `| jq ...` 换成 `| python3 -m json.tool`。

---

## 3. 用 SQL 查（进 psql）

```bash
docker exec -it steeldig-db psql -U steeldig -d steeldig
```

进去之后，`\x auto` 会让宽结果竖排显示，然后逐条试：

```sql
-- ① 有哪些表
\dt core.*

-- ② 一条最简单的查询
select count(*) from core.paper;

-- ③ 强度排行（前 10）
select sample_id, formula, yield_strength_mpa ys, elongation_pct el
from api.sample_summary
where yield_strength_mpa is not null
order by yield_strength_mpa desc nulls last
limit 10;

-- ④ 按合金族看平均性能
select family_key, count(*) n,
       round(avg(yield_strength_mpa)::numeric,0) avg_ys,
       round(avg(elongation_pct)::numeric,1) avg_el
from api.sample_summary
where family_key is not null
group by 1 having count(*) >= 5 order by 2 desc;

-- ⑤ 成分筛选：含 Al ≥ 8 wt% 的合金
select a.formula, a.chemsys, e.weight_pct
from core.alloy a join core.alloy_element e
  on e.paper_id=a.paper_id and e.alloy_id=a.alloy_id
where e.element='Al' and e.weight_pct >= 8
order by e.weight_pct desc limit 10;

-- ⑥ 相筛选：铁素体体积分数 > 5%
select sample_id, phase_name, max(volume_fraction_pct) vf
from core.phase
where volume_fraction_pct > 5 and phase_name ilike '%ferrite%'
group by 1,2 order by 3 desc limit 10;

-- ⑦ 工艺筛选：退火温度 ≥ 900 °C（1173.15 K）
select sample_id, seq, step_type, method, temperature_raw
from core.processing_step
where temperature_k >= 1173.15
order by sample_id, seq limit 10;

-- ⑧ 强塑积排行（UTS × EL）
select sample_id, round((tensile_strength_mpa*elongation_pct/100)::numeric,0) uts_x_el
from api.sample_summary
where tensile_strength_mpa is not null and elongation_pct is not null
order by uts_x_el desc nulls last limit 5;

-- ⑨ 溯源：一个数值出自哪段原文
select v.metric, v.value_raw, v.source_block_ids,
       left(b.text, 120) as 原文
from core.property_value v
left join core.evidence_block b
  on b.paper_id = v.paper_id and b.block_id = v.source_block_ids[1]
where v.paper_id = '10.1002_srin.202100643'
  and v.metric = 'yield_strength';

-- ⑩ 质量：按规则看问题
select rule_code, severity, count(*) from ops.qa_issue group by 1,2 order by 3 desc;

-- ⑪ 退出
\q
```

---

## 3.5 成分检索（元素周期表）

浏览器打开 <http://127.0.0.1:8011/composition>，点周期表里的元素设上下限。

命令行等价：

```bash
# 有完全匹配：Al 8–11 wt%，Mn 25–30 wt%
curl -s --get http://127.0.0.1:8011/api/composition/search \
  --data "el=Al:8-11" --data "el=Mn:25-30" \
  | jq '{exact: .exact.count, nearest: .nearest.count, fallback}'

# 没有完全匹配：会返回最接近的，并标注差多少
curl -s --get http://127.0.0.1:8011/api/composition/search \
  --data "el=Al:20-25" \
  | jq '{fallback, top3: [.nearest.items[:3][] | {formula, distance, deltas}]}'

# 只要求含有某元素，不限含量
curl -s --get http://127.0.0.1:8011/api/composition/search \
  --data "el=Cr" --data "el=Ni" | jq '.exact.count'
```

预期：第一条 `exact=41`；第二条 `fallback=true`，最近的铝合金约 12.6 wt%（差 7.4）。

## 4. 用命令行工具

```bash
cd /Users/mac/Desktop/SteelDig/database/06_db

.venv/bin/python -m steeldig_db stats     # 全库行数概览
.venv/bin/python -m steeldig_db verify    # 重算 6,667 个湖对象的 sha256 + 检查断链
.venv/bin/python -m steeldig_db curate list   # 人工校订流水
```

预期 `verify` 输出：

```
对象 6,667 个，147.7 MB，损坏 0
无引用的孤儿对象：0
溯源断链行：0
```

---

## 5. 试一次“写”（改一条数值，看重跑会不会丢）

这一节是理解这个库**最关键的 30 秒**。

### 5.1 先记下原值

```bash
docker exec steeldig-db psql -U steeldig -d steeldig -c "
select value_canonical from core.property_value
where paper_id='10.1002_srin.202100643'
  and sample_id like '%0.0025n%' and metric='yield_strength';"
```

预期 `685`。

### 5.2 直接用 SQL 改（会丢）

```bash
docker exec steeldig-db psql -U steeldig -d steeldig -c "
update core.property_value set value_canonical=700
where paper_id='10.1002_srin.202100643'
  and sample_id like '%0.0025n%' and metric='yield_strength';"

cd /Users/mac/Desktop/SteelDig/database/06_db
.venv/bin/python -m steeldig_db ingest --papers 10.1002_srin.202100643
```

再查一次 → **又变回 685**。因为这库的事实层是从资产湖重放出来的。

### 5.3 走校订层改（不会丢）

```bash
# 改
curl -s -X POST http://127.0.0.1:8011/api/curate/changes \
  -H 'Content-Type: application/json' -d '{
  "op":"update","target_table":"core.property_value",
  "target_key":{"paper_id":"10.1002_srin.202100643",
                "sample_id":"sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac",
                "run_id":"run_0915_pro",
                "path":"$.properties[0].mechanical.tensile_properties.yield_strength[0]"},
  "field":"value_canonical","new_value":690,
  "note":"原文 Table 2","author":"test"}' | jq

# 再重跑一次入库
.venv/bin/python -m steeldig_db ingest --papers 10.1002_srin.202100643

# 再查 —— 这次是 690，重跑冲不掉
docker exec steeldig-db psql -U steeldig -d steeldig -c "
select value_canonical from core.property_value
where paper_id='10.1002_srin.202100643'
  and sample_id like '%0.0025n%' and metric='yield_strength';"
```

### 5.4 清理（把 690 撤销，恢复原状）

```bash
# 上一步返回的 change_id，比如 40
curl -s -X POST http://127.0.0.1:8011/api/curate/changes/40/revert | jq
.venv/bin/python -m steeldig_db ingest --papers 10.1002_srin.202100643
```

再查应回到 `685`，`curate list` 里那条变成 `reverted`。

---

## 6. 验证索引真的在用（技术验证）

```bash
docker exec steeldig-db psql -U steeldig -d steeldig -c "
explain (analyze, costs off)
select doc_id from search.document
where tsv @@ websearch_to_tsquery('simple','carbide precipitation')
limit 3;"
```

预期看到 `Bitmap Index Scan on document_tsv_idx` —— 说明全文索引生效，不是全表扫。

---

## 7. 一次跑完的冒烟检查

```bash
cd /Users/mac/Desktop/SteelDig/database/06_db
.venv/bin/python -m pytest tests -q
```

预期 `75 passed`（约 40 秒）。

---

## 8. 服务没起来怎么办

```bash
# 1) 数据库容器
docker compose -f 06_db/docker-compose.yml up -d db
docker compose -f 06_db/docker-compose.yml ps          # 等 STATUS 变 healthy

# 2) API / 界面（前台运行，Ctrl-C 停）
cd 06_db && .venv/bin/uvicorn steeldig_api.main:app --host 127.0.0.1 --port 8011

# 3) 端口被占
lsof -i :8011          # 看谁占了
lsof -i :5435

# 4) 数据库连不上
docker exec steeldig-db psql -U steeldig -d steeldig -c "select 1;"
```

常见原因：

| 现象 | 原因 | 处理 |
|---|---|---|
| `Connection refused` :8011 | API 没起 | 跑上面第 2 步 |
| `Connection refused` :5435 | 容器没起 / Docker 没开 | 先启动 Docker Desktop |
| 界面 500 | 代码改了没重启 | 重启 uvicorn |
| 中文搜不到 | 查询没 URL 编码 | curl 用 `--data-urlencode` |

---

## 一句话总结

- **想看** → 浏览器 <http://127.0.0.1:8011/>
- **想查** → psql 或 `/api/*`
- **想改** → 界面「人工校订」或 `/api/curate/changes`（不要直接 UPDATE）
- **想加论文** → 文件放进 `02_extraction/<id>/`，`ingest --papers <id>`
