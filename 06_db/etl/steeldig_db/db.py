"""连接、迁移与批量装载工具。"""
from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Sequence

import psycopg
from psycopg import Connection

from .config import DB_HOME, settings

MIGRATIONS = DB_HOME / "migrations"

BOOTSTRAP = """
CREATE SCHEMA IF NOT EXISTS ops;
CREATE TABLE IF NOT EXISTS ops.schema_migration (
    filename    text PRIMARY KEY,
    checksum    text NOT NULL,
    applied_at  timestamptz NOT NULL DEFAULT now(),
    duration_ms integer
);
"""


@contextmanager
def connect(dsn: str | None = None, autocommit: bool = False):
    conn = psycopg.connect(dsn or settings.dsn, autocommit=autocommit,
                           application_name="steeldig-etl")
    try:
        yield conn
    finally:
        conn.close()


def _checksum(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def migrate(verbose: bool = True) -> list[str]:
    """按文件名顺序执行 migrations/*.sql，已执行过的跳过（记录 checksum 以便发现漂移）。"""
    applied: list[str] = []
    with connect(autocommit=True) as conn:
        conn.execute(BOOTSTRAP)
        done = dict(conn.execute("SELECT filename, checksum FROM ops.schema_migration").fetchall())
        for path in sorted(MIGRATIONS.glob("*.sql")):
            cs = _checksum(path)
            if path.name in done:
                if done[path.name] != cs:
                    raise RuntimeError(
                        f"迁移文件已被修改：{path.name}（库内 {done[path.name]} ≠ 当前 {cs}）。"
                        " 请新增迁移文件，不要改动已执行的历史迁移。"
                    )
                continue
            t0 = time.time()
            conn.execute(path.read_text(encoding="utf-8"))
            ms = int((time.time() - t0) * 1000)
            conn.execute(
                "INSERT INTO ops.schema_migration (filename, checksum, duration_ms) VALUES (%s,%s,%s)",
                (path.name, cs, ms),
            )
            applied.append(path.name)
            if verbose:
                print(f"  ✓ {path.name}  ({ms} ms)")
    return applied


def copy_rows(conn: Connection, table: str, columns: Sequence[str],
              rows: Iterable[Sequence], *, page_size: int = 2000) -> int:
    """用 COPY 批量写入；rows 为可迭代的元组序列。空列表直接返回 0。"""
    n = 0
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(row)
                n += 1
    return n


def scalar(conn: Connection, sql: str, params: Sequence = ()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def table_counts(conn: Connection, schema: str = "core") -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT c.relname, c.reltuples::bigint
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relkind = 'r'
        ORDER BY c.relname
        """,
        (schema,),
    ).fetchall()
    return {name: int(est) for name, est in rows}
