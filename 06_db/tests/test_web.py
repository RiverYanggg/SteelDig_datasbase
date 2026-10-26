"""浏览界面（服务端渲染）的冒烟测试。

只验证"页面能渲染、关键内容在、没有 500"，不锁定具体排版。
"""
from __future__ import annotations

import pytest
import re
from fastapi.testclient import TestClient

from steeldig_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _first_sample(client):
    return client.get("/api/samples", params={"min_ys": 400, "limit": 1}).json()["items"][0]


@pytest.mark.parametrize("path", ["/", "/browse", "/papers", "/search",
                                  "/analytics", "/quality"])
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "<!doctype html>" in r.text.lower()
    assert "SteelDig" in r.text


def test_home_contains_kpis(client):
    t = client.get("/").text
    assert "材料知识库总览" in t
    assert "强度–塑性分布" in t
    assert "强塑积排行" in t


def test_browse_filters_apply(client):
    loose = client.get("/browse", params={"ys_min": 300}).text
    tight = client.get("/browse", params={"ys_min": 1200}).text
    assert loose != tight


def test_sample_page_shows_composition_and_provenance(client):
    s = _first_sample(client)
    r = client.get(f"/samples/{s['paper_id']}/{s['sample_id']}")
    assert r.status_code == 200
    body = r.text
    assert "名义成分" in body and "性能" in body
    assert "工艺链" in body


def test_sample_evidence_links_open_source_blocks(client):
    paper = "10.1002_srin.202100643"
    sample = "sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac"
    body = client.get(f"/samples/{paper}/{sample}").text
    links = re.findall(r'href="(/evidence/[^\"]+)"', body)
    assert links, "有据性能应提供可点击的原文证据链接"
    for link in set(links):
        source = client.get(link)
        assert source.status_code == 200
        assert "被引用为" in source.text


def test_sample_curation_options_include_property_paths(client):
    paper = "10.1002_srin.202100643"
    sample = "sample_fe-28mn-10al-0.8c-0.0025n__hot-forged-1123-1323k-ac"
    body = client.get(f"/samples/{paper}/{sample}").text
    options = re.findall(r'<option value="([^\"]*)">', body)
    assert options and all(path.startswith("$.properties[") for path in options)


def test_paper_page_lists_figures(client):
    s = _first_sample(client)
    r = client.get(f"/papers/{s['paper_id']}")
    assert r.status_code == 200
    assert "图表" in r.text


def test_search_page_runs_hybrid(client):
    r = client.get("/search", params={"q": "轻质钢 铝"})
    assert r.status_code == 200
    assert "检索" in r.text
    assert "score" in r.text


def test_quality_page_reports_no_error(client):
    t = client.get("/quality").text
    assert "数据质量" in t
    assert "BLOCK_ID_DANGLING" in t


def test_figure_image_endpoint_serves_bytes(client):
    s = _first_sample(client)
    fig = client.get(f"/api/papers/{s['paper_id']}/figures").json()["items"]
    if not fig:
        pytest.skip("该论文没有图表")
    fid = fig[0]["figure_id"]
    r = client.get(f"/media/figure/{s['paper_id']}/{fid}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_rest_api_and_ui_coexist(client):
    """同一个服务里，/api 返回 JSON、根路径返回 HTML，互不遮挡。"""
    assert client.get("/api/stats").headers["content-type"].startswith("application/json")
    assert client.get("/").headers["content-type"].startswith("text/html")
