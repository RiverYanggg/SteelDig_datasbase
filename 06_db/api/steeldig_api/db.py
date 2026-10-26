"""共享连接池（API 与 Web 页面共用）。"""
from __future__ import annotations

import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DSN = os.environ.get(
    "STEELDIG_DSN", "postgresql://steeldig:steeldig_dev_pw@127.0.0.1:5435/steeldig")

pool: ConnectionPool | None = None


def init(min_size: int = 1, max_size: int = 8) -> None:
    global pool
    if pool is None:
        pool = ConnectionPool(DSN, min_size=min_size, max_size=max_size, open=True,
                              kwargs={"row_factory": dict_row,
                                      "application_name": "steeldig-api"})


def close() -> None:
    global pool
    if pool is not None:
        pool.close()
        pool = None


def all(sql: str, params=()) -> list[dict]:
    assert pool is not None, "连接池未初始化"
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


def one(sql: str, params=()) -> dict | None:
    assert pool is not None
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchone()
