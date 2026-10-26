-- ============================================================================
-- 001 扩展与 Schema 骨架
-- ----------------------------------------------------------------------------
-- 分层对应《数据库建立》总体架构图：
--
--   [消费层]  api  —— 只读视图/函数，供 REST API / RAG / BI 使用
--   [检索层]  search —— 统一检索文档（tsvector + pg_trgm + pgvector）
--   [事实源]  core —— 实体表（列）+ JSONB（保真）+ trace
--             lake —— 资产湖目录（内容寻址，写入后不可变）
--             ops  —— 运行版本、入库日志、质量门禁
--             canon —— 跨论文消解用的受控词表（元素/相/合金族）
--
-- 依赖扩展：
--   vector    pgvector —— 语义检索（HNSW）
--   pg_trgm   三元组模糊匹配 —— 中文/拼写容错、LIKE 加速
--   btree_gin 复合 GIN 索引（低频标量 + 数组/GIN 列组合过滤）
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

CREATE SCHEMA IF NOT EXISTS ops;     -- 运行与治理
CREATE SCHEMA IF NOT EXISTS lake;    -- 资产湖（不可变对象）
CREATE SCHEMA IF NOT EXISTS core;    -- 事实层（实体 + 保真 JSONB）
CREATE SCHEMA IF NOT EXISTS canon;   -- 规范化 / 消解层
CREATE SCHEMA IF NOT EXISTS search;  -- 检索层
CREATE SCHEMA IF NOT EXISTS api;     -- 消费层（只读）

COMMENT ON SCHEMA ops    IS '运行版本、入库日志、数据质量门禁（可写，运维用）';
COMMENT ON SCHEMA lake   IS '资产湖目录：内容寻址、写入后不可变；真实字节存放在本地/S3/MinIO';
COMMENT ON SCHEMA core   IS '事实层：论文/合金/工艺/样品/图/公式/证据块，列 + JSONB 保真';
COMMENT ON SCHEMA canon  IS '跨论文消解的受控词表：元素、相、合金族（不在建库时强行合并）';
COMMENT ON SCHEMA search IS '检索层：统一文档表 + 全文/模糊/向量索引';
COMMENT ON SCHEMA api    IS '消费层：面向 API 的只读视图与函数';
