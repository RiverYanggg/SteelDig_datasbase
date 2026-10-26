"""校订层（增删改）测试。

验证的核心命题：**人工修改不会被重跑入库覆盖**。
这是本库写入模型的关键约束——事实层可重建，人的修正必须持久。
"""
from __future__ import annotations

import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from steeldig_db import curate
from steeldig_db.config import DB_HOME
from steeldig_db.db import connect

from steeldig_api.main import app

PAPER = "10.1002_srin.202100643"
SAMPLE = "sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac"
PATH_YS = "$.properties[0].mechanical.tensile_properties.yield_strength[0]"
RUN = "run_0915_pro"


def reingest(paper_id: str) -> None:
    """从湖重放一篇论文（会先删除本篇全部事实）。"""
    subprocess.run(
        [sys.executable, "-m", "steeldig_db", "ingest", "--papers", paper_id],
        cwd=str(DB_HOME / "etl"), check=True, capture_output=True, timeout=180)


def cleanup(change_ids: list[int], paper_id: str) -> None:
    with connect() as c:
        c.execute("DELETE FROM curate.change WHERE change_id = ANY (%s)", (change_ids,))
        c.commit()
    reingest(paper_id)


def ys_value(paper_id: str, sample_id: str, path: str):
    with connect() as c:
        row = c.execute("""
            SELECT value_canonical FROM core.property_value
            WHERE paper_id=%s AND sample_id=%s AND path=%s
        """, (paper_id, sample_id, path)).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# 校订原语
# ---------------------------------------------------------------------------
def test_update_survives_reingest():
    """核心断言：改完再重跑，值仍然是改后的。"""
    original = ys_value(PAPER, SAMPLE, PATH_YS)
    assert original is not None

    with connect() as c:
        cid = curate.record(
            c, op="update", table="core.property_value",
            target_key={"paper_id": PAPER, "sample_id": SAMPLE, "run_id": RUN, "path": PATH_YS},
            field_name="value_canonical", new_value=999, note="pytest", author="pytest")
        c.commit()

    try:
        assert float(ys_value(PAPER, SAMPLE, PATH_YS)) == 999
        reingest(PAPER)
        assert float(ys_value(PAPER, SAMPLE, PATH_YS)) == 999, "重跑后人工修改被覆盖了"
    finally:
        with connect() as c:
            curate.revert(c, cid)
            c.execute("DELETE FROM curate.change WHERE change_id=%s", (cid,))
            c.commit()
        reingest(PAPER)

    assert float(ys_value(PAPER, SAMPLE, PATH_YS)) == float(original)


def test_revert_restores_old_value():
    original = float(ys_value(PAPER, SAMPLE, PATH_YS))
    with connect() as c:
        cid = curate.record(
            c, op="update", table="core.sample",
            target_key={"paper_id": PAPER, "sample_id": SAMPLE},
            field_name="label", new_value="临时标签", note="pytest", author="pytest")
        c.commit()
        assert c.execute("SELECT label FROM core.sample WHERE sample_id=%s",
                         (SAMPLE,)).fetchone()[0] == "临时标签"
        assert curate.revert(c, cid) is True
        c.commit()
        c.execute("DELETE FROM curate.change WHERE change_id=%s", (cid,))
        c.commit()
    assert ys_value(PAPER, SAMPLE, PATH_YS) == original


def test_create_sample_and_persist():
    sid = "sample_pytest-temp__as-cast"
    with connect() as c:
        cid = curate.record(
            c, op="create", table="core.sample",
            target_key={"paper_id": PAPER, "sample_id": sid,
                        "alloy_id": "alloy_pytest-temp", "process_id": "proc_as-cast"},
            new_value={"paper_id": PAPER, "sample_id": sid,
                       "alloy_id": "alloy_pytest-temp", "process_id": "proc_as-cast",
                       "label": "pytest 新增", "aliases": []},
            note="pytest", author="pytest")
        c.commit()
    try:
        with connect() as chk:
            assert chk.execute("SELECT count(*) FROM core.sample WHERE sample_id=%s",
                               (sid,)).fetchone()[0] == 1
        reingest(PAPER)
        with connect() as c:
            assert c.execute("SELECT count(*) FROM core.sample WHERE sample_id=%s",
                             (sid,)).fetchone()[0] == 1, "新增的样品在重跑后消失了"
    finally:
        cleanup([cid], PAPER)


