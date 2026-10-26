-- ============================================================================
-- 050 检索层 search —— 精确/面聚合 + 全文 + 模糊 + 语义
-- ----------------------------------------------------------------------------
-- 对应总体架构图 [检索层]：
--   精确/面聚合：PG 列 + GIN
--   全文：      tsvector（中文用 jieba 预分词写入 content_seg，可平滑升级 zhparser/OpenSearch）
--   语义：      pgvector HNSW
--
-- 为什么不直接在业务表上建索引？
--   因为"检索单元"与"事实单元"不是一一对应：一篇论文的 wiki、11 张图、3 条公式
--   都要能被同一个查询召回。所以收敛成一张 search.document 宽表，
--   doc_id 指回 core 的具体实体。
-- ============================================================================

CREATE TABLE search.document (
    doc_id      text PRIMARY KEY,
    doc_type    text NOT NULL CHECK (doc_type IN
                  ('paper','wiki','figure','table','equation','finding','trace','block')),
    paper_id    text NOT NULL,
    sample_id   text,
    ref_id      text,                                    -- figure_001 / equation_001 / b0012 …
    title       text,
    body        text NOT NULL,                           -- 原文（展示用）
    content_seg text NOT NULL,                           -- 分词文本（索引用；中文经 jieba）
    lang        text,                                    -- zh | en | mixed
    tsv         tsvector GENERATED ALWAYS AS
                  (to_tsvector('simple', coalesce(content_seg,''))) STORED,
    embed       vector(384),
    embed_model text,
    meta        jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON search.document USING gin (tsv);
CREATE INDEX ON search.document USING gin (body gin_trgm_ops);
CREATE INDEX ON search.document (doc_type);
CREATE INDEX ON search.document (paper_id);
CREATE INDEX ON search.document (sample_id);
-- 语义索引：余弦距离。68 篇规模下 HNSW 建索引是毫秒级，量级到百万级仍然可用。
CREATE INDEX document_embed_hnsw ON search.document
    USING hnsw (embed vector_cosine_ops) WITH (m = 16, ef_construction = 64);
COMMENT ON TABLE  search.document IS '统一检索文档：一张表覆盖论文摘要/wiki/图/表/公式/未归类发现，支持全文+模糊+向量三路召回';
COMMENT ON COLUMN search.document.content_seg IS
  '预分词文本。中文由 ETL 侧 jieba 切分后写入；迁移到 zhparser 后可退化为原文';

-- ---------------------------------------------------------------------------
-- 三路召回 + RRF 融合
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION search.text_rank(p_seg text, p_limit integer DEFAULT 200)
RETURNS TABLE(doc_id text, rank real)
LANGUAGE sql STABLE AS $$
    -- p_seg 必须是已分词文本；websearch_to_tsquery 容忍空串与语法错误
    SELECT d.doc_id, ts_rank_cd(d.tsv, q.query)::real
    FROM search.document d,
         websearch_to_tsquery('simple', coalesce(nullif(p_seg,''), 'zzzz')) AS q(query)
    WHERE d.tsv @@ q.query
    ORDER BY 2 DESC
    LIMIT p_limit;
$$;
COMMENT ON FUNCTION search.text_rank IS '全文召回；按 ts_rank_cd 排序（覆盖密度 + 词频）';

CREATE OR REPLACE FUNCTION search.fuzzy_rank(p_raw text, p_limit integer DEFAULT 200)
RETURNS TABLE(doc_id text, rank real)
LANGUAGE sql STABLE AS $$
    -- 中文长查询与长正文的整串相似度天然偏低，因此同时用 word_similarity
    -- （"查询串与正文中最相似片段的相似度"）作为补充信号。
    SELECT d.doc_id,
           greatest(similarity(d.body, p_raw), word_similarity(p_raw, d.body))::real
    FROM search.document d
    WHERE d.body % p_raw
       OR word_similarity(p_raw, d.body) > 0.35
    ORDER BY 2 DESC
    LIMIT p_limit;
$$;
COMMENT ON FUNCTION search.fuzzy_rank IS 'pg_trgm 模糊召回：对中文短查询、拼写差异、分词失败场景兜底';

CREATE OR REPLACE FUNCTION search.semantic_rank(p_embed vector, p_limit integer DEFAULT 200)
RETURNS TABLE(doc_id text, rank real)
LANGUAGE sql STABLE AS $$
    SELECT d.doc_id, (1 - (d.embed <=> p_embed))::real
    FROM search.document d
    WHERE d.embed IS NOT NULL
    ORDER BY d.embed <=> p_embed
    LIMIT p_limit;
$$;
COMMENT ON FUNCTION search.semantic_rank IS '向量召回（余弦）；p_embed 为 NULL 时不参与融合';

-- Reciprocal Rank Fusion：三路排名直接相加，无需归一化各分数量纲
CREATE OR REPLACE FUNCTION search.hybrid(
    p_seg   text,
    p_raw   text,
    p_embed vector DEFAULT NULL,
    p_k     integer DEFAULT 20,
    p_types text[]  DEFAULT NULL
) RETURNS TABLE(
    doc_id   text,
    doc_type text,
    paper_id text,
    sample_id text,
    title    text,
    snippet  text,
    score    real,
    signals  jsonb
)
LANGUAGE sql STABLE AS $$
    WITH
    t AS (SELECT *, row_number() OVER (ORDER BY rank DESC) AS r FROM search.text_rank(p_seg, 200)),
    f AS (SELECT *, row_number() OVER (ORDER BY rank DESC) AS r FROM search.fuzzy_rank(p_raw, 200)),
    v AS (SELECT *, row_number() OVER (ORDER BY rank DESC) AS r
          FROM search.semantic_rank(p_embed, 200) WHERE p_embed IS NOT NULL),
    fused AS (
        SELECT u.doc_id,
               MIN(u.r) AS best_r,
               SUM(1.0 / (60 + u.r))::real AS rrf,
               jsonb_object_agg(u.src, round(u.rank::numeric, 4)) AS signals
        FROM (
            SELECT doc_id, r, rank, 'text'   AS src FROM t
            UNION ALL SELECT doc_id, r, rank, 'fuzzy'  FROM f
            UNION ALL SELECT doc_id, r, rank, 'vector' FROM v
        ) u
        GROUP BY u.doc_id
    )
    SELECT d.doc_id, d.doc_type, d.paper_id, d.sample_id, d.title,
           left(d.body, 320) AS snippet,
           fs.rrf AS score,
           fs.signals
    FROM fused fs
    JOIN search.document d USING (doc_id)
    WHERE p_types IS NULL OR d.doc_type = ANY (p_types)
    ORDER BY fs.rrf DESC
    LIMIT p_k;
$$;
COMMENT ON FUNCTION search.hybrid IS
  'RRF 融合三路召回（k=60）。任一信号缺失时自动降级：无 embed 则只用全文+模糊';
