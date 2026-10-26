-- ============================================================================
-- 100 校订层 curate —— 人工增删改的唯一入口
-- ----------------------------------------------------------------------------
-- 为什么不能直接 UPDATE core.*？
--   事实层由 ETL 从资产湖重建：ingest 一篇论文 = DELETE 本篇 + 重新 COPY。
--   直接 UPDATE 的值下一次重跑就会被覆盖（已实测验证）。
--
-- 所以写入模型必须是三层的：
--   湖（不可变） → core（可重建） → curate（人工增量，持久，可审计）
--
-- curate.change 记录"人对事实的修正"，ingest 结束后统一重新应用。
-- 因此人工修改既能持久化，又不会污染来源数据，还能随时撤销。
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS curate;

CREATE TABLE curate.change (
    change_id    bigserial PRIMARY KEY,
    op           text NOT NULL CHECK (op IN ('update','create','delete')),
    target_table text NOT NULL,                 -- 只允许白名单内的表，见 etl/steeldig_db/curate.py
    target_key   jsonb NOT NULL,                -- 行定位键，如 {"paper_id": "...", "sample_id": "..."}
    field        text,                          -- update 时的列名
    old_value    jsonb,                         -- 变更前的值（自动快照）
    new_value    jsonb,                         -- 变更后的值 / create 的整行
    status       text NOT NULL DEFAULT 'applied'
                 CHECK (status IN ('applied','reverted','failed')),
    error        text,
    note         text,
    author       text NOT NULL DEFAULT 'anonymous',
    source       text NOT NULL DEFAULT 'api',   -- api | ui | cli | import
    created_at   timestamptz NOT NULL DEFAULT now(),
    applied_at   timestamptz
);
CREATE INDEX ON curate.change (target_table, status);
CREATE INDEX ON curate.change (created_at DESC);
CREATE INDEX ON curate.change USING gin (target_key);
COMMENT ON TABLE curate.change IS
  '人工校订流水：每一次增删改一行。ingest 结束后由 curate.apply 重新应用，因此不会被重跑覆盖';

-- 当前生效的校订（视图：便于审计"这条数据被人改过没有"）
CREATE VIEW curate.active_change AS
SELECT c.*, c.target_key ->> 'paper_id' AS paper_id
FROM curate.change c
WHERE c.status = 'applied';

COMMENT ON VIEW curate.active_change IS '当前生效的校订，供 UI 与报表使用';

-- 每篇论文的校订次数（质量报告里用）
CREATE VIEW curate.paper_change_count AS
SELECT target_key ->> 'paper_id' AS paper_id,
       count(*) AS n,
       count(*) FILTER (WHERE status = 'applied') AS n_active,
       max(created_at) AS last_change
FROM curate.change
GROUP BY 1;