def test_delete_property_and_persist():
    path = "$.properties[0].mechanical.tensile_properties.elongation[0]"
    with connect() as c:
        exists = c.execute("""SELECT count(*) FROM core.property_value
                              WHERE paper_id=%s AND sample_id=%s AND path=%s""",
                           (PAPER, SAMPLE, path)).fetchone()[0]
    if not exists:
        pytest.skip("该样品没有可删的 elongation 行")

    with connect() as c:
        cid = curate.record(
            c, op="delete", table="core.property_value",
            target_key={"paper_id": PAPER, "sample_id": SAMPLE, "run_id": RUN, "path": path},
            note="pytest 删除", author="pytest")
        c.commit()
    try:
        assert ys_value(PAPER, SAMPLE, path) is None
        reingest(PAPER)
        assert ys_value(PAPER, SAMPLE, path) is None, "删除在重跑后失效了"
    finally:
        cleanup([cid], PAPER)


# ---------------------------------------------------------------------------
# 白名单校验
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("kwargs,msg", [
    (dict(op="update", table="core.paper", target_key={"paper_id": PAPER},
          field_name="created_at", new_value="2000-01-01"), "不可写"),
    (dict(op="update", table="core.sample", target_key={"paper_id": PAPER, "sample_id": SAMPLE},
          field_name="sample_id", new_value="x"), "不可写"),
    (dict(op="update", table="curate.change", target_key={"change_id": 1},
          field_name="note", new_value="x"), "白名单"),
    (dict(op="delete", table="core.paper", target_key={"paper_id": PAPER},
          field_name=None, new_value=None), "不支持 delete"),
])
def test_registry_rejects(kwargs, msg):
    with connect() as c:
        with pytest.raises(curate.CurationError):
            curate.record(c, **kwargs, author="pytest")


def test_missing_row_rejected():
    with connect() as c:
        with pytest.raises(curate.CurationError):
            curate.record(c, op="update", table="core.sample",
                          target_key={"paper_id": PAPER, "sample_id": "不存在的样品"},
                          field_name="label", new_value="x", author="pytest")


# ---------------------------------------------------------------------------
# REST 接口
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_curate_schema_lists_registry(client):
    items = client.get("/api/curate/schema").json()["items"]
    tables = {i["table"] for i in items}
    assert "core.sample" in tables and "core.property_value" in tables


def test_api_rejects_unknown_table(client):
    r = client.post("/api/curate/changes", json={
        "op": "update", "target_table": "public.pg_class",
        "target_key": {"x": 1}, "field": "y", "new_value": 1})
    assert r.status_code == 422


def test_api_rejects_unwritable_field(client):
    r = client.post("/api/curate/changes", json={
        "op": "update", "target_table": "core.sample",
        "target_key": {"paper_id": PAPER, "sample_id": SAMPLE},
        "field": "paper_id", "new_value": "x"})
    assert r.status_code == 422


def test_api_write_key_enforced(client, monkeypatch):
    import steeldig_api.main as m
    monkeypatch.setattr(m, "WRITE_KEY", "secret-key")
    body = {"op": "update", "target_table": "core.sample",
            "target_key": {"paper_id": PAPER, "sample_id": SAMPLE},
            "field": "label", "new_value": "x"}
    assert client.post("/api/curate/changes", json=body).status_code == 401
    ok = client.post("/api/curate/changes", json=body, headers={"X-API-Key": "secret-key"})
    assert ok.status_code == 201
    # 撤销刚写入的那一条，避免留下脏数据
    cid = ok.json()["change_id"]
    assert client.post(f"/api/curate/changes/{cid}/revert",
                       headers={"X-API-Key": "secret-key"}).status_code == 200
    with connect() as c:
        c.execute("DELETE FROM curate.change WHERE change_id=%s", (cid,))
        c.commit()


def test_changes_endpoint_lists(client):
    d = client.get("/api/curate/changes").json()
    assert "items" in d and "stats" in d
    assert d["stats"]["failed"] == 0
