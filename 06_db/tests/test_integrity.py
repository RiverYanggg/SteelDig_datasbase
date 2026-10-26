"""数据完整性验收测试 —— 库是否"可信"的硬性检查。

这些断言即发布门禁：任何一条失败都说明入库链路破坏了事实层或溯源层。
"""
from __future__ import annotations

import json

import pytest
from steeldig_db.text import json_pointer


def test_row_counts_match_source(conn):
    """行数必须与源资产一一对应（防止漏读/重复）。"""
    expect = {
        "core.paper": 68,
        "core.sample": 638,
        "core.figure": 1041,
        "core.equation": 396,
        "core.evidence_block": 10316,
    }
    for table, n in expect.items():
        got = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        assert got == n, f"{table}: 期望 {n}，实际 {got}"


def test_every_sample_references_resolvable_entities(conn):
    bad = conn.execute("""
        SELECT count(*) FROM core.sample s
        LEFT JOIN core.alloy a ON a.paper_id = s.paper_id AND a.alloy_id = s.alloy_id
        LEFT JOIN core.process p ON p.paper_id = s.paper_id AND p.process_id = s.process_id
        WHERE a.alloy_id IS NULL OR p.process_id IS NULL
    """).fetchone()[0]
    assert bad == 0, f"{bad} 个样品的 alloy/process 外键悬空"


def test_sample_id_follows_composition_rule(conn):
    """discover 的核心身份规则：sample_id = sample_<alloy_stem>__<process_stem>。

    注意前缀：alloy_id 以 alloy_ 开头、process_id 以 proc_ 开头，
    而 sample_id 只保留两者的"词干"。
    """
    bad = conn.execute("""
        SELECT count(*) FROM core.sample
        WHERE sample_id <> 'sample_' || regexp_replace(alloy_id, '^alloy_', '')
                          || '__'  || regexp_replace(process_id, '^proc_', '')
    """).fetchone()[0]
    assert bad == 0, f"{bad} 个样品不符合 sample_id 构成规则"


def test_exactly_one_latest_sample_data(conn):
    bad = conn.execute("""
        SELECT count(*) FROM (
            SELECT paper_id, sample_id, count(*) FILTER (WHERE is_latest) AS n
            FROM core.sample_data GROUP BY 1,2
        ) t WHERE n <> 1
    """).fetchone()[0]
    assert bad == 0, f"{bad} 个样品的 is_latest 数量不为 1"


def test_trace_paths_resolve_in_payload(conn):
    """原则 2 的核心：每条 trace 的 JSON Pointer 必须能在 data 上命中。"""
    rows = conn.execute("""
        SELECT t.paper_id, t.sample_id, t.path, d.payload
        FROM core.sample_trace t
        JOIN core.sample_data d USING (paper_id, sample_id, run_id)
        WHERE d.is_latest
    """).fetchall()
    assert rows, "sample_trace 为空"
    missing = []
    for paper_id, sample_id, path, payload in rows:
        try:
            json_pointer(payload, path)
        except (KeyError, ValueError):
            missing.append((paper_id, sample_id, path))
    assert not missing, f"{len(missing)} 条 trace 路径无法命中，例如 {missing[:3]}"


def test_no_dangling_block_ids(conn):
    """所有 block_ids 都必须指向真实证据块（溯源不能断链）。"""
    bad = conn.execute("""
        WITH refs AS (
            SELECT paper_id, block_id FROM core.sample_trace, unnest(block_ids) AS block_id
            UNION ALL SELECT paper_id, block_id FROM core.figure_observation, unnest(block_ids) AS block_id
            UNION ALL SELECT paper_id, block_id FROM core.figure, unnest(block_ids) AS block_id
            UNION ALL SELECT paper_id, block_id FROM core.alloy, unnest(source_block_ids) AS block_id
            UNION ALL SELECT paper_id, block_id FROM core.process, unnest(source_block_ids) AS block_id
        )
        SELECT count(*) FROM refs r
        LEFT JOIN core.evidence_block e USING (paper_id, block_id)
        WHERE e.block_id IS NULL
    """).fetchone()[0]
    assert bad == 0, f"{bad} 个 block_id 引用悬空"


def test_figure_block_ids_resolved_from_image_groups(conn):
    """图表必须挂上题注/引用块（允许极少数无题注的组图）。"""
    total, with_blocks = conn.execute("""
        SELECT count(*), count(*) FILTER (WHERE cardinality(block_ids) > 0)
        FROM core.figure
    """).fetchone()
    assert with_blocks / total > 0.9, f"仅 {with_blocks}/{total} 个图表挂上了证据块"


