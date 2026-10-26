-- ============================================================================
-- 025 规范化层 canon —— 受控词表（跨论文消解的锚点）
-- ----------------------------------------------------------------------------
-- 设计原则 4：两级身份。
--   第一级（core）：paper 内实体用复合键 (paper_id, entity_id)，忠实保留原文表述；
--   第二级（canon）：跨论文的"同一合金/同一相"不做建库时强行合并，只提供
--                    受控词表 + 一个 later-resolution 的挂载点。
-- 因此 core 表里只有 family_key / phase_key 这类可空外键，填错也不影响保真。
-- ============================================================================

CREATE TABLE canon.element (
    symbol        text PRIMARY KEY,
    name_en       text NOT NULL,
    name_zh       text,
    atomic_number integer NOT NULL,
    atomic_mass   numeric(9,4) NOT NULL,
    category      text,                          -- transition metal / metalloid / nonmetal ...
    is_steel_relevant boolean NOT NULL DEFAULT false
);
COMMENT ON TABLE canon.element IS '元素周期表子集，用于成分解析、chemsys 计算与元素维度过滤';

CREATE TABLE canon.alloy_family (
    family_key  text PRIMARY KEY,
    name        text NOT NULL,
    name_zh     text,
    description text,
    rule        jsonb NOT NULL DEFAULT '{}'::jsonb,   -- 判定规则快照（人工/规则引擎写入）
    parent_key  text REFERENCES canon.alloy_family(family_key)
);
COMMENT ON TABLE canon.alloy_family IS
  '合金族/钢种分类（可多层）。core.alloy.family_key 由规则引擎赋值，NULL 表示未分类，可人工回填';

CREATE TABLE canon.phase (
    phase_key        text PRIMARY KEY,
    name             text NOT NULL,
    name_zh          text,
    formula          text,
    crystal_structure text,
    family           text,                       -- fcc / bcc / hcp / intermetallic / inclusion ...
    aliases          text[] NOT NULL DEFAULT '{}',
    notes            text
);
COMMENT ON TABLE canon.phase IS '相/组织的受控词表；core.phase.phase_key 由名称+别名+形貌规则匹配得到';
CREATE INDEX ON canon.phase USING gin (aliases);

CREATE TABLE canon.characterization_technique (
    technique_key text PRIMARY KEY,
    name          text NOT NULL,
    abbreviation  text,
    category      text,                          -- microscopy / diffraction / thermal / mechanical ...
    aliases       text[] NOT NULL DEFAULT '{}'
);
COMMENT ON TABLE canon.characterization_technique IS '表征手段受控词表，用于"哪些样品做过 EBSD"这类过滤';
CREATE INDEX ON canon.characterization_technique USING gin (aliases);
