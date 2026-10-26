-- ============================================================================
-- 020 资产湖 lake —— 内容寻址、写入后不可变
-- ----------------------------------------------------------------------------
-- 对应总体架构图最底层 [资产湖] 对象存储(MinIO/S3/OSS) — 原始 JSON + 图片。
--
-- 关键思想：文件是"湖"（immutable，可重建一切），数据库是"仓"
-- （为查询组织，可随时从湖重建）。因此：
--   1. 湖里的每个对象以 sha256 命名，同一份字节只存一次；
--   2. 表里只记录"哪个对象被哪个逻辑位置引用"，不重复存字节；
--   3. DB 的所有事实行都带对象引用，随时可回湖校验（re-hash）。
-- ============================================================================

CREATE TABLE lake.object (
    object_id   text PRIMARY KEY CHECK (object_id ~ '^[0-9a-f]{64}$'),
    bytes       bigint NOT NULL CHECK (bytes >= 0),
    media_type  text   NOT NULL,
    kind        text   NOT NULL CHECK (kind IN ('json','image','pdf','markdown','text','other')),
    uri         text   NOT NULL,            -- 如 s3://steeldig/lake/sha256/ab/cd/<hash>.json
    created_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE lake.object IS '内容寻址对象表：object_id = sha256(bytes)。写入后永不修改，只增不删';
COMMENT ON COLUMN lake.object.uri IS '存储后端 URI；本地开发为 05_lake/objects/sha256/xx/yy/<hash>.<ext>，生产可平移到 S3/MinIO';

CREATE TABLE lake.object_ref (
    object_id text   NOT NULL REFERENCES lake.object(object_id),
    paper_id  text   NOT NULL,
    rel_path  text   NOT NULL,              -- 相对该论文目录的逻辑路径，如 output/sample/x.data.json
    role      text   NOT NULL,              -- preprocess | discover | sample | trace | wiki | figure | equation | image | pdf
    PRIMARY KEY (paper_id, rel_path)
);
CREATE INDEX ON lake.object_ref (object_id);
CREATE INDEX ON lake.object_ref (paper_id, role);
COMMENT ON TABLE lake.object_ref IS '逻辑路径 → 物理对象。同一字节被多篇引用时自动去重（image 复用很常见）';

CREATE TABLE lake.paper_manifest (
    paper_id     text PRIMARY KEY,
    run_id       text REFERENCES ops.run(run_id),
    object_count integer NOT NULL,
    total_bytes  bigint  NOT NULL,
    manifest     jsonb   NOT NULL,          -- [{rel_path, object_id, bytes, role, media_type}]
    created_at   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE lake.paper_manifest IS '单篇的湖内清单（≈ preprocess/manifest.json 的超集），用于按篇校验与增量重建';

-- ---------------------------------------------------------------------------
-- 湖 → 仓的可验证性：随时重算对象哈希，与 lake.object 比对
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION lake.verify_object(p_object_id text)
RETURNS boolean
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_uri text;
BEGIN
    SELECT uri INTO v_uri FROM lake.object WHERE object_id = p_object_id;
    IF v_uri IS NULL THEN
        RETURN false;
    END IF;
    -- 字节级校验由 ETL 侧完成（Python 读文件重算 sha256），SQL 侧只做元数据健全性判断
    RETURN v_uri <> '';
END;
$$;
COMMENT ON FUNCTION lake.verify_object(text) IS '字节级校验在 ETL（etl/steeldig_db/lake.py::verify）。此处只保证元数据可解析';
