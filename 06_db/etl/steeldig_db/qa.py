"""质量门禁：入库后的规则校验 + 覆盖率报告。

分两类：
    error —— 破坏可信性（溯源断链、路径失效），阻断发布
    warn  —— 数据脏但可修（合成 id、章节名泄漏）
    info  —— 覆盖率统计，用于驱动 schema 迭代
"""
from __future__ import annotations

import json
from typing import Any

from psycopg import Connection

from .text import json_pointer

# ---------------------------------------------------------------------------
# 运行时校验（依赖 payload，用 Python 做）
# ---------------------------------------------------------------------------

def check_trace_paths(conn: Connection, ingest_id: int) -> list[dict]:
    """sample_trace.path 必须能在 sample_data.payload 上命中。"""
    issues: list[dict] = []
    rows = conn.execute("""
        SELECT t.paper_id, t.sample_id, t.path, d.payload
        FROM core.sample_trace t
        JOIN core.sample_data d
          ON d.paper_id = t.paper_id AND d.sample_id = t.sample_id AND d.run_id = t.run_id
        WHERE d.is_latest
    """).fetchall()
    missing = 0
    for paper_id, sample_id, path, payload in rows:
        try:
            json_pointer(payload, path)
        except (KeyError, ValueError):
            missing += 1
            if missing <= 200:
                issues.append({
                    "rule_code": "TRACE_PATH_MISSING", "severity": "error",
                    "paper_id": paper_id, "subject": f"{sample_id}{path}",
                    "message": "trace 路径在 data 中不存在",
                    "detail": {"sample_id": sample_id, "path": path},
                })
    if missing:
        conn.execute("UPDATE core.paper SET qa_flags = array_append(qa_flags, 'TRACE_PATH_MISSING')"
                     " WHERE paper_id IN (SELECT DISTINCT paper_id FROM core.sample_trace)"
                     " AND NOT ('TRACE_PATH_MISSING' = ANY (qa_flags))")
    return issues


def check_dangling_blocks(conn: Connection) -> list[dict]:
    """所有 block_ids 引用都必须命中 evidence_block。"""
    sql = """
    WITH refs AS (
        SELECT paper_id, block_id FROM core.sample_trace, unnest(block_ids) AS block_id
        UNION ALL SELECT paper_id, block_id FROM core.figure_observation, unnest(block_ids) AS block_id
        UNION ALL SELECT paper_id, block_id FROM core.figure, unnest(block_ids) AS block_id
        UNION ALL SELECT paper_id, block_id FROM core.alloy, unnest(source_block_ids) AS block_id
        UNION ALL SELECT paper_id, block_id FROM core.process, unnest(source_block_ids) AS block_id
    )
    SELECT r.paper_id, r.block_id, count(*)
    FROM refs r
    LEFT JOIN core.evidence_block e USING (paper_id, block_id)
    WHERE e.block_id IS NULL
    GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 100
    """
    return [{"rule_code": "BLOCK_ID_DANGLING", "severity": "error",
             "paper_id": p, "subject": b, "message": "引用了不存在的证据块",
             "detail": {"refs": n}}
            for p, b, n in conn.execute(sql).fetchall()]


