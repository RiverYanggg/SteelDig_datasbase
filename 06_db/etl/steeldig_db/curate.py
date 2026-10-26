"""校订层：人工增删改的**唯一合法入口**。

为什么需要这一层
----------------
事实层 `core.*` 是 ETL 从资产湖重放的产物：入库一篇论文 = `DELETE` 本篇 + 重新 `COPY`。
如果人直接 `UPDATE core.property_value`，下一次重跑就把修改冲掉了（实测确认）。

因此写入走三层：

    湖（不可变） → core（可重建） → curate（人写，持久，可审计）

`curate.change` 只记录"意图 + 前后值"，真正落库由 `apply_changes()` 统一执行；
每次 ingest 结束后自动重放一遍，所以人工修改既持久，又能在湖更新后继续生效。

权限模型：白名单。只有登记在 `REGISTRY` 里的表/列才能改，
避免 API 变成任意 SQL 执行器。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


# ---------------------------------------------------------------------------
# 可写白名单
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Entity:
    table: str
    key: tuple[str, ...]
    updatable: tuple[str, ...] = ()
    creatable: bool = False
    deletable: bool = False
    required_on_create: tuple[str, ...] = ()

    @property
    def key_doc(self) -> str:
        return ", ".join(self.key)


REGISTRY: dict[str, Entity] = {
    "core.paper": Entity(
        table="core.paper", key=("paper_id",),
        updatable=("title", "doi", "journal", "year", "research_type", "abstract",
                   "keywords", "authors", "qa_flags"),
    ),
    "core.alloy": Entity(
        table="core.alloy", key=("paper_id", "alloy_id"),
        updatable=("name", "base_element", "family_key", "description", "notes",
                   "formula", "chemsys", "aliases"),
        creatable=True,
        required_on_create=("paper_id", "alloy_id", "payload"),
    ),
    "core.process": Entity(
        table="core.process", key=("paper_id", "process_id"),
        updatable=("name", "state_label", "description", "notes", "aliases"),
    ),
    "core.sample": Entity(
        table="core.sample", key=("paper_id", "sample_id"),
        updatable=("label", "aliases"),
        creatable=True,
        deletable=True,
        required_on_create=("paper_id", "sample_id", "alloy_id", "process_id"),
    ),
    "core.property_value": Entity(
        table="core.property_value", key=("paper_id", "sample_id", "run_id", "path"),
        updatable=("value_raw", "value_kind", "value_canonical", "value_low_canonical",
                   "value_high_canonical", "value_unit", "unit_canonical",
                   "uncertainty_raw", "block_status"),
        deletable=True,
    ),
    "core.phase": Entity(
        table="core.phase", key=("paper_id", "sample_id", "microstructure_id", "idx"),
        updatable=("phase_name", "phase_key", "volume_fraction_pct", "grain_size_um",
                   "morphology", "crystal_structure"),
    ),
    "core.figure": Entity(
        table="core.figure", key=("paper_id", "figure_id"),
        updatable=("label", "description", "image_type", "confidence"),
    ),
    "core.figure_observation": Entity(
        table="core.figure_observation", key=("paper_id", "figure_id", "idx"),
        updatable=("observation", "source", "block_status"),
        deletable=True,
    ),
    "core.equation": Entity(
        table="core.equation", key=("paper_id", "equation_id"),
        updatable=("purpose", "applicability", "latex", "equation_number"),
    ),
    "core.characterization": Entity(
        table="core.characterization", key=("paper_id", "sample_id", "idx"),
        updatable=("technique", "technique_key", "instrument", "conditions",
                   "purpose", "key_findings"),
    ),
    "core.unmapped_finding": Entity(
        table="core.unmapped_finding", key=("paper_id", "sample_id", "idx"),
        updatable=("text",), deletable=True,
    ),
}


def _q(conn: Connection, sql: str, params=()) -> list[dict]:
    """以 dict 形式查询（ETL 默认连接返回 tuple，这里显式指定行工厂）。"""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


class CurationError(ValueError):
    """参数非法（表不在白名单、字段不可写、键缺失……）。"""


# ---------------------------------------------------------------------------
# 校验
# ---------------------------------------------------------------------------
def entity_for(table: str) -> Entity:
    ent = REGISTRY.get(table)
    if ent is None:
        raise CurationError(
            f"{table} 不在可写白名单内；允许的表：{', '.join(sorted(REGISTRY))}")
    return ent


def validate(op: str, table: str, target_key: dict, field_name: str | None,
             new_value: Any) -> Entity:
    ent = entity_for(table)
    if op not in ("update", "create", "delete"):
        raise CurationError("op 只能是 update / create / delete")

    if op == "create":
        if not ent.creatable:
            raise CurationError(f"{table} 不支持 create（新增数据请走 ETL 入库）")
        missing = [c for c in ent.required_on_create if c not in target_key]
        if missing:
            raise CurationError(f"create 缺少必填字段：{', '.join(missing)}")
        return ent

    missing = [k for k in ent.key if k not in target_key]
    if missing:
        raise CurationError(f"target_key 缺少主键字段：{', '.join(missing)}（需要 {ent.key_doc}）")

    if op == "delete" and not ent.deletable:
        raise CurationError(f"{table} 不支持 delete")
    if op == "update":
        if not field_name:
            raise CurationError("update 必须指定 field")
        if field_name not in ent.updatable:
            raise CurationError(
                f"{table}.{field_name} 不可写；允许的列：{', '.join(ent.updatable)}")
    return ent


# ---------------------------------------------------------------------------
# 记录一条校订
# ---------------------------------------------------------------------------
def _row_exists(conn: Connection, ent: Entity, key: dict) -> dict | None:
    where = " AND ".join(f"{k} = %s" for k in ent.key)
    rows = _q(conn, f"SELECT * FROM {ent.table} WHERE {where}",
              tuple(key[k] for k in ent.key))
    return rows[0] if rows else None


def record(conn: Connection, *, op: str, table: str, target_key: dict,
           field_name: str | None = None, new_value: Any = None,
           note: str | None = None, author: str = "anonymous",
           source: str = "api", apply_now: bool = True) -> int:
    """写入一条校订并（可选）立即应用。返回 change_id。"""
    ent = validate(op, table, target_key, field_name, new_value)

    old = None
    if op != "create":
        row = _row_exists(conn, ent, target_key)
        if row is None:
            raise CurationError(
                f"{table} 中不存在目标行：{json.dumps(target_key, ensure_ascii=False)}")
        old = row.get(field_name) if field_name else None

    change_id = _q(conn, """
        INSERT INTO curate.change (op, target_table, target_key, field, old_value,
                                   new_value, note, author, source, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'applied')
        RETURNING change_id
    """, (op, table, json.dumps(target_key, ensure_ascii=False), field_name,
          json.dumps(old, ensure_ascii=False, default=str) if old is not None else None,
          json.dumps(new_value, ensure_ascii=False, default=str),
          note, author, source))[0]["change_id"]

    if apply_now:
        apply_one(conn, change_id)
    return change_id


# ---------------------------------------------------------------------------
# 应用 / 撤销
# ---------------------------------------------------------------------------
_TYPE_CACHE: dict[str, dict[str, tuple[str, str]]] = {}


def _column_types(conn: Connection, table: str) -> dict[str, tuple[str, str]]:
    if table not in _TYPE_CACHE:
        schema, name = table.split(".", 1)
        rows = _q(conn, """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema=%s AND table_name=%s
        """, (schema, name))
        _TYPE_CACHE[table] = {r["column_name"]: (r["data_type"], r["udt_name"]) for r in rows}
    return _TYPE_CACHE[table]


def _adapt(conn: Connection, table: str, column: str, value: Any) -> Any:
    """按目标列类型转换：jsonb 用 JSON 字符串，数组直接用 Python list。"""
    data_type, _udt = _column_types(conn, table).get(column, ("text", "text"))
    if data_type in ("json", "jsonb"):
        return json.dumps(value, ensure_ascii=False)
    if data_type == "ARRAY":
        return list(value) if isinstance(value, (list, tuple)) else [value]
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _ensure_sample_parents(conn: Connection, row: dict) -> None:
    """新增样品前，保证 alloy / process 存在（不存在则补 stub，保持外键完整）。"""
    paper_id = row["paper_id"]
    for table, id_col, id_val in (
        ("core.alloy", "alloy_id", row.get("alloy_id")),
        ("core.process", "process_id", row.get("process_id")),
    ):
        if not id_val:
            continue
        exists = conn.execute(
            f"SELECT 1 FROM {table} WHERE paper_id=%s AND {id_col}=%s",
            (paper_id, id_val)).fetchone()
        if exists:
            continue
        if table == "core.alloy":
            conn.execute("""
                INSERT INTO core.alloy (paper_id, alloy_id, name, is_stub, payload)
                VALUES (%s,%s,%s,true,'{}'::jsonb) ON CONFLICT DO NOTHING
            """, (paper_id, id_val, f"人工补建：{id_val}"))
        else:
            conn.execute("""
                INSERT INTO core.process (paper_id, process_id, name, is_stub, payload)
                VALUES (%s,%s,%s,true,'{}'::jsonb) ON CONFLICT DO NOTHING
            """, (paper_id, id_val, f"人工补建：{id_val}"))


def _apply(conn: Connection, ch: dict) -> None:
    ent = entity_for(ch["target_table"])
    key = ch["target_key"]
    op = ch["op"]

    if op == "update":
        where = " AND ".join(f"{k} = %s" for k in ent.key)
        conn.execute(
            f"UPDATE {ent.table} SET {ch['field']} = %s WHERE {where}",
            (_adapt(conn, ent.table, ch["field"], ch["new_value"]),
             *(key[k] for k in ent.key)))
    elif op == "delete":
        where = " AND ".join(f"{k} = %s" for k in ent.key)
        conn.execute(f"DELETE FROM {ent.table} WHERE {where}",
                     tuple(key[k] for k in ent.key))
    elif op == "create":
        row = dict(ch["new_value"])
        # 事实表普遍有 payload NOT NULL：人工新增的行没有产物原文，给空对象
        row.setdefault("payload", {})
        ch = {**ch, "new_value": row}
        if ent.table == "core.sample":
            _ensure_sample_parents(conn, row)
        cols = list(ch["new_value"].keys())
        allowed = set(ent.key) | set(ent.updatable) | set(ent.required_on_create) | {"payload"}
        bad = [c for c in cols if c not in allowed]
        if bad:
            raise CurationError(f"create 不允许的列：{', '.join(bad)}")
        placeholders = ", ".join(["%s"] * len(cols))
        conn.execute(
            f"INSERT INTO {ent.table} ({', '.join(cols)}) VALUES ({placeholders})"
            " ON CONFLICT DO NOTHING",
            tuple(_adapt(conn, ent.table, c, ch["new_value"][c]) for c in cols))


def apply_one(conn: Connection, change_id: int) -> bool:
    rows = _q(conn, "SELECT * FROM curate.change WHERE change_id = %s", (change_id,))
    if not rows:
        raise CurationError(f"change {change_id} 不存在")
    ch = rows[0]
    conn.execute("SAVEPOINT curate_apply")
    try:
        _apply(conn, ch)
        conn.execute("RELEASE SAVEPOINT curate_apply")
        conn.execute("UPDATE curate.change SET status='applied', applied_at=now(),"
                     " error=NULL WHERE change_id=%s", (change_id,))
        return True
    except Exception as exc:  # noqa: BLE001
        conn.execute("ROLLBACK TO SAVEPOINT curate_apply")
        conn.execute("UPDATE curate.change SET status='failed', error=%s"
                     " WHERE change_id=%s", (f"{type(exc).__name__}: {exc}", change_id))
        return False


def apply_changes(conn: Connection) -> dict[str, int]:
    """重放全部生效校订。ingest 结束后自动调用。"""
    rows = _q(conn, "SELECT * FROM curate.change WHERE status = 'applied' ORDER BY change_id")
    ok = failed = 0
    for ch in rows:
        conn.execute("SAVEPOINT curate_batch")
        try:
            _apply(conn, ch)
            conn.execute("RELEASE SAVEPOINT curate_batch")
            conn.execute("UPDATE curate.change SET applied_at = now(), error = NULL"
                         " WHERE change_id = %s", (ch["change_id"],))
            ok += 1
        except Exception as exc:  # noqa: BLE001
            conn.execute("ROLLBACK TO SAVEPOINT curate_batch")
            conn.execute("UPDATE curate.change SET status='failed', error=%s"
                         " WHERE change_id=%s", (f"{type(exc).__name__}: {exc}",
                                                 ch["change_id"]))
            failed += 1
    return {"applied": ok, "failed": failed}


def revert(conn: Connection, change_id: int) -> bool:
    """撤销一条校订：update 写回旧值；create 删除新建行；delete 需重新入库。"""
    found = _q(conn, "SELECT * FROM curate.change WHERE change_id = %s", (change_id,))
    if not found or found[0]["status"] == "reverted":
        return False
    ch = found[0]
    ent = entity_for(ch["target_table"])
    key = ch["target_key"]

    if ch["op"] == "update":
        where = " AND ".join(f"{k} = %s" for k in ent.key)
        conn.execute(f"UPDATE {ent.table} SET {ch['field']} = %s WHERE {where}",
                     (ch["old_value"], *(key[k] for k in ent.key)))
    elif ch["op"] == "create":
        where = " AND ".join(f"{k} = %s" for k in ent.key)
        conn.execute(f"DELETE FROM {ent.table} WHERE {where}",
                     tuple(key[k] for k in ent.key))
    # delete 的撤销需要从湖重建该行，交由调用方重新 ingest 该篇

    conn.execute("UPDATE curate.change SET status='reverted', applied_at=now()"
                 " WHERE change_id=%s", (change_id,))
    return True


def stats(conn: Connection) -> dict:
    row = _q(conn, """
        SELECT count(*) AS total,
               count(*) FILTER (WHERE status='applied')  AS applied,
               count(*) FILTER (WHERE status='reverted') AS reverted,
               count(*) FILTER (WHERE status='failed')   AS failed,
               count(DISTINCT target_table) AS tables,
               count(DISTINCT target_key->>'paper_id') AS papers
        FROM curate.change
    """)[0]
    return row
