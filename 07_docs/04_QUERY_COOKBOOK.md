# 查询手册（Cookbook）

> 覆盖三类用法：**SQL 直查**（分析师）、**REST API**（应用）、**Python**（数据科学）。
> 所有示例都在本库 68 篇真实数据上验证过。
> 注意：PostgreSQL 里 `ORDER BY col DESC` 默认 **NULL 排最前**，
> 对可空列排序时请显式写 `DESC NULLS LAST`，否则空值会占满前几行。

---

## A. 数值查询（这才是建库的意义）

### A1. 屈服强度 700–900 MPa 的样品

```sql
SELECT paper_id, sample_id, formula, yield_strength_mpa, tensile_strength_mpa, elongation_pct
FROM api.sample_summary
WHERE yield_strength_mpa BETWEEN 700 AND 900
ORDER BY yield_strength_mpa DESC NULLS LAST;
```

### A2. 强度–塑性权衡：强塑积 > 30 GPa·%

```sql
SELECT sample_id, formula, yield_strength_mpa, elongation_pct,
       round((tensile_strength_mpa * elongation_pct / 100)::numeric, 1) AS uts_x_el_gpa_pct
FROM api.sample_summary
WHERE tensile_strength_mpa IS NOT NULL AND elongation_pct IS NOT NULL
  AND tensile_strength_mpa * elongation_pct / 100 > 30
ORDER BY 5 DESC NULLS LAST;
```

### A3. 成分筛选：含 Al ≥ 8 wt% 且含 Si

```sql
SELECT a.paper_id, a.alloy_id, a.formula, a.chemsys
FROM core.alloy a
WHERE a.alloy_id IN (SELECT alloy_id FROM core.alloy_element
                     WHERE element='Al' AND weight_pct >= 8)
  AND a.elements @> ARRAY['Si']
ORDER BY a.formula;
```

### A4. 元素体系分面（仿 Materials Project 的 chemsys）

```sql
SELECT chemsys, count(*) AS n_alloys, count(DISTINCT paper_id) AS n_papers
FROM core.alloy GROUP BY 1 ORDER BY 2 DESC;
```

### A5. 按合金族看性能分布

```sql
SELECT family_key, count(*) AS n,
       round(avg(yield_strength_mpa)::numeric,1) AS avg_ys,
       round(max(yield_strength_mpa)::numeric,1) AS max_ys,
       round(avg(elongation_pct)::numeric,1)   AS avg_el
FROM api.sample_summary
WHERE family_key IS NOT NULL
GROUP BY 1 HAVING count(*) >= 3 ORDER BY n DESC;
```

### A6. 区间值怎么用？

`value_kind='range'` 的值同时有 `value_low_canonical` / `value_high_canonical`。
要"区间与查询区间有交集"：

```sql
SELECT metric, value_raw, value_low_canonical, value_high_canonical
FROM core.property_value
WHERE metric = 'yield_strength' AND value_kind = 'range'
  AND value_low_canonical < 900 AND value_high_canonical > 700;
```

---

## B. 组织与工艺

### B1. 铁素体体积分数 > 5% 的样品

```sql
SELECT s.paper_id, s.sample_id, ph.phase_name, ph.volume_fraction_pct, ph.grain_size_um
FROM core.phase ph JOIN core.sample s USING (paper_id, sample_id)
WHERE ph.phase_name ILIKE '%ferrite%' AND ph.volume_fraction_pct > 5
ORDER BY 4 DESC;
```

### B2. 谁的工艺里含"退火 ≥ 900 °C"

```sql
SELECT DISTINCT s.sample_id, ps.seq, ps.step_type, ps.method, ps.temperature_raw
FROM core.processing_step ps JOIN core.sample s USING (paper_id, sample_id)
WHERE ps.temperature_k >= 1173.15
  AND (ps.method ILIKE '%anneal%' OR ps.step_type ILIKE '%heat%')
ORDER BY s.sample_id, ps.seq;
```

### B3. 工艺链全文

```sql
SELECT * FROM api.process_chain WHERE paper_id = '10.1002_srin.202100643';
```

### B4. 工艺谱系（前驱工序）

```sql
WITH RECURSIVE up AS (
    SELECT process_id, parent_process_id, 1 AS depth
    FROM core.process_edge WHERE paper_id = '10.1002_srin.202100643'
    UNION ALL
    SELECT u.process_id, e.parent_process_id, u.depth + 1
    FROM up u JOIN core.process_edge e
      ON e.paper_id = '10.1002_srin.202100643' AND e.child_process_id = u.parent_process_id
)
SELECT * FROM up ORDER BY depth;
```

---

## C. 证据与溯源（RAG 的地基）

### C1. 查一个性能值的原文

```sql
SELECT p.metric, p.value_raw, p.source_block_ids,
       (SELECT string_agg(b.text, E'\n') FROM core.evidence_block b
         WHERE b.paper_id = p.paper_id AND b.block_id = ANY (p.source_block_ids)) AS evidence
FROM core.property_value p
WHERE p.paper_id = '10.1002_srin.202100643'
  AND p.sample_id LIKE '%0.0025n%'
  AND p.metric IN ('yield_strength','ultimate_tensile_strength');
```

