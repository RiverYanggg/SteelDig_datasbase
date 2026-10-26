-- ============================================================================
-- 分析用 SQL（可直接在 psql / BI 工具里跑）
-- ----------------------------------------------------------------------------
-- 这些查询是"仓"的典型用法：面向回答业务问题，而不是面向单条记录。
-- ============================================================================

-- 1) 性能–成分趋势：Al 含量 vs 屈服强度（按 1 wt% 分箱）
SELECT width_bucket(e.weight_pct, 0, 12, 12) AS al_bin,
       round(min(e.weight_pct)::numeric, 1) AS al_from,
       count(*) AS n,
       round(avg(s.yield_strength_mpa)::numeric, 0) AS avg_ys,
       round(avg(s.elongation_pct)::numeric, 1) AS avg_el
FROM core.alloy_element e
JOIN api.sample_summary s USING (paper_id, alloy_id)
WHERE e.element = 'Al' AND s.yield_strength_mpa IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- 2) 强塑积排行榜（UTS × EL）
SELECT paper_id, sample_id, formula, yield_strength_mpa, tensile_strength_mpa,
       elongation_pct,
       round((tensile_strength_mpa * elongation_pct / 100)::numeric, 1) AS uts_el_gpa_pct
FROM api.sample_summary
WHERE tensile_strength_mpa IS NOT NULL AND elongation_pct IS NOT NULL
ORDER BY uts_el_gpa_pct DESC NULLS LAST
LIMIT 20;

-- 3) 工艺 → 性能：退火温度与晶粒尺寸
SELECT wt.temperature_k,
       round(avg(ph.grain_size_um)::numeric, 2) AS avg_grain_um,
       count(DISTINCT ps.sample_id) AS n_samples
FROM core.processing_step ps
JOIN (SELECT paper_id, sample_id, max(temperature_k) AS temperature_k
      FROM core.processing_step
      WHERE step_type ILIKE '%heat%' AND temperature_k IS NOT NULL
      GROUP BY 1,2) wt USING (paper_id, sample_id)
JOIN core.phase ph USING (paper_id, sample_id)
WHERE ph.grain_size_um IS NOT NULL
GROUP BY 1 HAVING count(DISTINCT ps.sample_id) >= 2
ORDER BY 1;

-- 4) 相–性能关联：铁素体分数与延伸率
SELECT width_bucket(ferrite_pct, 0, 60, 6) AS ferrite_bin,
       count(*) AS n, round(avg(elongation_pct)::numeric, 1) AS avg_el
FROM api.sample_summary
WHERE ferrite_pct IS NOT NULL AND elongation_pct IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- 5) 年会分布与提取质量
SELECT year, count(*) AS papers,
       round(avg(n_figures), 1) AS avg_figures,
       round(avg(n_samples), 1) AS avg_samples
FROM api.paper WHERE year IS NOT NULL GROUP BY 1 ORDER BY 1;

-- 6) 每个 run 的产物完整度（多模型对比的基础表）
SELECT r.run_id, r.model, count(DISTINCT p.paper_id) AS papers,
       count(DISTINCT sd.sample_id) AS samples,
       count(DISTINCT f.figure_id) AS figures,
       count(DISTINCT e.equation_id) AS equations,
       count(DISTINCT v.path) AS properties
FROM ops.run r
LEFT JOIN core.paper p USING (run_id)
LEFT JOIN core.sample_data sd ON sd.paper_id = p.paper_id
LEFT JOIN core.figure f ON f.paper_id = p.paper_id
LEFT JOIN core.equation e ON e.paper_id = p.paper_id
LEFT JOIN core.property_value v ON v.paper_id = p.paper_id
GROUP BY 1,2 ORDER BY 1;

-- 7) 溯源健康度（按论文）
SELECT t.paper_id,
       count(*) AS trace_rows,
       round(100.0 * count(*) FILTER (WHERE t.status = 'ok') / count(*), 1) AS pct_ok
FROM core.sample_trace t
GROUP BY 1 ORDER BY pct_ok DESC NULLS LAST;

-- 8) 未归类发现的关键词频次（驱动 schema 迭代）
SELECT word, count(*) AS n
FROM core.unmapped_finding,
     unnest(regexp_split_to_array(lower(text), '[^a-z0-9\-]+')) AS word
WHERE length(word) > 4 AND word NOT IN ('which','these','their','there','shown','using')
GROUP BY 1 ORDER BY 2 DESC LIMIT 30;
