"""成分检索：先精确、再按成分距离做模糊匹配。

查询形式：`Al:8-11`、`Mn:25-`、`C:-1.2`、`Si`（只要求含该元素）。
匹配规则：
    精确  —— 每个指定元素的 wt% 都落在区间内（未列出视为 0），且 must 元素含量 > 0
    模糊  —— 到区间的最短距离之和（wt% 点），score = 1 / (1 + d/5)

规模说明：当前 250 个合金、约 1,100 条成分行，直接在内存里算最直观；
到万篇级应把这段逻辑下推到 SQL（或对成分向量建 ANN 索引）。
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from . import db

SYMBOL = re.compile(r"^[A-Z][a-z]?$")
CACHE_TTL = 60.0
_cache: dict[str, Any] = {"t": 0.0, "alloys": {}, "available": {}}


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
@dataclass
class Query:
    ranges: dict[str, tuple[float | None, float | None]] = field(default_factory=dict)
    must: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "ranges": {k: {"min": v[0], "max": v[1]} for k, v in self.ranges.items()},
            "must": self.must,
        }


def parse_params(pairs: list[str] | None, must: str | None = None) -> Query:
    """把 ['Al:8-11', 'Mn:25-'] 解析成区间；解析失败抛 ValueError。"""
    q = Query()
    for raw in pairs or []:
        item = (raw or "").strip()
        if not item:
            continue
        if ":" in item:
            sym, spec = item.split(":", 1)
        else:
            sym, spec = item, ""
        sym = sym.strip()
        if not SYMBOL.match(sym):
            raise ValueError(f"非法元素符号：{sym}")
        if not spec:
            q.ranges.setdefault(sym, (0.0, None))
            continue
        lo_s, _, hi_s = spec.partition("-")
        try:
            lo = float(lo_s) if lo_s.strip() else 0.0
            hi = float(hi_s) if hi_s.strip() else None
        except ValueError as exc:
            raise ValueError(f"区间格式不对：{item}（应为 Al:8-11）") from exc
        if lo < 0 or (hi is not None and hi < lo):
            raise ValueError(f"区间不合法：{item}")
        q.ranges[sym] = (lo, hi)

    if must:
        for sym in must.replace("，", ",").split(","):
            sym = sym.strip()
            if sym:
                if not SYMBOL.match(sym):
                    raise ValueError(f"非法元素符号：{sym}")
                q.must.append(sym)
    return q


# ---------------------------------------------------------------------------
# 数据加载（60 秒缓存）
# ---------------------------------------------------------------------------
def load_matrix(force: bool = False) -> tuple[dict, dict]:
    now = time.time()
    if not force and _cache["alloys"] and now - _cache["t"] < CACHE_TTL:
        return _cache["alloys"], _cache["available"]

    rows = db.all("""
        SELECT c.paper_id, c.alloy_id, c.element, c.weight_pct,
               a.formula, a.chemsys, a.family_key, a.base_element, c.is_inferred
        FROM api.alloy_composition c
        JOIN core.alloy a ON a.paper_id = c.paper_id AND a.alloy_id = c.alloy_id
        WHERE c.weight_pct IS NOT NULL AND c.weight_pct > 0
    """)
    stats = {
        (r["paper_id"], r["alloy_id"]): r
        for r in db.all("""
            SELECT paper_id, alloy_id,
                   count(*) AS n_samples,
                   min(sample_id) AS first_sample,
                   max(yield_strength_mpa) AS max_ys,
                   max(tensile_strength_mpa) AS max_uts
            FROM api.sample_summary GROUP BY 1, 2
        """)
    }

    alloys: dict[tuple[str, str], dict] = {}
    available: dict[str, int] = {}
    for r in rows:
        key = (r["paper_id"], r["alloy_id"])
        a = alloys.setdefault(key, {
            "paper_id": r["paper_id"], "alloy_id": r["alloy_id"],
            "formula": r["formula"], "chemsys": r["chemsys"],
            "family_key": r["family_key"], "base_element": r["base_element"],
            "els": {}, "inferred": set(),
            "n_samples": 0, "max_ys": None, "max_uts": None, "first_sample": None,
        })
        a["els"][r["element"]] = float(r["weight_pct"])
        if r["is_inferred"]:
            a["inferred"].add(r["element"])
        if float(r["weight_pct"]) >= 0.5:
            available[r["element"]] = available.get(r["element"], 0) + 1

    for key, a in alloys.items():
        s = stats.get(key) or {}
        a["n_samples"] = s.get("n_samples") or 0
        a["max_ys"] = s.get("max_ys")
        a["max_uts"] = s.get("max_uts")
        a["first_sample"] = s.get("first_sample")

    _cache.update(t=now, alloys=alloys, available=available)
    return alloys, available


# ---------------------------------------------------------------------------
# 匹配
# ---------------------------------------------------------------------------
def _gap(value: float, lo: float, hi: float | None) -> float:
    if value < lo:
        return lo - value
    if hi is not None and value > hi:
        return value - hi
    return 0.0


def search(q: Query, limit: int = 20) -> dict:
    alloys, available = load_matrix()
    targets = q.ranges
    must = set(q.must) | {s for s, (lo, hi) in targets.items() if lo == 0 and hi is None}

    exact: list[dict] = []
    near: list[dict] = []

    for a in alloys.values():
        els = a["els"]
        if any(els.get(s, 0.0) <= 0 for s in must):
            continue

        dist = 0.0
        deltas: dict[str, float] = {}
        for el, (lo, hi) in targets.items():
            v = els.get(el, 0.0)
            g = _gap(v, lo, hi)
            if g > 0:
                dist += g
                deltas[el] = round(v - (hi if (hi is not None and v > hi) else lo), 3)
            elif el not in els:
                deltas[el] = round(v - lo, 3)
        # 未被要求的元素只作为排序的次要因素（不要让它把"精确"判成"模糊"）：
        # 用户问的是 Al 和 C，Mn 含量多少不该影响"是否满足查询"。
        base = a.get("base_element")
        extra = sum(v for el, v in els.items()
                    if el not in targets and v >= 1.0 and el != base)

        item = {
            "paper_id": a["paper_id"], "alloy_id": a["alloy_id"],
            "formula": a["formula"], "chemsys": a["chemsys"],
            "family_key": a["family_key"], "n_samples": a["n_samples"],
            "sample_id": a["first_sample"],
            "max_ys": float(a["max_ys"]) if a["max_ys"] is not None else None,
            "max_uts": float(a["max_uts"]) if a["max_uts"] is not None else None,
            "composition": {k: round(v, 3) for k, v in sorted(
                els.items(), key=lambda kv: kv[1], reverse=True)},
            "inferred": sorted(a["inferred"]),
        }
        if dist == 0.0:
            item["extra_elements_pct"] = round(extra, 1)
            exact.append(item)
        else:
            item["distance"] = round(dist, 2)
            item["score"] = round(1.0 / (1.0 + dist / 5.0), 3)
            item["deltas"] = deltas
            item["extra_elements_pct"] = round(extra, 1)
            near.append(item)

    exact.sort(key=lambda x: (x["extra_elements_pct"], -(x["n_samples"] or 0), x["formula"] or ""))
    near.sort(key=lambda x: (x["distance"], x["extra_elements_pct"]))
    return {
        "query": q.as_dict(),
        "exact": {"count": len(exact), "items": exact[:limit]},
        "nearest": {"count": len(near), "items": near[:limit]},
        "fallback": len(exact) == 0 and bool(targets or must),
        "available_elements": available,
    }
