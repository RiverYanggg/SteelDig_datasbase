"""API 的 SQL 组装层：把参数化的过滤条件拼成安全的 WHERE 子句。

所有值一律走占位符；只有 limit/offset 这类整数和白名单排序字段会进入字面量。
"""
from __future__ import annotations

from steeldig_db.text import segment  # 与 ETL 共用同一套分词，保证索引/查询一致

__all__ = ["segment", "list_papers", "sample_filters", "process_tree",
           "paper_graph", "block_backlinks", "METRIC_CATALOG"]

METRIC_CATALOG = """
SELECT metric,
       count(*) AS n_rows,
       count(*) FILTER (WHERE value_canonical IS NOT NULL) AS n_numeric,
       mode() WITHIN GROUP (ORDER BY unit_canonical) AS typical_unit,
       min(value_canonical) AS min_value,
       max(value_canonical) AS max_value,
       count(DISTINCT paper_id) AS n_papers
FROM core.property_value
GROUP BY metric
ORDER BY n_rows DESC
"""


def list_papers(fetch_all, fetch_one, q, year_from, year_to, family, limit, offset):
    where, params = ["1=1"], []
    if q:
        where.append("(p.title ILIKE %s OR p.abstract ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if year_from:
        where.append("p.year >= %s")
        params.append(year_from)
    if year_to:
        where.append("p.year <= %s")
        params.append(year_to)
    if family:
        where.append("EXISTS (SELECT 1 FROM core.alloy a WHERE a.paper_id = p.paper_id"
                     " AND a.family_key = %s)")
        params.append(family)
    w = "WHERE " + " AND ".join(where)
    total = fetch_one(f"SELECT count(*) AS n FROM core.paper p {w}", tuple(params))["n"]
    items = fetch_all(
        f"SELECT p.paper_id, p.doi, p.title, p.journal, p.year, p.research_type,"
        f" array(SELECT DISTINCT a.family_key FROM core.alloy a"
        f"       WHERE a.paper_id = p.paper_id AND a.family_key IS NOT NULL) AS families,"
        f" (SELECT count(*) FROM core.sample s WHERE s.paper_id = p.paper_id) AS n_samples,"
        f" (SELECT count(*) FROM core.figure f WHERE f.paper_id = p.paper_id) AS n_figures"
        f" FROM core.paper p {w}"
        f" ORDER BY p.year DESC NULLS LAST, p.paper_id LIMIT {limit} OFFSET {offset}",
        tuple(params))
    return items, total


def sample_filters(family, element, min_ys, max_ys, min_uts, min_elongation, has_ferrite):
    where, params = ["1=1"], []
    if family:
        where.append("s.family_key = %s")
        params.append(family)
    if element:
        where.append("%s = ANY (s.elements)")
        params.append(element)
    if min_ys is not None:
        where.append("s.yield_strength_mpa >= %s")
        params.append(min_ys)
    if max_ys is not None:
        where.append("s.yield_strength_mpa <= %s")
        params.append(max_ys)
    if min_uts is not None:
        where.append("s.tensile_strength_mpa >= %s")
        params.append(min_uts)
    if min_elongation is not None:
        where.append("s.elongation_pct >= %s")
        params.append(min_elongation)
    if has_ferrite is True:
        where.append("s.ferrite_pct > 0")
    elif has_ferrite is False:
        where.append("(s.ferrite_pct IS NULL OR s.ferrite_pct = 0)")
    return "WHERE " + " AND ".join(where), tuple(params)


def process_tree(fetch_all, paper_id: str) -> dict:
    """论文内工艺谱系（parent_process_ids 构成的 DAG）。"""
    nodes = fetch_all(
        "SELECT process_id, name, state_label, aliases FROM core.process"
        " WHERE paper_id = %s ORDER BY process_id", (paper_id,))
    edges = fetch_all(
        "SELECT child_process_id AS source, parent_process_id AS target"
        " FROM core.process_edge WHERE paper_id = %s", (paper_id,))
    return {"nodes": nodes, "edges": edges}


def paper_graph(fetch_all, paper_id: str) -> dict:
    """论文内的实体关系图：合金-(构成)->样品-(工艺)->性能/相/图表。"""
    rows = fetch_all("""
        SELECT 'alloy' AS kind, alloy_id AS id, coalesce(formula, alloy_id) AS label FROM core.alloy
        WHERE paper_id = %s
        UNION ALL
        SELECT 'process', process_id, coalesce(name, process_id) FROM core.process WHERE paper_id = %s
        UNION ALL
        SELECT 'sample', sample_id, coalesce(label, sample_id) FROM core.sample WHERE paper_id = %s
        UNION ALL
        SELECT 'figure', figure_id, coalesce(left(label, 80), figure_id) FROM core.figure
        WHERE paper_id = %s AND figure_id LIKE 'figure%%'
    """, (paper_id, paper_id, paper_id, paper_id))
    edges = fetch_all("""
        SELECT alloy_id AS source, sample_id AS target, 'has_sample' AS rel
        FROM core.sample WHERE paper_id = %s
        UNION ALL
        SELECT sample_id, process_id, 'has_process' FROM core.sample WHERE paper_id = %s
        UNION ALL
        SELECT sample_id, coalesce(alloy_id, process_id), 'mentions'
        FROM core.sample WHERE paper_id = %s
    """, (paper_id, paper_id, paper_id))
    return {"nodes": rows, "edges": edges}


def block_backlinks(fetch_all, paper_id: str, block_id: str) -> dict:
    """反向引用：这个证据块被哪些事实用到。"""
    return {
        "trace": fetch_all(
            "SELECT sample_id, path, status FROM core.sample_trace"
            " WHERE paper_id = %s AND %s = ANY (block_ids) LIMIT 50", (paper_id, block_id)),
        "figure_observations": fetch_all(
            "SELECT figure_id, idx, left(observation, 160) AS observation"
            " FROM core.figure_observation"
            " WHERE paper_id = %s AND %s = ANY (block_ids) LIMIT 50", (paper_id, block_id)),
        "figures": fetch_all(
            "SELECT figure_id, left(label, 160) AS label FROM core.figure"
            " WHERE paper_id = %s AND %s = ANY (block_ids) LIMIT 50", (paper_id, block_id)),
        "alloys": fetch_all(
            "SELECT alloy_id FROM core.alloy"
            " WHERE paper_id = %s AND %s = ANY (source_block_ids)", (paper_id, block_id)),
        "processes": fetch_all(
            "SELECT process_id FROM core.process"
            " WHERE paper_id = %s AND %s = ANY (source_block_ids)", (paper_id, block_id)),
    }
