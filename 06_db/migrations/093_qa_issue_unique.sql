-- ============================================================================
-- 093 ops.qa_issue 改为"当前状态快照"
-- ----------------------------------------------------------------------------
-- 之前每次入库都追加新行，同一问题在多轮重跑后重复累积（例如 7,677 行历史
-- BLOCK_ID_DANGLING 早已修复）。改为按 (rule_code, paper_id, subject) 唯一，
-- 重复检测时 UPDATE 而非 INSERT，保证表里永远是"现在的问题清单"。
-- ============================================================================
UPDATE ops.qa_issue SET paper_id = coalesce(paper_id, ''), subject = coalesce(subject, '');
ALTER TABLE ops.qa_issue ALTER COLUMN paper_id SET DEFAULT '';
ALTER TABLE ops.qa_issue ALTER COLUMN subject  SET DEFAULT '';
ALTER TABLE ops.qa_issue ALTER COLUMN paper_id SET NOT NULL;
ALTER TABLE ops.qa_issue ALTER COLUMN subject  SET NOT NULL;
DELETE FROM ops.qa_issue a USING ops.qa_issue b
 WHERE a.issue_id > b.issue_id
   AND a.rule_code = b.rule_code AND a.paper_id = b.paper_id AND a.subject = b.subject;
CREATE UNIQUE INDEX IF NOT EXISTS qa_issue_unique
    ON ops.qa_issue (rule_code, paper_id, subject);
COMMENT ON TABLE ops.qa_issue IS
  '当前质量问题快照：按 (rule_code, paper_id, subject) 唯一，重跑更新而非追加';
