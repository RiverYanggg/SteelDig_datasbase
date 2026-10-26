"""SteelDig 材料知识库查询 API。

设计约束（与总体架构图一致）：
    * 只读：所有写操作都属于 ETL，本服务不提供写接口；
    * 分页 + 白名单排序字段，避免 SQL 注入与全表扫描；
    * 语义检索为"可选增强"：模型不可用时自动降级为全文 + 模糊检索；
    * 所有响应带 provenance（run_id / 数据版本），便于审计。
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import (APIRouter, Depends, FastAPI, Header, HTTPException, Query)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import steeldig_db.config  # noqa: F401  —— 导入即加载 06_db/.env，保证与 ETL 同源配置

from . import composition, db, queries as Q
from steeldig_db import curate as curation
from .embed import get_embedder
from .web import router as web_router

DSN = os.environ.get(
    "STEELDIG_DSN", "postgresql://steeldig:steeldig_dev_pw@127.0.0.1:5435/steeldig")
EMBED_MODEL = os.environ.get("STEELDIG_EMBED_MODEL") or None
EMBED_DIM = int(os.environ.get("STEELDIG_EMBED_DIM", "384"))
MODEL_CACHE = str(steeldig_db.config.settings.model_cache)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield
    db.close()


app = FastAPI(
    title=f"{steeldig_db.config.settings.app_name} Materials Knowledge API",
    version="1.0.0",
    description=(
        "面向 Fe-Mn-Al-C 低密度钢文献知识库的只读查询接口。\n\n"
        "**分层**：资产湖（不可变 JSON/图片）→ PostgreSQL（实体列 + JSONB 保真 + trace）"
        "→ 检索层（全文 / 模糊 / 向量）→ 本 API。\n\n"
        "**溯源**：任一性能值都可通过 `source_block_ids` 回指原文段落。"
    ),
    lifespan=lifespan,
)
api = APIRouter()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(__import__("pathlib").Path(__file__).parent / "static")),
          name="static")
app.include_router(web_router)


def fetch_all(sql: str, params: dict | tuple = ()) -> list[dict]:
    return db.all(sql, params)


def fetch_one(sql: str, params: dict | tuple = ()) -> dict | None:
    return db.one(sql, params)


@api.get("/health", tags=["运维"])
def health() -> dict:
    row = fetch_one("SELECT 1 AS ok, now() AS ts")
    return {"status": "ok", "db": bool(row), "ts": row["ts"] if row else None}


@api.get("/stats", tags=["运维"])
def stats() -> dict:
    data = fetch_one("SELECT * FROM api.stats")
    data["lake_bytes_mb"] = round(float(data["lake_bytes"]) / 1e6, 1)
    return data


# ---------------------------------------------------------------------------
# 写操作：人工校订（增删改）
# ----------------------------------------------------------------------------
# 事实层 core 由 ETL 重建，直接写会被覆盖。所有人工修改都落到 curate.change，
# ingest 结束后自动重放，因此持久、可审计、可撤销。
# 鉴权：设置环境变量 STEELDIG_WRITE_KEY 后，写接口要求 X-API-Key 头。
# ---------------------------------------------------------------------------
WRITE_KEY = os.environ.get("STEELDIG_WRITE_KEY")


def require_write_key(x_api_key: str | None = Header(default=None)) -> str:
    if WRITE_KEY and x_api_key != WRITE_KEY:
        raise HTTPException(401, "写操作需要有效的 X-API-Key")
    return "api"


@app.get("/api/curate/schema", tags=["校订"])
def curate_schema() -> dict:
    return {"items": [
        {"table": e.table, "key": list(e.key), "updatable": list(e.updatable),
         "creatable": e.creatable, "deletable": e.deletable,
         "required_on_create": list(e.required_on_create)}
        for e in curation.REGISTRY.values()
    ]}


@app.get("/api/curate/changes", tags=["校订"])
def list_changes(status: str | None = None, table: str | None = None,
                 paper_id: str | None = None,
                 limit: int = Query(50, ge=1, le=500)) -> dict:
    where, params = ["1=1"], []
    if status:
        where.append("status = %s"); params.append(status)
    if table:
        where.append("target_table = %s"); params.append(table)
    if paper_id:
        where.append("target_key->>'paper_id' = %s"); params.append(paper_id)
    w = " AND ".join(where)
    rows = db.all(f"SELECT * FROM curate.change WHERE {w}"
                  f" ORDER BY change_id DESC LIMIT {limit}", tuple(params))
    with db.pool.connection() as conn:
        st = curation.stats(conn)
    return {"n": len(rows), "items": rows, "stats": st}


@app.post("/api/curate/changes", tags=["校订"], status_code=201)
def create_change(body: dict, _: str = Depends(require_write_key)) -> dict:
    try:
        with db.pool.connection() as conn:
            cid = curation.record(
                conn,
                op=body.get("op", "update"),
                table=body.get("target_table", ""),
                target_key=body.get("target_key") or {},
                field_name=body.get("field"),
                new_value=body.get("new_value"),
                note=body.get("note"),
                author=body.get("author") or "api",
                source="api",
            )
        return {"change_id": cid, "status": "applied"}
    except curation.CurationError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/curate/changes/{change_id}/revert", tags=["校订"])
def revert_change(change_id: int, _: str = Depends(require_write_key)) -> dict:
    try:
        with db.pool.connection() as conn:
            ok = curation.revert(conn, change_id)
            if not ok:
                raise HTTPException(404, "校订不存在或已撤销")
            ch = conn.execute("SELECT op FROM curate.change WHERE change_id=%s",
                              (change_id,)).fetchone()
        return {"change_id": change_id, "status": "reverted",
                "need_reingest": ch["op"] == "delete"}
    except curation.CurationError as exc:
        raise HTTPException(422, str(exc)) from exc


# ---------------------------------------------------------------------------
# 论文
# ---------------------------------------------------------------------------
@api.get("/papers", tags=["论文"])
def list_papers(
    q: str | None = Query(None, description="标题/摘要关键词"),
    year_from: int | None = None,
    year_to: int | None = None,
    family: str | None = Query(None, description="合金族 family_key"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    items, total = Q.list_papers(fetch_all, fetch_one, q, year_from, year_to, family, limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@api.get("/papers/{paper_id}", tags=["论文"])
def get_paper(paper_id: str) -> dict:
    row = fetch_one("SELECT * FROM api.paper WHERE paper_id = %s", (paper_id,))
    if not row:
        raise HTTPException(404, f"paper {paper_id} not found")
    row["process_tree"] = Q.process_tree(fetch_all, paper_id)
    row["alloys"] = fetch_all(
        "SELECT alloy_id, name, formula, chemsys, elements, family_key, n_elements"
        " FROM core.alloy WHERE paper_id = %s ORDER BY alloy_id", (paper_id,))
    row["samples"] = fetch_all(
        "SELECT * FROM api.sample_summary WHERE paper_id = %s ORDER BY sample_id", (paper_id,))
    return row


@api.get("/papers/{paper_id}/samples", tags=["论文"])
def paper_samples(paper_id: str) -> dict:
    return {"items": fetch_all(
        "SELECT * FROM api.sample_summary WHERE paper_id = %s ORDER BY sample_id", (paper_id,))}


# ---------------------------------------------------------------------------
# 样品
# ---------------------------------------------------------------------------
@api.get("/samples", tags=["样品"])
def list_samples(
    family: str | None = None,
    element: str | None = Query(None, description="必须含有的元素符号，如 Al"),
    min_ys: float | None = Query(None, description="屈服强度下限 MPa"),
    max_ys: float | None = Query(None, description="屈服强度上限 MPa"),
    min_uts: float | None = Query(None, description="抗拉强度下限 MPa"),
    min_elongation: float | None = Query(None, description="断后伸长率下限 %"),
    has_ferrite: bool | None = Query(None, description="是否含铁素体"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    where, params = Q.sample_filters(family, element, min_ys, max_ys, min_uts, min_elongation, has_ferrite)
    total = fetch_one(f"SELECT count(*) AS n FROM api.sample_summary s {where}", params)["n"]
    rows = fetch_all(
        f"SELECT * FROM api.sample_summary s {where}"
        " ORDER BY yield_strength_mpa DESC NULLS LAST, paper_id, sample_id"
        f" LIMIT {limit} OFFSET {offset}", params)
    return {"total": total, "limit": limit, "offset": offset, "items": rows}


@api.get("/samples/{paper_id}/{sample_id}", tags=["样品"])
def get_sample(paper_id: str, sample_id: str) -> dict:
    doc = fetch_one("SELECT api.material_document(%s, %s) AS doc", (paper_id, sample_id))
    if not doc or doc["doc"] is None:
        raise HTTPException(404, "sample not found")
    doc["doc"]["process_chain"] = fetch_one(
        "SELECT * FROM api.process_chain WHERE paper_id = %s AND sample_id = %s",
        (paper_id, sample_id))
    return doc["doc"]


@api.get("/samples/{paper_id}/{sample_id}/trace", tags=["溯源"])
def sample_trace(paper_id: str, sample_id: str, only_ok: bool = False) -> dict:
    rows = fetch_all(
        "SELECT * FROM api.trace WHERE paper_id = %s AND sample_id = %s"
        + (" AND status = 'ok'" if only_ok else "")
        + " ORDER BY path", (paper_id, sample_id))
    return {"n": len(rows), "items": rows}


# ---------------------------------------------------------------------------
# 性能量
# ---------------------------------------------------------------------------
@api.get("/properties", tags=["性能"])
def list_properties(
    metric: str | None = None,
    section: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    paper_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    where = ["1=1"]
    params: list[Any] = []
    if metric:
        where.append("metric = %s")
        params.append(metric)
    if section:
        where.append("section = %s")
        params.append(section)
    if paper_id:
        where.append("paper_id = %s")
        params.append(paper_id)
    if min_value is not None:
        where.append("value_canonical >= %s")
        params.append(min_value)
    if max_value is not None:
        where.append("value_canonical <= %s")
        params.append(max_value)
    w = "WHERE " + " AND ".join(where)
    total = fetch_one(f"SELECT count(*) AS n FROM api.property {w}", tuple(params))["n"]
    rows = fetch_all(
        f"SELECT paper_id, sample_id, label, formula, section, metric, value_raw,"
        f" value_canonical, unit_canonical, value_kind, block_status, source_block_ids"
        f" FROM api.property {w} ORDER BY metric, value_canonical DESC NULLS LAST"
        f" LIMIT {limit} OFFSET {offset}", tuple(params))
    return {"total": total, "items": rows}


@api.get("/metrics", tags=["性能"])
def metric_catalog() -> dict:
    return {"items": fetch_all(Q.METRIC_CATALOG)}


# ---------------------------------------------------------------------------
# 图表 / 公式 / 证据
# ---------------------------------------------------------------------------
@api.get("/papers/{paper_id}/figures", tags=["图表"])
def paper_figures(paper_id: str, kind: Literal["figure", "table"] | None = None) -> dict:
    sql = "SELECT * FROM api.figure WHERE paper_id = %s"
    params: list[Any] = [paper_id]
    if kind:
        sql += " AND kind = %s"
        params.append(kind)
    return {"items": fetch_all(sql + " ORDER BY ordinal NULLS LAST, figure_id", tuple(params))}


@api.get("/papers/{paper_id}/equations", tags=["公式"])
def paper_equations(paper_id: str) -> dict:
    return {"items": fetch_all(
        "SELECT * FROM api.equation WHERE paper_id = %s ORDER BY equation_id", (paper_id,))}


@api.get("/evidence/{paper_id}/{block_id}", tags=["溯源"])
def get_evidence(paper_id: str, block_id: str) -> dict:
    row = fetch_one(
        "SELECT * FROM core.evidence_block WHERE paper_id = %s AND block_id = %s",
        (paper_id, block_id))
    if not row:
        raise HTTPException(404, "block not found")
    row["cited_by"] = Q.block_backlinks(fetch_all, paper_id, block_id)
    return row


# ---------------------------------------------------------------------------
# 成分检索（元素周期表 + 区间筛选）
# ---------------------------------------------------------------------------
@app.get("/api/composition/elements", tags=["成分"])
def composition_elements() -> dict:
    """元素分布：库里有多少合金含该元素（供前端画周期表）。"""
    _, available = composition.load_matrix()
    return {"available": available, "total_alloys": 250}


@app.get("/api/composition/search", tags=["成分"])
def composition_search(
    el: list[str] | None = Query(None, description="重复传参：el=Al:8-11&el=Mn:25-30"),
    must: str | None = Query(None, description="必须含有的元素，逗号分隔"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    try:
        q = composition.parse_params(el, must)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not q.ranges and not q.must:
        raise HTTPException(422, "至少指定一个元素或区间")
    return composition.search(q, limit)


# ---------------------------------------------------------------------------
# 检索
# ---------------------------------------------------------------------------
@api.get("/search", tags=["检索"])
def search(
    q: str = Query(..., min_length=1, description="查询串（中英文均可）"),
    k: int = Query(10, ge=1, le=50),
    types: str | None = Query(None, description="逗号分隔：paper,wiki,figure,table,equation,finding"),
    mode: Literal["hybrid", "text", "fuzzy", "vector"] = "hybrid",
) -> dict:
    seg = Q.segment(q)
    vec = None
    if mode in ("hybrid", "vector"):
        emb = get_embedder()
        if emb is not None:
            prefix = "query: " if "e5" in (EMBED_MODEL or "").lower() else ""
            v = next(iter(emb.query_embed([f"{prefix}{q}"])))
            vec = "[" + ",".join(f"{x:.7f}" for x in v) + "]"
    if mode == "vector" and vec is None:
        raise HTTPException(503, "语义检索不可用：未配置或无法加载嵌入模型")

    type_list = [t.strip() for t in types.split(",")] if types else None
    rows = fetch_all(
        "SELECT * FROM search.hybrid(%s, %s, %s::vector, %s, %s)",
        (seg, q, vec, k, type_list))
    return {"query": q, "segmented": seg, "mode": mode, "vector_used": vec is not None,
            "n": len(rows), "items": rows}


@api.get("/graph/{paper_id}", tags=["图谱"])
def paper_graph(paper_id: str) -> dict:
    return Q.paper_graph(fetch_all, paper_id)


# ---------------------------------------------------------------------------
# 导出（下游训练数据 / 批量分析）
# ---------------------------------------------------------------------------
@api.get("/export/samples", tags=["导出"])
def export_samples(
    family: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    rows = fetch_all(
        "SELECT paper_id, sample_id FROM api.sample_summary"
        + (" WHERE family_key = %s" if family else "")
        + f" ORDER BY paper_id, sample_id LIMIT {limit}",
        (family,) if family else ())
    docs = []
    for r in rows:
        d = fetch_one("SELECT api.material_document(%s, %s) AS doc",
                      (r["paper_id"], r["sample_id"]))
        if d and d["doc"]:
            docs.append(d["doc"])
    return {"n": len(docs), "items": docs}


# REST API 统一挂在 /api 下；根路径留给浏览界面
app.include_router(api, prefix="/api")
