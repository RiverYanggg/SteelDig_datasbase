"""成分检索（元素周期表 + 区间 + 模糊回退）测试。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from steeldig_api import composition
from steeldig_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 参数解析（纯函数）
# ---------------------------------------------------------------------------
def test_parse_range_variants():
    q = composition.parse_params(["Al:8-11", "Mn:25-", "C:-1.2", "Si"])
    assert q.ranges["Al"] == (8.0, 11.0)
    assert q.ranges["Mn"] == (25.0, None)
    assert q.ranges["C"] == (0.0, 1.2)
    assert q.ranges["Si"] == (0.0, None)


def test_parse_must():
    q = composition.parse_params([], "Cr,Ni")
    assert q.must == ["Cr", "Ni"]


@pytest.mark.parametrize("bad", ["铝:8-11", "Al:11-8", "Al:abc", "Al:8-11-13"])
def test_parse_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        composition.parse_params([bad])


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def test_exact_match(client):
    r = client.get("/api/composition/search",
                   params=[("el", "Al:8-11"), ("el", "Mn:25-30")])
    assert r.status_code == 200
    d = r.json()
    assert d["exact"]["count"] > 0
    assert d["fallback"] is False
    formulas = [i["formula"] for i in d["exact"]["items"]]
    assert any("Al9" in f or "Al10" in f for f in formulas)
    # 完全匹配的每个元素都必须落在区间内
    for item in d["exact"]["items"]:
        assert 8 <= item["composition"].get("Al", 0) <= 11
        assert 25 <= item["composition"].get("Mn", 0) <= 30


def test_fallback_when_no_exact(client):
    r = client.get("/api/composition/search", params=[("el", "Al:20-25")])
    d = r.json()
    assert d["exact"]["count"] == 0
    assert d["fallback"] is True
    assert d["nearest"]["count"] > 0
    # 按距离升序
    dists = [i["distance"] for i in d["nearest"]["items"]]
    assert dists == sorted(dists)
    # 每个结果都带差异说明
    assert all("deltas" in i for i in d["nearest"]["items"])


def test_must_have_element(client):
    d = client.get("/api/composition/search", params=[("el", "Cr"), ("el", "Ni")]).json()
    for item in d["exact"]["items"]:
        assert item["composition"].get("Cr", 0) > 0
        assert item["composition"].get("Ni", 0) > 0


def test_missing_params_rejected(client):
    assert client.get("/api/composition/search").status_code == 422
    assert client.get("/api/composition/search", params=[("el", "Al:abc")]).status_code == 422


def test_elements_endpoint(client):
    d = client.get("/api/composition/elements").json()
    assert d["available"]["Fe"] > 200
    assert d["available"]["Al"] > 100


# ---------------------------------------------------------------------------
# 页面
# ---------------------------------------------------------------------------
def test_page_renders_table(client):
    r = client.get("/composition")
    assert r.status_code == 200
    assert "元素周期表" in r.text
    assert 'data-sym="Al"' in r.text


def test_page_exact_banner(client):
    r = client.get("/composition", params=[("el", "Al:8-11"), ("el", "Mn:25-30")])
    assert "找到" in r.text and "个完全匹配" in r.text


def test_page_fallback_banner(client):
    r = client.get("/composition", params=[("el", "Al:20-25")])
    assert "未找到完全匹配的合金" in r.text
    assert "最接近" in r.text


def test_page_bad_input_shows_error(client):
    r = client.get("/composition", params=[("el", "Al:abc")])
    assert r.status_code == 200
    assert "区间格式不对" in r.text


# ---------------------------------------------------------------------------
# 数据前提：余量元素被补全
# ---------------------------------------------------------------------------
def test_balance_element_is_filled(client):
    """Fe 写成 Bal. 的合金，在检索视图里必须有 Fe 的数值。"""
    d = client.get("/api/composition/search", params=[("el", "Fe:55-65")]).json()
    assert d["exact"]["count"] > 0
    assert all(55 <= i["composition"]["Fe"] <= 65 for i in d["exact"]["items"])
