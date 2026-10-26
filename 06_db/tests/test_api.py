"""API 契约测试。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from steeldig_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_stats(client):
    d = client.get("/api/stats").json()
    assert d["papers"] == 68 and d["samples"] == 638
    assert d["lake_bytes_mb"] > 0


def test_openapi_is_served(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/search" in r.json()["paths"]


def test_paper_detail(client):
    pid = client.get("/api/papers", params={"limit": 1}).json()["items"][0]["paper_id"]
    d = client.get(f"/api/papers/{pid}").json()
    assert d["paper_id"] == pid
    assert isinstance(d["samples"], list)


def test_sample_detail_has_provenance(client):
    item = client.get("/api/samples", params={"min_ys": 500, "limit": 1}).json()["items"][0]
    d = client.get(f"/api/samples/{item['paper_id']}/{item['sample_id']}").json()
    assert d["material_id"]
    assert d["provenance"]["dataset_version"]


def test_sample_filters_are_monotonic(client):
    loose = client.get("/api/samples", params={"min_ys": 300, "limit": 1}).json()["total"]
    tight = client.get("/api/samples", params={"min_ys": 900, "limit": 1}).json()["total"]
    assert tight <= loose


def test_element_filter(client):
    total = client.get("/api/samples", params={"element": "Al", "limit": 1}).json()["total"]
    assert total > 0


def test_search_hybrid_returns_ranked(client):
    r = client.get("/api/search", params={"q": "κ-carbide", "k": 5}).json()
    assert r["n"] > 0
    scores = [i["score"] for i in r["items"]]
    assert scores == sorted(scores, reverse=True)


def test_search_chinese(client):
    r = client.get("/api/search", params={"q": "轻质钢 铝 密度", "k": 3}).json()
    assert r["n"] > 0
    assert r["segmented"] != r["query"] or " " in r["query"]


def test_trace_endpoint(client):
    item = client.get("/api/samples", params={"limit": 1}).json()["items"][0]
    d = client.get(f"/api/samples/{item['paper_id']}/{item['sample_id']}/trace").json()
    assert d["n"] > 0


def test_export_samples(client):
    d = client.get("/api/export/samples", params={"limit": 3}).json()
    assert d["n"] == 3


def test_404(client):
    assert client.get("/api/papers/10.9999_doesnotexist").status_code == 404