# 这些指标的维度是明确的（应力/分数/温度/密度/尺寸），必须完成归一化。
NORMALIZED_METRICS = (
    "yield_strength", "ultimate_tensile_strength", "elongation",
    "reduction_of_area", "density", "average_grain_size", "grain_size",
    "volume_fraction", "temperature",
)


def test_property_value_kind_invariants(conn):
    """数值型必须有值；区间型必须有上下界；定性型不得有归一化值。

    维度未知的指标（如 strain_hardening_rate）不做单位换算，
    其 value_canonical 允许为空——因此按指标白名单断言。
    """
    bad_numeric = conn.execute("""
        SELECT count(*) FROM core.property_value
        WHERE value_kind = 'numeric' AND value_canonical IS NULL
          AND metric = ANY (%s)
    """, (list(NORMALIZED_METRICS),)).fetchone()[0]
    bad_range = conn.execute("""
        SELECT count(*) FROM core.property_value
        WHERE value_kind = 'range' AND metric = ANY (%s)
          AND (value_low_canonical IS NULL OR value_high_canonical IS NULL)
    """, (list(NORMALIZED_METRICS),)).fetchone()[0]
    bad_qual = conn.execute("""
        SELECT count(*) FROM core.property_value
        WHERE value_kind = 'qualitative' AND value_canonical IS NOT NULL
    """).fetchone()[0]
    assert bad_numeric == 0 and bad_range == 0 and bad_qual == 0, (
        f"数值型缺值 {bad_numeric}，区间型缺界 {bad_range}，定性型有值 {bad_qual}")


def test_numeric_coverage_is_reasonable(conn):
    """归一化覆盖率不能太低，否则库退化成文档库。"""
    total, numeric = conn.execute("""
        SELECT count(*), count(*) FILTER (WHERE value_canonical IS NOT NULL)
        FROM core.property_value
    """).fetchone()
    ratio = numeric / total
    assert ratio > 0.5, f"可数值化比例仅 {ratio:.1%}"


def test_key_metric_ranges_are_physical(conn):
    """关键指标必须落在物理合理区间（抓单位换算错误）。"""
    ranges = {
        "yield_strength": (10, 3000),
        "ultimate_tensile_strength": (10, 3000),
        "elongation": (0, 100),
    }
    for metric, (lo, hi) in ranges.items():
        bad = conn.execute("""
            SELECT count(*) FROM core.property_value
            WHERE metric = %s AND value_canonical IS NOT NULL
              AND (value_canonical < %s OR value_canonical > %s)
        """, (metric, lo, hi)).fetchone()[0]
        assert bad == 0, f"{metric} 有 {bad} 条超出物理区间 [{lo},{hi}]"


def test_every_run_has_papers(conn):
    rows = conn.execute("""
        SELECT r.run_id, r.paper_count, count(p.paper_id)
        FROM ops.run r LEFT JOIN core.paper p USING (run_id)
        GROUP BY 1,2
    """).fetchall()
    assert rows
    for run_id, declared, actual in rows:
        if declared:
            assert declared == actual, f"{run_id}: 声明 {declared} 篇，实际 {actual} 篇"


def test_lake_refs_point_to_existing_objects(conn):
    bad = conn.execute("""
        SELECT count(*) FROM lake.object_ref r
        LEFT JOIN lake.object o USING (object_id) WHERE o.object_id IS NULL
    """).fetchone()[0]
    assert bad == 0, f"{bad} 个引用指向不存在的湖对象"


def test_lake_dedup_works(conn):
    """同一字节被多篇引用时只应存一份。"""
    total_refs, total_objects = conn.execute("""
        SELECT (SELECT count(*) FROM lake.object_ref), (SELECT count(*) FROM lake.object)
    """).fetchone()
    assert total_objects <= total_refs
    assert total_refs - total_objects > 0, "没有发生任何去重，可能哈希算错了"


def test_search_documents_cover_all_content_types(conn):
    types = dict(conn.execute(
        "SELECT doc_type, count(*) FROM search.document GROUP BY 1").fetchall())
    for t in ("paper", "wiki", "figure", "equation"):
        assert types.get(t, 0) > 0, f"缺少 {t} 类型检索文档"


def test_no_paper_has_null_title(conn):
    bad = conn.execute("SELECT count(*) FROM core.paper WHERE title IS NULL OR title = ''").fetchone()[0]
    assert bad == 0


def test_api_material_document_is_valid_json(conn):
    pid, sid = conn.execute("SELECT paper_id, sample_id FROM core.sample LIMIT 1").fetchone()
    doc = conn.execute("SELECT api.material_document(%s, %s)", (pid, sid)).fetchone()[0]
    assert doc["material_id"] == f"{pid}:{sid}"
    assert "properties" in doc and "composition" in doc
    json.dumps(doc)  # 必须可序列化
