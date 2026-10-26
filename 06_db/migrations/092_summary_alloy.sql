-- ============================================================================
-- 092 api.sample_summary 暴露 alloy_id
-- ----------------------------------------------------------------------------
-- 分析场景常需要从样品直接连回成分长表（core.alloy_element），
-- 缺 alloy_id 就必须绕道 core.sample。视图属于消费层契约，用重建方式演进。
-- ============================================================================
DROP VIEW IF EXISTS api.sample_summary CASCADE;

CREATE VIEW api.sample_summary AS
SELECT s.paper_id, s.sample_id, s.alloy_id, s.label,
       a.formula, a.chemsys, a.family_key, a.elements,
       p.year, p.title AS paper_title,
       ys.value_canonical   AS yield_strength_mpa,
       uts.value_canonical  AS tensile_strength_mpa,
       el.value_canonical   AS elongation_pct,
       ra.value_canonical   AS reduction_of_area_pct,
       hv.value_canonical   AS hardness,
       hv.unit_canonical    AS hardness_scale,
       rho.value_canonical  AS density_g_cm3,
       e.value_canonical    AS youngs_modulus_gpa,
       fer.vf               AS ferrite_pct,
       aus.vf               AS austenite_pct,
       gs.grain_um          AS grain_size_um,
       (SELECT count(*) FROM core.property_value v
          WHERE v.paper_id = s.paper_id AND v.sample_id = s.sample_id
            AND v.value_canonical IS NOT NULL) AS n_numeric_properties
FROM core.sample s
JOIN core.alloy a  ON a.paper_id  = s.paper_id AND a.alloy_id  = s.alloy_id
JOIN core.paper p  ON p.paper_id  = s.paper_id
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'yield_strength'
    ORDER BY idx LIMIT 1) ys ON true
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'ultimate_tensile_strength'
    ORDER BY idx LIMIT 1) uts ON true
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'elongation'
    ORDER BY idx LIMIT 1) el ON true
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'reduction_of_area'
    ORDER BY idx LIMIT 1) ra ON true
LEFT JOIN LATERAL (
    SELECT value_canonical, unit_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id
      AND metric = 'hardness'
      AND unit_canonical IN ('HV','HRC','HB','MPa')
    ORDER BY (unit_canonical = 'HV') DESC, idx LIMIT 1) hv ON true
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'density'
    ORDER BY idx LIMIT 1) rho ON true
LEFT JOIN LATERAL (
    SELECT value_canonical FROM core.property_value
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND metric = 'youngs_modulus'
    ORDER BY idx LIMIT 1) e ON true
LEFT JOIN LATERAL (
    SELECT max(volume_fraction_pct) AS vf FROM core.phase
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND phase_name ILIKE '%ferrite%'
    ) fer ON true
LEFT JOIN LATERAL (
    SELECT max(volume_fraction_pct) AS vf FROM core.phase
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND phase_name ILIKE '%austenite%'
    ) aus ON true
LEFT JOIN LATERAL (
    SELECT max(grain_size_um) AS grain_um FROM core.phase
    WHERE paper_id = s.paper_id AND sample_id = s.sample_id AND grain_size_um IS NOT NULL
    ) gs ON true;
