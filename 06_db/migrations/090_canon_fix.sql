-- ============================================================================
-- 090 词表修正：让合金族规则在真实语料上可解释
-- ----------------------------------------------------------------------------
-- 首轮入库暴露两个问题：
--   1) pure_metal 的规则用了未实现的谓词 has_element_carbon，
--      导致它退化成了"兜底类"，语义不可解释；
--   2) 语料里大量 Fe-Al / Fe-Mn 二元、三元合金落到最粗的 steel 类，
--      分面粒度不够，无法支撑"Fe-Al 系 vs Fe-Mn-Al-C 系"的对比分析。
-- 迁移原则：不删历史，只修正规则与新增族（ETL 重跑后自动重新分类）。
-- ============================================================================

UPDATE canon.alloy_family
SET rule = '{"all":[{"base_element":"Fe"},{"element_at_most":{"C":0.05}},
                    {"element_at_most":{"Mn":1.0}},{"element_at_most":{"Al":0.5}},
                    {"element_at_most":{"Cr":1.0}}]}',
    description = '近乎不含合金元素的纯铁/工业纯铁（C≤0.05、Mn≤1、Al≤0.5、Cr≤1）'
WHERE family_key = 'pure_metal';

INSERT INTO canon.alloy_family (family_key, name, name_zh, description, parent_key, rule) VALUES
('fe_al', 'Fe-Al alloy', 'Fe-Al 合金',
 'Fe 基 + Al 为主要合金元素（Al ≥ 5 wt%，Mn < 3 wt%），典型的 B2/DO3 有序固溶与轻量化体系',
 NULL,
 '{"all":[{"base_element":"Fe"},{"element_at_least":{"Al":5.0}},{"element_at_most":{"Mn":3.0}}]}'),
('fe_mn', 'Fe-Mn alloy', 'Fe-Mn 合金',
 'Fe 基 + Mn 为主要合金元素（Mn 3–15 wt%，Al < 3 wt%），中锰/高锰奥氏体体系',
 NULL,
 '{"all":[{"base_element":"Fe"},{"element_range":{"Mn":[3.0,15.0]}},{"element_at_most":{"Al":3.0}}]}'),
('fe_cr', 'Fe-Cr alloy', 'Fe-Cr 合金',
 'Fe 基 + Cr 为主要合金元素但未达不锈钢门槛（Cr 3–10.5 wt%）',
 NULL,
 '{"all":[{"base_element":"Fe"},{"element_range":{"Cr":[3.0,10.5]}}]}')
ON CONFLICT (family_key) DO NOTHING;

-- 新增族后，把父级关系补上（Fe-Al/Fe-Mn 属于广义钢/铁基合金谱系）
UPDATE canon.alloy_family SET parent_key = 'steel' WHERE family_key IN ('fe_mn', 'fe_cr');

INSERT INTO ops.qa_rule (rule_code, severity, title, description) VALUES
('PROPERTY_EMPTY', 'info', '样品没有结构化性能数据',
 'sample 存在但 property_value 为空。多数是纯组织表征样品，也可能是提取阶段漏抽，需按篇抽查'),
('FAMILY_UNCLASSIFIED', 'info', '合金未能归入任何合金族',
 'canon.alloy_family 规则未命中。既是分类规则的改进信号，也可能是新体系')
ON CONFLICT (rule_code) DO NOTHING;
