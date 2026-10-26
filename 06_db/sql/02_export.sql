-- ============================================================================
-- 下游导出 SQL
-- ----------------------------------------------------------------------------
-- 训练/RAG/评测数据从这里出。每个导出行都保留 provenance，
-- 便于回溯到论文与原文段落（合规与可审计）。
-- ============================================================================

-- A. 样品级宽表（CSV 导出，给 Excel / DataFrame）
COPY (
    SELECT s.paper_id, s.sample_id, s.label, s.formula, s.chemsys, s.family_key,
           s.year, s.paper_title,
           s.yield_strength_mpa, s.tensile_strength_mpa, s.elongation_pct,
           s.reduction_of_area_pct, s.hardness, s.hardness_scale,
           s.density_g_cm3, s.youngs_modulus_gpa,
           s.ferrite_pct, s.austenite_pct, s.grain_size_um,
           s.n_numeric_properties
    FROM api.sample_summary s
    ORDER BY s.paper_id, s.sample_id
) TO STDOUT WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- B. 长表（属性量，适合做统计建模）
COPY (
    SELECT paper_id, sample_id, section, metric, value_kind,
           value_canonical, unit_canonical, value_raw, qualifier,
           array_to_string(source_block_ids, '|') AS source_block_ids
    FROM api.property
    WHERE value_canonical IS NOT NULL
    ORDER BY paper_id, sample_id, metric
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- C. RAG 语料（文档 + 元数据 + 向量，pgvector 文本格式）
COPY (
    SELECT doc_id, doc_type, paper_id, sample_id, title, body,
           embed::text AS embedding, embed_model
    FROM search.document
    WHERE embed IS NOT NULL
    ORDER BY doc_id
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- D. 带证据的问答对素材（问题=指标+样品，答案=值，引用=原文）
COPY (
    SELECT p.paper_id, p.sample_id, p.metric, p.value_raw, p.value_canonical,
           p.unit_canonical,
           (SELECT string_agg(b.text, E'\n')
              FROM core.evidence_block b
             WHERE b.paper_id = p.paper_id AND b.block_id = ANY (p.source_block_ids)) AS evidence_text
    FROM core.property_value p
    WHERE cardinality(p.source_block_ids) > 0
    ORDER BY p.paper_id, p.sample_id, p.metric
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- E. 整篇 JSONL（一个样品一行，含成分/工艺/相/性能/叙述/溯源）
COPY (
    SELECT jsonb_build_object(
        'material_id', s.paper_id || ':' || s.sample_id,
        'doc', api.material_document(s.paper_id, s.sample_id))
    FROM core.sample s
    ORDER BY s.paper_id, s.sample_id
) TO STDOUT;