def check_duplicate_titles(conn: Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT a.paper_id, b.paper_id, similarity(a.title, b.title)
        FROM core.paper a JOIN core.paper b
          ON a.paper_id < b.paper_id AND similarity(a.title, b.title) > 0.92
        ORDER BY 3 DESC LIMIT 20
    """).fetchall()
    return [{"rule_code": "DUPLICATE_TITLE", "severity": "warn", "paper_id": p,
             "subject": q, "message": f"标题相似度 {s:.2f}",
             "detail": {"other": q, "similarity": round(s, 3)}} for p, q, s in rows]


def persist(conn: Connection, ingest_id: int, issues: list[dict]) -> int:
    if not issues:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ops.qa_issue (ingest_id, rule_code, severity, paper_id, subject, message, detail)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (rule_code, paper_id, subject) DO UPDATE SET"
            " ingest_id = EXCLUDED.ingest_id, severity = EXCLUDED.severity,"
            " message = EXCLUDED.message, detail = EXCLUDED.detail, created_at = now()",
            [(ingest_id, i["rule_code"], i["severity"], i.get("paper_id"),
              i.get("subject"), i["message"],
              json.dumps(i.get("detail") or {}, ensure_ascii=False)) for i in issues],
        )
    return len(issues)


# ---------------------------------------------------------------------------
# 覆盖率与质量报告
# ---------------------------------------------------------------------------

def report(conn: Connection) -> dict[str, Any]:
    def one(sql: str, params=()):
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None

    tables = {}
    for schema, table in conn.execute("""
        SELECT n.nspname, c.relname FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN ('core','lake','search','ops','canon') AND c.relkind = 'r'
        ORDER BY 1,2
    """).fetchall():
        tables[f"{schema}.{table}"] = one(
            f'SELECT count(*) FROM "{schema}"."{table}"')

    prop = conn.execute("""
        SELECT section, count(*) AS n,
               count(*) FILTER (WHERE value_canonical IS NOT NULL) AS numeric,
               count(*) FILTER (WHERE value_kind = 'range') AS ranges,
               count(*) FILTER (WHERE value_kind = 'qualitative') AS qualitative
        FROM core.property_value GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()

    metrics = conn.execute("""
        SELECT metric, count(*) AS n, count(*) FILTER (WHERE value_canonical IS NOT NULL) AS usable,
               min(value_canonical), max(value_canonical), max(unit_canonical)
        FROM core.property_value
        WHERE metric IN ('yield_strength','ultimate_tensile_strength','elongation',
                         'reduction_of_area','hardness','average_grain_size')
        GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()

    resolutions = conn.execute("""
        SELECT method, count(*) FROM ops.block_id_resolution GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()

    issues = conn.execute("""
        SELECT rule_code, severity, count(*) FROM ops.qa_issue GROUP BY 1,2 ORDER BY 3 DESC
    """).fetchall()

    families = conn.execute("""
        SELECT family_key, count(*) FROM core.alloy GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()

    return {
        "tables": tables,
        "property_sections": [
            {"section": s, "rows": n, "numeric": nu, "ranges": r, "qualitative": q}
            for s, n, nu, r, q in prop
        ],
        "key_metrics": [
            {"metric": m, "rows": n, "numeric": u, "min": float(mn) if mn is not None else None,
             "max": float(mx) if mx is not None else None, "unit": unit}
            for m, n, u, mn, mx, unit in metrics
        ],
        "block_id_resolution": [{"method": m, "n": n} for m, n in resolutions],
        "issues": [{"rule": r, "severity": s, "n": n} for r, s, n in issues],
        "families": [{"family": f, "n": n} for f, n in families],
    }


def markdown_report(rep: dict[str, Any], ingest_id: int | None = None) -> str:
    lines = ["# 入库质量与覆盖率报告", ""]
    if ingest_id:
        lines.append(f"- ingest_id: `{ingest_id}`")
    lines += ["", "## 表行数", "", "| 表 | 行数 |", "|---|---:|"]
    for k, v in sorted(rep["tables"].items()):
        lines.append(f"| `{k}` | {v:,} |")

    lines += ["", "## 属性量（按分区）", "",
              "| 分区 | 总行 | 可数值化 | 区间 | 定性 |", "|---|---:|---:|---:|---:|"]
    for r in rep["property_sections"]:
        lines.append(f"| {r['section']} | {r['rows']:,} | {r['numeric']:,} | {r['ranges']:,} | {r['qualitative']:,} |")

    lines += ["", "## 关键指标分布（已单位归一）", "",
              "| 指标 | 行数 | 可数值化 | 最小 | 最大 | 单位 |", "|---|---:|---:|---:|---:|---|"]
    for r in rep["key_metrics"]:
        lines.append(f"| {r['metric']} | {r['rows']:,} | {r['numeric']:,} | {r['min']} | {r['max']} | {r['unit']} |")

    lines += ["", "## block_id 对齐", "", "| 方法 | 数量 |", "|---|---:|"]
    for r in rep["block_id_resolution"]:
        lines.append(f"| {r['method']} | {r['n']:,} |")

    lines += ["", "## 质量问题", "", "| 规则 | 级别 | 数量 |", "|---|---|---:|"]
    for r in rep["issues"]:
        lines.append(f"| {r['rule']} | {r['severity']} | {r['n']:,} |")

    lines += ["", "## 合金族分布", "", "| 合金族 | 合金数 |", "|---|---:|"]
    for r in rep["families"]:
        lines.append(f"| {r['family']} | {r['n']:,} |")
    return "\n".join(lines) + "\n"