### C2. trace ↔ data 联查（原则 2 的直接用法）

```sql
SELECT t.path, t.status, d.payload #> string_to_array(replace(replace(t.path,'$.',''),'.','/'), '/') AS raw_value
FROM core.sample_trace t
JOIN core.sample_data d USING (paper_id, sample_id, run_id)
WHERE t.paper_id = '10.1002_srin.202100643'
  AND t.sample_id = 'sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac'
  AND t.status = 'ok' LIMIT 5;
```

> `#>` 只适用于纯对象路径；数组下标路径请用 `api.trace` 视图或 `core.property_value`。

### C3. 一个证据块被谁引用

```sql
SELECT * FROM api.trace WHERE paper_id='10.1002_srin.202100643' AND 'b0013' = ANY (block_ids);
```

### C4. block_id 对齐质量

```sql
SELECT method, count(*) FROM ops.block_id_resolution GROUP BY 1 ORDER BY 2 DESC;
SELECT block_status, count(*) FROM core.figure_observation GROUP BY 1;
```

---

## D. 全文 / 模糊 / 语义检索

### D1. SQL 直接调用（查询串需先分词）

```sql
-- 英文可直接用；中文建议走 API（API 会做 jieba 切分）
SELECT * FROM search.hybrid('low density steel austenite', 'low density steel austenite', NULL, 10, NULL);
```

### D2. 纯全文 / 纯模糊 / 纯语义

```sql
SELECT * FROM search.text_rank('kappa carbide', 10);
SELECT * FROM search.fuzzy_rank('铝含量对密度的影响', 10);
SELECT * FROM search.semantic_rank('[0.01,0.02,...]'::vector, 10);   -- 需要先有向量
```

### D3. API

```bash
curl 'http://127.0.0.1:8011/api/search?q=κ-碳化物%20析出%20强化&k=5'
curl 'http://127.0.0.1:8011/api/search?q=why%20aluminium%20lowers%20density&mode=vector&k=5'
```

### D4. 只看图表的检索

```bash
curl 'http://127.0.0.1:8011/api/search?q=EBSD%20grain%20boundary&types=figure,table&k=8'
```

---

## D3.5 成分检索（元素周期表 / 区间）

```bash
# 完全匹配
curl -s --get .../api/composition/search --data "el=Al:8-11" --data "el=Mn:25-30"

# 无匹配时自动给最接近的（带距离与差异说明）
curl -s --get .../api/composition/search --data "el=Al:20-25" | jq '.nearest.items[:3]'
```

SQL 等价（用补全过余量的 `api.alloy_composition`）：

```sql
select a.paper_id, a.alloy_id, a.formula
from core.alloy a
join api.alloy_composition c using (paper_id, alloy_id)
group by 1, 2, 3
having max(c.weight_pct) filter (where c.element = 'Al') between 8 and 11
   and max(c.weight_pct) filter (where c.element = 'Mn') between 25 and 30;
```

> `max(...) filter (...)` 在元素缺失时返回 NULL，`NULL between …` 不成立，
> 因此这条查询天然要求"必须含有该元素"。

## E. 导出与 RAG

### E1. 单样品完整文档（仿 MP summary doc）

```sql
SELECT jsonb_pretty(api.material_document('10.1002_srin.202100643',
       'sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac'));
```

```bash
curl 'http://127.0.0.1:8011/api/samples/10.1002_srin.202100643/sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac'
```

### E2. 训练语料导出（带证据的问答对素材）

```sql
SELECT doc_type, paper_id, title, body
FROM search.document
WHERE doc_type IN ('wiki','finding')
ORDER BY paper_id LIMIT 100;
```

### E3. 一次导出 100 个样品文档

```bash
curl 'http://127.0.0.1:8011/api/export/samples?limit=100' > samples.json
```

---

## F. Python 直连

```python
import psycopg, json, jieba

conn = psycopg.connect("postgresql://steeldig:steeldig_dev_pw@127.0.0.1:5435/steeldig")
seg = " ".join(t for t in jieba.cut("低密度钢 铝含量 密度降低") if t.strip())
rows = conn.execute(
    "SELECT doc_type, doc_id, score FROM search.hybrid(%s, %s, NULL, 10, NULL)",
    (seg, "低密度钢 铝含量 密度降低")).fetchall()
print(rows)
```

---

## G. 性能与索引验证

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM api.sample_summary WHERE yield_strength_mpa > 800;   -- Seq Scan（638 行无所谓）

EXPLAIN (ANALYZE)
SELECT * FROM search.document
WHERE tsv @@ websearch_to_tsquery('simple', 'carbide precipitation');  -- 走 GIN

EXPLAIN (ANALYZE)
SELECT * FROM search.document ORDER BY embed <=> (SELECT embed FROM search.document LIMIT 1) LIMIT 5;
-- 走 document_embed_hnsw
```
