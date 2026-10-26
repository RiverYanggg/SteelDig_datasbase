-- ============================================================================
-- 080 消费层 api —— 只读视图与函数
-- ----------------------------------------------------------------------------
-- 对应总体架构图 [消费层] 查询 API / RAG Agent / 分析看板 / 下游训练数据导出。
-- 消费层只读：所有写路径都必须走 ETL，保证"湖 → 仓 → 消费"单向流动。
--
-- api.v_sample_summary 是仿 Materials Project summary 文档的宽表：
-- 一行一个样品，把最常被过滤/展示的维度拍平成列，其余仍在 core 里保真。
-- ============================================================================

CREATE VIEW api.paper AS
SELECT p.paper_id, p.doi, p.title, p.journal, p.year, p.research_type,
       p.authors, p.keywords, p.paper_scope, p.page_count,
       p.block_count, p.figure_count, p.section_headings,
       p.run_id, p.qa_flags,
       (SELECT count(*) FROM core.sample s WHERE s.paper_id = p.paper_id) AS n_samples,
       (SELECT count(*) FROM core.alloy a WHERE a.paper_id = p.paper_id)  AS n_alloys,
       (SELECT count(*) FROM core.figure f WHERE f.paper_id = p.paper_id) AS n_figures,
       (SELECT count(*) FROM core.equation e WHERE e.paper_id = p.paper_id) AS n_equations
FROM core.paper p;
COMMENT ON VIEW api.paper IS '论文列表/详情：带各实体计数，避免 N+1 查询';

-- ---------------------------------------------------------------------------
CREATE VIEW api.sample AS
SELECT s.paper_id, s.sample_id, s.label, s.alloy_id, s.process_id,
       a.name AS alloy_name, a.formula, a.formula_alpha, a.chemsys, a.elements,
       a.n_elements, a.family_key, fam.name_zh AS family_name_zh,
       pr.name AS process_name, pr.state_label,
       p.title AS paper_title, p.doi, p.year, p.journal, p.run_id,
       (SELECT count(*) FROM core.property_value v
          WHERE v.paper_id = s.paper_id AND v.sample_id = s.sample_id) AS n_properties,
       (SELECT count(*) FROM core.phase ph
          WHERE ph.paper_id = s.paper_id AND ph.sample_id = s.sample_id) AS n_phases,
       (SELECT count(*) FROM core.processing_step ps
          WHERE ps.paper_id = s.paper_id AND ps.sample_id = s.sample_id) AS n_steps
FROM core.sample s
JOIN core.alloy a ON a.paper_id = s.paper_id AND a.alloy_id = s.alloy_id
LEFT JOIN core.process pr ON pr.paper_id = s.paper_id AND pr.process_id = s.process_id
LEFT JOIN canon.alloy_family fam ON fam.family_key = a.family_key
JOIN core.paper p ON p.paper_id = s.paper_id;
COMMENT ON VIEW api.sample IS '样品主视图：合金成分、体系、合金族、工艺、论文元数据一次取齐';

-- ---------------------------------------------------------------------------
-- 仿 MP summary：常用性能拍平为列（单位已统一）
-- ---------------------------------------------------------------------------
CREATE VIEW api.sample_summary AS
SELECT s.paper_id, s.sample_id, s.label,
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
COMMENT ON VIEW api.sample_summary IS
  '仿 Materials Project summary 文档：把屈服/抗拉/延伸/硬度/密度/相分数拍平为可过滤的数值列';

-- ---------------------------------------------------------------------------
CREATE VIEW api.property AS
SELECT v.paper_id, v.sample_id, s.label, a.formula, a.chemsys, a.family_key,
       v.section, v.group_path, v.metric, v.path,
       v.value_raw, v.value_kind, v.value_num, v.value_low, v.value_high,
       v.value_unit, v.unit_canonical, v.value_canonical,
       v.value_low_canonical, v.value_high_canonical,
       v.qualifier, v.uncertainty_raw, v.direction, v.block_status,
       v.conditions, v.source_block_ids
FROM core.property_value v
JOIN core.sample s ON s.paper_id = v.paper_id AND s.sample_id = v.sample_id
JOIN core.alloy a  ON a.paper_id = s.paper_id AND a.alloy_id  = s.alloy_id;
COMMENT ON VIEW api.property IS '性能量（含原文、数值、单位归一、溯源状态），供过滤与导出';

