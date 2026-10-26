"""从 PostgreSQL 系统目录生成数据字典与 ER 图（文档与实现永不脱节）。

    python ops/gen_docs.py --out ../07_docs
"""
from __future__ import annotations

import argparse
import collections
import textwrap
from pathlib import Path

from steeldig_db.config import DB_HOME
from steeldig_db.db import connect

SCHEMA_TITLES = {
    "ops": "治理层 ops",
    "lake": "资产湖 lake",
    "core": "事实层 core",
    "canon": "规范化层 canon",
    "curate": "校订层 curate",
    "search": "检索层 search",
    "api": "消费层 api（视图/函数）",
}


def tables(conn):
    return conn.execute("""
        SELECT n.nspname, c.relname, obj_description(c.oid) AS comment
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN ('ops','lake','core','canon','curate','search','api')
          AND c.relkind IN ('r','v')
        ORDER BY 1, 2
    """).fetchall()


def columns(conn, schema, table):
    return conn.execute("""
        SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS type,
               a.attnotnull, col_description(a.attrelid, a.attnum) AS comment,
               pg_get_expr(d.adbin, d.adrelid) AS default_expr,
               a.attgenerated
        FROM pg_attribute a
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE a.attrelid = (%s || '.' || %s)::regclass
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum
    """, (schema, table)).fetchall()


def primary_keys(conn, schema, table):
    rows = conn.execute("""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey)
        WHERE i.indrelid = (%s || '.' || %s)::regclass AND i.indisprimary
        ORDER BY array_position(i.indkey, a.attnum)
    """, (schema, table)).fetchall()
    return [r[0] for r in rows]


def foreign_keys(conn):
    return conn.execute("""
        SELECT n.nspname AS schema, c.relname AS table,
               a.attname AS col,
               fn.nspname AS ref_schema, fc.relname AS ref_table, fa.attname AS ref_col
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class fc ON fc.oid = con.confrelid
        JOIN pg_namespace fn ON fn.oid = fc.relnamespace
        JOIN LATERAL unnest(con.conkey) WITH ORDINALITY k(attnum, ord) ON true
        JOIN LATERAL unnest(con.confkey) WITH ORDINALITY fk(attnum, ord) ON fk.ord = k.ord
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
        JOIN pg_attribute fa ON fa.attrelid = fc.oid AND fa.attnum = fk.attnum
        WHERE con.contype = 'f' AND n.nspname IN ('ops','lake','core','canon','curate','search')
        ORDER BY 1,2,3
    """).fetchall()


def row_counts(conn):
    out = {}
    for schema, table, _ in tables(conn):
        kind = conn.execute(
            "SELECT relkind FROM pg_class WHERE oid = (%s || '.' || %s)::regclass",
            (schema, table)).fetchone()[0]
        if kind == "r":
            out[f"{schema}.{table}"] = conn.execute(
                f'SELECT count(*) FROM "{schema}"."{table}"').fetchone()[0]
    return out


def data_dictionary(conn) -> str:
    counts = row_counts(conn)
    lines = ["# 数据字典", "",
             "> 本文件由 `06_db/ops/gen_docs.py` 从 `information_schema` 自动生成，",
             "> 与数据库实现保持一致。修改表结构后请重新生成。", ""]

    groups = collections.defaultdict(list)
    for schema, table, comment in tables(conn):
        groups[schema].append((table, comment))

    for schema in ["ops", "lake", "core", "canon", "curate", "search", "api"]:
        if not groups[schema]:
            continue
        lines += [f"## {SCHEMA_TITLES.get(schema, schema)}", ""]
        for table, comment in groups[schema]:
            full = f"{schema}.{table}"
            n = counts.get(full)
            title = f"### `{full}`" + (f" — {n:,} 行" if n is not None else "")
            lines += [title, ""]
            if comment:
                lines += [f"> {comment}", ""]
            pk = primary_keys(conn, schema, table)
            lines += ["| 列 | 类型 | 可空 | 主键 | 默认 | 说明 |", "|---|---|:---:|:---:|---|---|"]
            for name, typ, notnull, ccol, default, gen in columns(conn, schema, table):
                note = (ccol or "").replace("\n", " ")
                lines.append(
                    f"| `{name}` | `{typ}` | {'否' if notnull else '是'} | "
                    f"{'✔' if name in pk else ''} | {('`'+default+'`') if default else ''} | {note} |")
            lines.append("")
    return "\n".join(lines)


def er_diagram(conn) -> str:
    fks = foreign_keys(conn)
    lines = ["# 实体关系（ER）", "",
             "```mermaid", "erDiagram"]
    rels = collections.OrderedDict()
    for schema, table, col, rs, rt, rc in fks:
        key = (f"{schema}.{table}", f"{rs}.{rt}")
        rels.setdefault(key, []).append((col, rc))
    for (src, dst), cols in rels.items():
        label = ", ".join(f"{c}→{r}" for c, r in cols[:3])
        if len(cols) > 3:
            label += f" (+{len(cols)-3})"
        lines.append(f'    {src.replace(".","_")} }}o--|| {dst.replace(".","_")} : "{label}"')
    lines += ["```", "", "## 分层说明", "",
              "- `lake.*` 只有目录，真实字节在对象存储；`core.*` 的事实行通过 "
              "`lake.object_ref` 回指原始 JSON。",
              "- `core.sample` 是枢纽：合金 × 工艺 = 样品，性能/相/溯源/词条都挂在它下面。",
              "- `core.sample_data` 与 `core.sample_trace` 通过 `(paper_id, sample_id, path)` 关联，",
              "  这是「科学事实」与「证据溯源」的分离点。",
              "- `search.document` 通过 `doc_type + paper_id + ref_id` 回指具体实体。",
              ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DB_HOME.parent / "07_docs")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        (args.out / "02_DATA_DICTIONARY.md").write_text(data_dictionary(conn), encoding="utf-8")
        (args.out / "01_SCHEMA.md").write_text(er_diagram(conn), encoding="utf-8")
    print(f"已生成 {args.out}/01_SCHEMA.md 与 02_DATA_DICTIONARY.md")


if __name__ == "__main__":
    main()
