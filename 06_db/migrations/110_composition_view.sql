-- ============================================================================
-- 110 成分的"可用视图"：补全余量元素，标记推断值
-- ----------------------------------------------------------------------------
-- 原始 nominal_composition 有两种写法：
--   (a) Fe 写成 "Bal."：weight_pct 为 NULL，is_balance=true
--   (b) 只列合金元素，Fe 根本不出现
-- 直接按成分查询会漏掉 60% 的合金（Fe 查不到值），所以需要一个"有效成分"视图：
--   余额元素 / 基体元素 → 100 − 其余元素之和，并标记 is_inferred=true。
--
-- 这是推断，不是原始数据：真实值仍在 core.alloy_element.weight_pct。
-- 任何对外展示都应同时给出 is_inferred，让使用者知道哪些是算出来的。
-- ============================================================================

CREATE OR REPLACE VIEW api.alloy_composition AS
WITH sums AS (
    SELECT e.paper_id, e.alloy_id,
           sum(e.weight_pct) FILTER (WHERE NOT e.is_balance) AS others
    FROM core.alloy_element e
    GROUP BY 1, 2
),
listed AS (
    SELECT e.paper_id, e.alloy_id, e.element, e.weight_pct, e.raw_wt,
           e.is_balance, a.base_element, coalesce(s.others, 0) AS others
    FROM core.alloy_element e
    JOIN core.alloy a ON a.paper_id = e.paper_id AND a.alloy_id = e.alloy_id
    LEFT JOIN sums s ON s.paper_id = e.paper_id AND s.alloy_id = e.alloy_id
),
resolved AS (
    SELECT paper_id, alloy_id, element,
           CASE
               WHEN is_balance
                    THEN greatest(round(100 - others, 4), 0)
               WHEN weight_pct IS NULL AND element = base_element
                    THEN greatest(round(100 - others, 4), 0)
               ELSE weight_pct
           END AS weight_pct,
           weight_pct AS reported,
           (is_balance OR (weight_pct IS NULL AND element = base_element)) AS is_inferred,
           raw_wt, is_balance
    FROM listed
)
SELECT paper_id, alloy_id, element, weight_pct, reported, is_inferred, raw_wt, is_balance
FROM resolved
UNION ALL
-- 基体元素完全没出现在成分表里的合金：按余额补一行
SELECT a.paper_id, a.alloy_id, a.base_element,
       greatest(round(100 - coalesce(s.others, 0), 4), 0),
       NULL::numeric, true, 'implied by base_element', false
FROM core.alloy a
LEFT JOIN sums s ON s.paper_id = a.paper_id AND s.alloy_id = a.alloy_id
WHERE a.base_element IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM core.alloy_element x
      WHERE x.paper_id = a.paper_id AND x.alloy_id = a.alloy_id
        AND x.element = a.base_element
  );

COMMENT ON VIEW api.alloy_composition IS
  '有效成分（wt%）：余量元素与基体元素按 100−Σ其余 推断，is_inferred 标记推断值；'
  'reported 保留原始上报值（可能为 NULL）';