-- ---------------------------------------------------------------------------
CREATE VIEW api.figure AS
SELECT f.paper_id, f.figure_id, f.kind, f.label, f.image_type, f.description,
       f.confidence, f.n_subfigures, f.n_observations, f.n_measured,
       f.image_paths, f.block_ids, f.page_idx, f.ordinal,
       (SELECT string_agg(e.text, E'\n' ORDER BY e.ordinal)
          FROM core.evidence_block e
         WHERE e.paper_id = f.paper_id AND e.block_id = ANY (f.block_ids)) AS caption_text,
       (SELECT count(*) FROM core.figure_observation o
         WHERE o.paper_id = f.paper_id AND o.figure_id = f.figure_id
           AND o.block_status = 'ok') AS n_observations_traced
FROM core.figure f;
COMMENT ON VIEW api.figure IS '图表视图：描述 + 题注原文（已按对齐后的真实 block 拼回）';

CREATE VIEW api.equation AS
SELECT e.paper_id, e.equation_id, e.block_id, e.equation_number, e.latex, e.purpose,
       e.applicability, e.symbols, e.n_symbols,
       b.text AS source_text
FROM core.equation e
LEFT JOIN core.evidence_block b
       ON b.paper_id = e.paper_id AND b.block_id = e.block_id;
COMMENT ON VIEW api.equation IS '公式视图：附带所在段落原文，便于人工核验';

-- ---------------------------------------------------------------------------
-- 工艺链：把逐步表折叠成"熔炼 → 锻造 → …"的可读序列
-- ---------------------------------------------------------------------------
CREATE VIEW api.process_chain AS
SELECT ps.paper_id, ps.sample_id,
       string_agg(
           concat_ws(' · ',
               ps.step_type,
               ps.method,
               ps.temperature_raw,
               ps.duration_raw,
               ps.cooling_medium),
           ' → ' ORDER BY ps.seq) AS chain_text,
       array_agg(ps.step_type ORDER BY ps.seq) AS step_types,
       max(ps.temperature_k) AS max_temperature_k,
       sum(ps.duration_s)   AS total_duration_s,
       count(*) AS n_steps
FROM core.processing_step ps
GROUP BY ps.paper_id, ps.sample_id;
COMMENT ON VIEW api.process_chain IS '工艺链折叠视图，用于列表展示与"含退火/含淬火"式过滤';

-- ---------------------------------------------------------------------------
-- 溯源联查：事实值 ↔ 证据原文
-- ---------------------------------------------------------------------------
CREATE VIEW api.trace AS
SELECT t.paper_id, t.sample_id, t.path, t.status, t.block_ids, t.reason,
       (SELECT string_agg(b.text, ' … ') FROM core.evidence_block b
         WHERE b.paper_id = t.paper_id AND b.block_id = ANY (t.block_ids)) AS evidence_text
FROM core.sample_trace t;
COMMENT ON VIEW api.trace IS '溯源明细：每条事实值的证据块与原文，可直接喂给 RAG 做"带引用回答"';

-- ---------------------------------------------------------------------------
-- 统计
-- ---------------------------------------------------------------------------
CREATE VIEW api.stats AS
SELECT (SELECT count(*) FROM core.paper)           AS papers,
       (SELECT count(*) FROM core.alloy)           AS alloys,
       (SELECT count(*) FROM core.sample)          AS samples,
       (SELECT count(*) FROM core.property_value)  AS properties,
       (SELECT count(*) FROM core.property_value WHERE value_canonical IS NOT NULL) AS numeric_properties,
       (SELECT count(*) FROM core.phase)           AS phases,
       (SELECT count(*) FROM core.processing_step) AS processing_steps,
       (SELECT count(*) FROM core.figure)          AS figures,
       (SELECT count(*) FROM core.equation)        AS equations,
       (SELECT count(*) FROM core.evidence_block)  AS evidence_blocks,
       (SELECT count(*) FROM search.document)      AS search_documents,
       (SELECT count(*) FROM search.document WHERE embed IS NOT NULL) AS embedded_documents,
       (SELECT count(*) FROM lake.object)          AS lake_objects,
       (SELECT coalesce(sum(bytes),0) FROM lake.object) AS lake_bytes;

