"""服务端渲染的浏览界面（与 REST API 同源，共用连接池）。

设计取向：
    * 无构建步骤：Jinja2 + 手写 CSS + ECharts（本地 vendor），离线可用；
    * 只读：所有页面查询均走 api.* 视图与只读 SQL；
    * 学术工具感：以"能不能快速判断这个样品值不值得看"为第一目标，
      因此详情页把成分 / 工艺 / 相 / 性能 / 证据放在同一屏内。
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from steeldig_db.config import settings as etl_settings
from steeldig_db.lake import Lake

from steeldig_db.text import segment

from steeldig_db import curate as curation

from . import composition, db, periodic
from .embed import embed_query
from .evidence import table_html

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
router = APIRouter(include_in_schema=False)

PAGE_SIZE = 24


# ---------------------------------------------------------------------------
# 公共上下文
# ---------------------------------------------------------------------------
def _family_names() -> dict[str, str]:
    rows = db.all("SELECT family_key, name_zh, name FROM canon.alloy_family")
    return {r["family_key"]: (r["name_zh"] or r["name"]) for r in rows}


def _stats() -> dict:
    s = db.one("SELECT * FROM api.stats") or {}
    s["lake_mb"] = round(float(s.get("lake_bytes") or 0) / 1e6, 1)
    return s


_FAM = {"t": 0.0, "m": {}}


def family_label(fk) -> str:
    """模板内可用的合金族中文名（60 秒缓存，避免每个徽章查一次库）。"""
    import time as _t
    if _t.time() - _FAM["t"] > 60:
        _FAM["m"] = _family_names()
        _FAM["t"] = _t.time()
    return _FAM["m"].get(fk, fk) if fk else "未分类"


def _jsonable(obj):
    return json.dumps(obj, ensure_ascii=False, default=float)


def ctx(request: Request, nav: str, **kw) -> dict:
    data = {
        "request": request,
        "nav": nav,
        "stats": _stats(),
        "dataset_version": "2026.10",
        "app_name": etl_settings.app_name,
        "q": request.query_params.get("q"),
    }
    data.update(kw)
    return data


templates.env.globals["page_window"] = lambda page, pages: _page_window(page, pages)
templates.env.globals["family_label"] = family_label
templates.env.filters["jsonable"] = _jsonable
# Jinja 的 |tojson 默认不认 Decimal；统一转 float
templates.env.policies["json.dumps_function"] = lambda obj, **kw: json.dumps(obj, default=float, **kw)
templates.env.filters["strip_html"] = lambda s: (s or "").replace("<", "&lt;")


def _page_window(page: int, pages: int) -> list:
    if pages <= 7:
        return list(range(1, pages + 1))
    out = [1]
    lo, hi = max(2, page - 1), min(pages - 1, page + 1)
    if lo > 2:
        out.append("…")
    out += list(range(lo, hi + 1))
    if hi < pages - 1:
        out.append("…")
    out.append(pages)
    return out


# ---------------------------------------------------------------------------
# 图表原图（从资产湖按内容哈希取，不在 Web 目录里另存副本）
# ---------------------------------------------------------------------------
_lake = Lake(etl_settings.lake_root)


@router.get("/media/figure/{paper_id}/{figure_id}")
def figure_image(paper_id: str, figure_id: str):
    row = db.one("SELECT image_paths FROM core.figure WHERE paper_id=%s AND figure_id=%s",
                 (paper_id, figure_id))
    if not row or not row["image_paths"]:
        return HTMLResponse(status_code=404)
    rel = f"{paper_id}/{row['image_paths'][0]}"
    obj = db.one("""
        SELECT o.uri, o.media_type FROM lake.object_ref r
        JOIN lake.object o USING (object_id)
        WHERE r.paper_id=%s AND r.rel_path=%s
    """, (paper_id, rel))
    if not obj:
        return HTMLResponse(status_code=404)
    path = _lake.resolve(obj["uri"])
    if not path.exists():
        return HTMLResponse(status_code=404)
    return FileResponse(path, media_type=obj["media_type"],
                        headers={"Cache-Control": "public, max-age=86400"})


# ---------------------------------------------------------------------------
# 总览
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    chemsys = db.all("""
        SELECT chemsys, count(*) AS n FROM core.alloy
        WHERE chemsys IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 7
    """)
    families = db.all("""
        SELECT a.family_key, coalesce(f.name_zh, f.name, '未分类') AS family_name,
               count(*) AS n,
               count(*) FILTER (WHERE s.yield_strength_mpa IS NOT NULL) AS with_ys
        FROM core.alloy a
        LEFT JOIN canon.alloy_family f ON f.family_key = a.family_key
        LEFT JOIN api.sample_summary s USING (paper_id, alloy_id)
        GROUP BY 1, 2 ORDER BY 3 DESC
    """)
    scatter = db.all("""
        SELECT paper_id, sample_id, family_key, yield_strength_mpa, elongation_pct,
               tensile_strength_mpa
        FROM api.sample_summary
        WHERE yield_strength_mpa IS NOT NULL AND elongation_pct IS NOT NULL
    """)
    recent = db.all("""
        SELECT paper_id, title, year, journal, n_samples, n_figures, n_equations
        FROM api.paper ORDER BY year DESC NULLS LAST, paper_id LIMIT 6
    """)
    top = db.all("""
        SELECT sample_id, paper_id, formula, yield_strength_mpa, tensile_strength_mpa,
               elongation_pct, family_key
        FROM api.sample_summary
        WHERE tensile_strength_mpa IS NOT NULL AND elongation_pct IS NOT NULL
        ORDER BY tensile_strength_mpa * elongation_pct DESC LIMIT 5
    """)
    sections = db.all("""
        SELECT section, count(*) AS n,
               count(*) FILTER (WHERE value_canonical IS NOT NULL) AS usable
        FROM core.property_value GROUP BY 1 ORDER BY 2 DESC
    """)
    return templates.TemplateResponse(request, "index.html", ctx(
        request, "home", chemsys=chemsys, families=families, scatter=json.dumps(scatter, default=float),
        recent=recent, top=top, sections=sections,
        fam_label={f["family_key"] or "未分类": f["family_name"] for f in families}))


# ---------------------------------------------------------------------------
# 样品库
# ---------------------------------------------------------------------------
@router.get("/browse", response_class=HTMLResponse)
def browse(request: Request):
    qp = request.query_params
    family = qp.get("family") or None
    element = qp.get("element") or None
    year_from = qp.get("year_from") or None
    ys_min = qp.get("ys_min") or None
    ys_max = qp.get("ys_max") or None
    el_min = qp.get("el_min") or None
    sort = qp.get("sort") or "ys"
    page = max(1, int(qp.get("page") or 1))

    where, params = ["1=1"], []
    if family:
        where.append("family_key = %s"); params.append(family)
    if element:
        where.append("%s = ANY (elements)"); params.append(element)
    if year_from:
        where.append("year >= %s"); params.append(int(year_from))
    if ys_min:
        where.append("yield_strength_mpa >= %s"); params.append(float(ys_min))
    if ys_max:
        where.append("yield_strength_mpa <= %s"); params.append(float(ys_max))
    if el_min:
        where.append("elongation_pct >= %s"); params.append(float(el_min))
    w = "WHERE " + " AND ".join(where)

    order = {
        "ys": "yield_strength_mpa DESC NULLS LAST",
        "el": "elongation_pct DESC NULLS LAST",
        "uts": "tensile_strength_mpa DESC NULLS LAST",
        "year": "year DESC NULLS LAST, paper_id",
        "al": "formula",
    }.get(sort, "yield_strength_mpa DESC NULLS LAST")

    total = db.one(f"SELECT count(*) AS n FROM api.sample_summary {w}", tuple(params))["n"]
    rows = db.all(
        f"SELECT * FROM api.sample_summary {w} ORDER BY {order}"
        f" LIMIT {PAGE_SIZE} OFFSET {(page - 1) * PAGE_SIZE}", tuple(params))

    fam_rows = db.all("""
        SELECT family_key, count(*) AS n FROM api.sample_summary
        GROUP BY 1 ORDER BY 2 DESC
    """)
    el_rows = db.all("""
        SELECT e.element, count(*) AS n FROM core.alloy_element e
        WHERE e.weight_pct IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC LIMIT 14
    """)
    pages = max(1, -(-total // PAGE_SIZE))

    keep = {k: v for k, v in qp.items() if k != "page" and v}
    base_url = "/browse?" + urlencode(keep) + ("&" if keep else "")

    return templates.TemplateResponse(request, "browse.html", ctx(
        request, "browse", rows=rows, total=total, page=page, pages=pages,
        base_url=base_url, families=fam_rows, elements=el_rows,
        sel=dict(family=family, element=element, year_from=year_from,
                 ys_min=ys_min, ys_max=ys_max, el_min=el_min, sort=sort)))


@router.get("/samples/{paper_id}/{sample_id}", response_class=HTMLResponse)
def sample_detail(request: Request, paper_id: str, sample_id: str):
    doc = db.one("SELECT api.material_document(%s,%s) AS doc", (paper_id, sample_id))["doc"]
    if not doc:
        return HTMLResponse("<h2>样品不存在</h2>", status_code=404)

    phases = db.all("""
        SELECT phase_name, phase_key, volume_fraction_pct, grain_size_um, morphology,
               crystal_structure
        FROM core.phase WHERE paper_id=%s AND sample_id=%s
        ORDER BY volume_fraction_pct DESC NULLS LAST, idx
    """, (paper_id, sample_id))
    steps = db.all("""
        SELECT seq, step_type, method, temperature_raw, temperature_k, duration_raw,
               duration_s, atmosphere, cooling_medium
        FROM core.processing_step WHERE paper_id=%s AND sample_id=%s ORDER BY seq
    """, (paper_id, sample_id))
    props = db.all("""
        SELECT section, group_path, metric, idx, path, value_raw, value_kind, value_canonical,
               value_low_canonical, value_high_canonical, unit_canonical, source_block_ids,
               block_status
        FROM core.property_value WHERE paper_id=%s AND sample_id=%s
        ORDER BY section, metric, idx
    """, (paper_id, sample_id))
    wiki = db.one("""
        SELECT summary, mechanisms, conclusions, payload
        FROM core.sample_wiki WHERE paper_id=%s AND sample_id=%s LIMIT 1
    """, (paper_id, sample_id)) or {}
    figs = db.all("""
        SELECT f.figure_id, f.kind, f.label, f.n_observations, f.block_ids
        FROM core.figure f WHERE f.paper_id=%s ORDER BY f.ordinal NULLS LAST LIMIT 8
    """, (paper_id,))
    paper = db.one("SELECT title, year, journal, doi FROM core.paper WHERE paper_id=%s",
                   (paper_id,))
    changes = db.all("""
        SELECT change_id, op, target_table, field, old_value, new_value, note, author,
               status, created_at
        FROM curate.change
        WHERE target_key->>'paper_id' = %s AND target_key->>'sample_id' = %s
        ORDER BY change_id DESC
    """, (paper_id, sample_id))

    grouped: dict[str, list] = {}
    for p in props:
        grouped.setdefault(p["section"], []).append(p)

    mechanisms = [m for m in (wiki.get("mechanisms") or []) if m]
    return templates.TemplateResponse(request, "sample.html", ctx(
        request, "browse", doc=doc, phases=phases, steps=steps, props=grouped,
        wiki=wiki, mechanisms=mechanisms, figures=figs, paper=paper,
        changes=changes, paper_id=paper_id, sample_id=sample_id))


# ---------------------------------------------------------------------------
# 校订（HTML 表单；与 REST 的 /api/curate/changes 共用同一套逻辑）
# ---------------------------------------------------------------------------
@router.post("/curate/property")
def curate_property(request: Request,
                    path: str = Form(...),
                    new_value: str = Form(...),
                    note: str = Form(""),
                    author: str = Form("ui"),
                    paper_id: str = Form(...),
                    sample_id: str = Form(...)):
    run_id = db.one("""SELECT run_id FROM core.sample_data
                       WHERE paper_id=%s AND sample_id=%s AND is_latest""",
                    (paper_id, sample_id))["run_id"]
    value = float(new_value) if new_value.replace(".", "", 1).lstrip("-").isdigit() else new_value
    with db.pool.connection() as conn:
        try:
            curation.record(conn, op="update", table="core.property_value",
                            target_key={"paper_id": paper_id, "sample_id": sample_id,
                                        "run_id": run_id, "path": path},
                            field_name="value_canonical", new_value=value,
                            note=note or None, author=author, source="ui")
        except curation.CurationError:
            pass
    return RedirectResponse(f"/samples/{paper_id}/{sample_id}", status_code=303)


@router.post("/curate/revert/{change_id}")
def curate_revert(request: Request, change_id: int,
                  back: str = Form("")):
    with db.pool.connection() as conn:
        curation.revert(conn, change_id)
    return RedirectResponse(back or "/", status_code=303)


# ---------------------------------------------------------------------------
# 文献
# ---------------------------------------------------------------------------
@router.get("/papers", response_class=HTMLResponse)
def papers(request: Request):
    qp = request.query_params
    q = (qp.get("q") or "").strip()
    year = qp.get("year") or None
    page = max(1, int(qp.get("page") or 1))

    where, params = ["1=1"], []
    if q:
        where.append("(title ILIKE %s OR abstract ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if year:
        where.append("year = %s"); params.append(int(year))
    w = "WHERE " + " AND ".join(where)

    total = db.one(f"SELECT count(*) AS n FROM core.paper p {w}", tuple(params))["n"]
    rows = db.all(f"""
        SELECT p.*, (SELECT count(*) FROM core.sample s WHERE s.paper_id=p.paper_id) AS n_samples,
               (SELECT count(*) FROM core.figure f WHERE f.paper_id=p.paper_id AND f.kind='figure') AS n_figures,
               (SELECT count(*) FROM core.equation e WHERE e.paper_id=p.paper_id) AS n_equations,
               (SELECT array_agg(DISTINCT a.family_key) FROM core.alloy a
                 WHERE a.paper_id=p.paper_id AND a.family_key IS NOT NULL) AS families
        FROM core.paper p {w}
        ORDER BY p.year DESC NULLS LAST, p.paper_id
        LIMIT {PAGE_SIZE} OFFSET {(page-1)*PAGE_SIZE}
    """, tuple(params))
    years = db.all("SELECT year, count(*) n FROM core.paper WHERE year IS NOT NULL GROUP BY 1 ORDER BY 1 DESC")
    pages = max(1, -(-total // PAGE_SIZE))
    keep = {k: v for k, v in qp.items() if k != "page" and v}
    base_url = "/papers?" + urlencode(keep) + ("&" if keep else "")
    return templates.TemplateResponse(request, "papers.html", ctx(
        request, "papers", rows=rows, total=total, page=page, pages=pages,
        base_url=base_url, years=years, sel_year=year, search_q=q))


@router.get("/papers/{paper_id}", response_class=HTMLResponse)
def paper_detail(request: Request, paper_id: str):
    p = db.one("SELECT * FROM api.paper WHERE paper_id=%s", (paper_id,))
    if not p:
        return HTMLResponse("<h2>文献不存在</h2>", status_code=404)
    samples = db.all("SELECT * FROM api.sample_summary WHERE paper_id=%s ORDER BY sample_id",
                     (paper_id,))
    figures = db.all("SELECT * FROM api.figure WHERE paper_id=%s ORDER BY ordinal NULLS LAST, figure_id",
                     (paper_id,))
    equations = db.all("SELECT * FROM api.equation WHERE paper_id=%s ORDER BY equation_id",
                       (paper_id,))
    alloys = db.all("""
        SELECT a.*, (SELECT count(*) FROM core.sample s WHERE s.paper_id=a.paper_id
                     AND s.alloy_id=a.alloy_id) AS n_samples
        FROM core.alloy a WHERE a.paper_id=%s ORDER BY a.alloy_id
    """, (paper_id,))
    chain = db.all("SELECT * FROM api.process_chain WHERE paper_id=%s", (paper_id,))
    return templates.TemplateResponse(request, "paper.html", ctx(
        request, "papers", p=p, samples=samples, figures=figures, equations=equations,
        alloys=alloys, chain=chain, paper_id=paper_id))


# ---------------------------------------------------------------------------
# 成分检索（元素周期表）
# ---------------------------------------------------------------------------
@router.get("/composition", response_class=HTMLResponse)
def composition_page(request: Request):
    qp = request.query_params
    els = qp.getlist("el")
    must = qp.get("must") or ""
    parsed = None
    result = None
    error = None
    if els or must:
        try:
            q = composition.parse_params(els, must)
            if q.ranges or q.must:
                parsed = q
                result = composition.search(q, 24)
        except ValueError as exc:
            error = str(exc)

    _, available = composition.load_matrix()
    selected = {}
    if parsed:
        selected = {k: {"min": "" if v[0] in (None, 0.0) else v[0],
                        "max": "" if v[1] is None else v[1]}
                    for k, v in parsed.ranges.items()}
    return templates.TemplateResponse(request, "composition.html", ctx(
        request, "composition",
        cells=periodic.cells(available),
        available=available,
        selected=selected,
        result=result, error=error,
        n_alloys=len(composition.load_matrix()[0]),
        family_names=_family_names()))


# ---------------------------------------------------------------------------
# 检索
# ---------------------------------------------------------------------------
@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    qp = request.query_params
    q = (qp.get("q") or "").strip()
    dtype = qp.get("type") or ""
    k = int(qp.get("k") or 20)

    items, vec_used, seg = [], False, ""
    if q:
        seg = segment(q)
        vec = embed_query(q)
        vec_used = vec is not None
        types = [dtype] if dtype else None
        items = db.all(
            "SELECT * FROM search.hybrid(%s,%s,%s::vector,%s,%s)",
            (seg, q, vec, k, types))
    counts = db.all("""
        SELECT doc_type, count(*) AS n FROM search.document GROUP BY 1 ORDER BY 2 DESC
    """)
    return templates.TemplateResponse(request, "search.html", ctx(
        request, "search", q=q, items=items, vec_used=vec_used, seg=seg,
        dtype=dtype, counts=counts))


@router.get("/evidence/{paper_id}/{block_id}", response_class=HTMLResponse)
def evidence_detail(request: Request, paper_id: str, block_id: str):
    b = db.one("""SELECT * FROM core.evidence_block
                  WHERE paper_id=%s AND block_id=%s""", (paper_id, block_id))
    if not b:
        return HTMLResponse("<h2>证据块不存在</h2>", status_code=404)
    trace = db.all("""
        SELECT sample_id, path, status FROM core.sample_trace
        WHERE paper_id=%s AND %s = ANY (block_ids) LIMIT 30
    """, (paper_id, block_id))
    figs = db.all("""
        SELECT figure_id, label, kind FROM core.figure
        WHERE paper_id=%s AND %s = ANY (block_ids) LIMIT 20
    """, (paper_id, block_id))
    return templates.TemplateResponse(request, "evidence.html", ctx(
        request, "browse", b=b, trace=trace, figures=figs, paper_id=paper_id,
        source_table=table_html(b.get("text") or "") if b["kind"] == "table" else ""))


# ---------------------------------------------------------------------------
# 分析
# ---------------------------------------------------------------------------
@router.get("/analytics", response_class=HTMLResponse)
def analytics(request: Request):
    by_year = db.all("""
        SELECT year, count(*) n FROM core.paper WHERE year IS NOT NULL GROUP BY 1 ORDER BY 1
    """)
    al_vs_ys = db.all("""
        SELECT e.weight_pct AS al, s.yield_strength_mpa AS ys, s.elongation_pct AS el
        FROM core.alloy_element e
        JOIN api.sample_summary s USING (paper_id, alloy_id)
        WHERE e.element='Al' AND e.weight_pct IS NOT NULL AND s.yield_strength_mpa IS NOT NULL
    """)
    family_stats = db.all("""
        SELECT COALESCE(f.name_zh, f.name, '未分类') AS fam, count(*) n,
               avg(s.yield_strength_mpa) ys, avg(s.elongation_pct) el
        FROM api.sample_summary s
        LEFT JOIN canon.alloy_family f ON f.family_key = s.family_key
        GROUP BY 1 ORDER BY n DESC
    """)
    metrics = db.all("""
        SELECT metric, count(*) n,
               count(*) FILTER (WHERE value_canonical IS NOT NULL) usable
        FROM core.property_value GROUP BY 1 ORDER BY 2 DESC LIMIT 12
    """)
    hist = db.all("""
        SELECT metric, value_canonical FROM core.property_value
        WHERE metric IN ('yield_strength','elongation','hardness')
          AND value_canonical IS NOT NULL
    """)
    return templates.TemplateResponse(request, "analytics.html", ctx(
        request, "analytics", by_year=by_year, al_vs_ys=json.dumps(al_vs_ys, default=float),
        family_stats=family_stats, metrics=metrics, hist=json.dumps(hist, default=float)))


# ---------------------------------------------------------------------------
# 质量
# ---------------------------------------------------------------------------
@router.get("/quality", response_class=HTMLResponse)
def quality(request: Request):
    issues = db.all("""
        SELECT rule_code, severity, count(*) n FROM ops.qa_issue GROUP BY 1,2 ORDER BY 3 DESC
    """)
    rules = db.all("SELECT * FROM ops.qa_rule ORDER BY severity, rule_code")
    resolution = db.all("""
        SELECT method, count(*) n FROM ops.block_id_resolution GROUP BY 1 ORDER BY 2 DESC
    """)
    coverage = db.all("""
        SELECT '证据块' k, count(*) n FROM core.evidence_block
        UNION ALL SELECT '溯源记录', count(*) FROM core.sample_trace
        UNION ALL SELECT '可数值化属性', count(*) FROM core.property_value WHERE value_canonical IS NOT NULL
        UNION ALL SELECT '已向量化文档', count(*) FROM search.document WHERE embed IS NOT NULL
        UNION ALL SELECT '湖对象', count(*) FROM lake.object
    """)
    status = db.all("""
        SELECT block_status, count(*) n FROM core.figure_observation GROUP BY 1 ORDER BY 2 DESC
    """)
    runs = db.all("SELECT * FROM ops.run ORDER BY run_id")
    with db.pool.connection() as conn:
        cure = curation.stats(conn)
    recent_changes = db.all("""
        SELECT change_id, op, target_table, target_key->>'paper_id' AS paper_id,
               field, note, author, status, created_at
        FROM curate.change ORDER BY change_id DESC LIMIT 10
    """)
    return templates.TemplateResponse(request, "quality.html", ctx(
        request, "quality", issues=issues, rules=rules, resolution=resolution,
        coverage=coverage, status=status, runs=runs,
        cure=cure, recent_changes=recent_changes))