-- ---------------------------------------------------------------------------
-- Materials Project 风格的"材料文档"（可直接进下游训练集/导出 JSON）
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION api.material_document(p_paper_id text, p_sample_id text)
RETURNS jsonb
LANGUAGE sql STABLE AS $$
    SELECT jsonb_build_object(
        'material_id', p_paper_id || ':' || p_sample_id,
        'paper', jsonb_build_object(
            'doi', p.doi, 'title', p.title, 'year', p.year,
            'journal', p.journal, 'authors', p.authors, 'research_type', p.research_type),
        'sample', jsonb_build_object(
            'sample_id', s.sample_id, 'label', s.label,
            'alloy_id', s.alloy_id, 'process_id', s.process_id),
        'composition', jsonb_build_object(
            'formula', a.formula, 'chemsys', a.chemsys, 'elements', a.elements,
            'family', a.family_key,
            'elements_wt_pct', (
                SELECT jsonb_object_agg(ae.element, ae.weight_pct)
                FROM core.alloy_element ae
                WHERE ae.paper_id = a.paper_id AND ae.alloy_id = a.alloy_id
                  AND ae.weight_pct IS NOT NULL)),
        'processing', (
            SELECT jsonb_agg(jsonb_build_object(
                       'seq', ps.seq, 'type', ps.step_type, 'method', ps.method,
                       'temperature_k', ps.temperature_k, 'duration_s', ps.duration_s,
                       'atmosphere', ps.atmosphere, 'cooling_medium', ps.cooling_medium)
                       ORDER BY ps.seq)
            FROM core.processing_step ps
            WHERE ps.paper_id = s.paper_id AND ps.sample_id = s.sample_id),
        'phases', (
            SELECT jsonb_agg(jsonb_build_object(
                       'phase', ph.phase_name, 'volume_fraction_pct', ph.volume_fraction_pct,
                       'grain_size_um', ph.grain_size_um, 'morphology', ph.morphology))
            FROM core.phase ph
            WHERE ph.paper_id = s.paper_id AND ph.sample_id = s.sample_id),
        'properties', (
            SELECT jsonb_agg(jsonb_build_object(
                       'metric', v.metric, 'value', v.value_canonical,
                       'low', v.value_low_canonical, 'high', v.value_high_canonical,
                       'unit', v.unit_canonical, 'raw', v.value_raw,
                       'kind', v.value_kind, 'section', v.section,
                       'block_status', v.block_status) ORDER BY v.section, v.metric)
            FROM core.property_value v
            WHERE v.paper_id = s.paper_id AND v.sample_id = s.sample_id),
        'evidence_blocks', (
            SELECT count(*) FROM core.sample_trace t
            WHERE t.paper_id = s.paper_id AND t.sample_id = s.sample_id AND t.status = 'ok'),
        'narrative', (SELECT w.payload FROM core.sample_wiki w
                       WHERE w.paper_id = s.paper_id AND w.sample_id = s.sample_id),
        'figures', (
            SELECT jsonb_agg(jsonb_build_object('figure_id', f.figure_id, 'caption', f.label))
            FROM core.figure f WHERE f.paper_id = s.paper_id),
        'provenance', jsonb_build_object(
            'run_id', s.paper_id::text,
            'extractor', (SELECT r.extractor || '/' || coalesce(r.model,'') FROM ops.run r
                           WHERE r.run_id = p.run_id),
            'dataset_version', (SELECT r.dataset_version FROM ops.run r WHERE r.run_id = p.run_id))
    )
    FROM core.sample s
    JOIN core.alloy a ON a.paper_id = s.paper_id AND a.alloy_id = s.alloy_id
    JOIN core.paper p ON p.paper_id = s.paper_id
    WHERE s.paper_id = p_paper_id AND s.sample_id = p_sample_id;
$$;
COMMENT ON FUNCTION api.material_document IS
  '单样品完整文档（仿 MP summary doc）：成分/工艺/相/性能/叙述/溯源一次导出';

GRANT USAGE ON SCHEMA api TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA api TO PUBLIC;
