"""合金族分类：数据驱动的规则引擎。

规则存放在 canon.alloy_family.rule（JSON），由 ETL 解释执行，而不是把
if/else 写死在代码里——这样材料专家新增一个钢种只需要 INSERT 一行。

支持的谓词::

    {"base_element": "Fe"}
    {"has_element": ["Mn","Al","C"]}
    {"element_at_least": {"Al": 3.0}}
    {"element_at_most":  {"Al": 3.0}}
    {"element_range":    {"Mn": [3.0, 12.0]}}
    {"keyword_any": ["TRIP", "transformation induced plasticity"]}
    {"title_regex": "(?i)low[- ]density"}
    {"research_type": "experimental"}
    {"all": [...]} {"any": [...]} {"not": {...}}

多族同时命中时取"最具体"的一个：树更深、条件更多者优先。
"""
from __future__ import annotations

import re
from typing import Any

MAX_DEPTH_BONUS = 10


def _conditions(rule: dict) -> int:
    """规则里的叶子条件数量，用于衡量"具体程度"。"""
    if not isinstance(rule, dict):
        return 0
    n = 0
    for k, v in rule.items():
        if k in ("all", "any"):
            n += sum(_conditions(x) for x in (v or []))
        elif k == "not":
            n += _conditions(v)
        else:
            n += 1
    return n


def _depth(rule: dict) -> int:
    if not isinstance(rule, dict):
        return 0
    best = 0
    for k, v in rule.items():
        if k in ("all", "any") and isinstance(v, list):
            best = max(best, max((_depth(x) for x in v), default=0) + 1)
        elif k == "not":
            best = max(best, _depth(v) + 1)
    return best


def evaluate(rule: Any, ctx: dict) -> bool:
    if not isinstance(rule, dict) or not rule:
        return False
    for key, val in rule.items():
        if key == "all":
            if not all(evaluate(r, ctx) for r in val):
                return False
        elif key == "any":
            if not any(evaluate(r, ctx) for r in val):
                return False
        elif key == "not":
            if evaluate(val, ctx):
                return False
        elif key == "base_element":
            if (ctx.get("base_element") or "") != val:
                return False
        elif key == "has_element":
            if not all(e in ctx["elements"] for e in val):
                return False
        elif key == "element_at_least":
            for el, thr in val.items():
                if ctx["weight_pct"].get(el, 0.0) < thr:
                    return False
        elif key == "element_at_most":
            # 约定：成分表未列出的元素按"未有意添加"处理（残余量级）。
            # 若需要"必须报道才可断言"的严格语义，改用 element_range。
            for el, thr in val.items():
                if ctx["weight_pct"].get(el, 0.0) > thr:
                    return False
        elif key == "element_range":
            for el, (lo, hi) in val.items():
                v = ctx["weight_pct"].get(el)
                if v is None or not (lo <= v <= hi):
                    return False
        elif key == "keyword_any":
            hay = ctx["keywords_blob"]
            if not any(str(k).lower() in hay for k in val):
                return False
        elif key == "title_regex":
            if not re.search(val, ctx.get("title") or ""):
                return False
        elif key == "n_elements_at_most":
            if len(ctx["elements"]) > int(val):
                return False
        elif key == "research_type":
            if (ctx.get("research_type") or "") != val:
                return False
        else:
            # 未知谓词：判否（宁可漏分，也不误分），并在 ETL 日志里可见
            return False
    return True


def classify(families: list[dict], ctx: dict) -> str | None:
    """families: [{family_key, rule, parent_key}]，返回最具体命中的 family_key。"""
    depth_of: dict[str, int] = {}
    for f in families:  # 计算层级深度，子类优先
        if f.get("family_key") not in depth_of:
            depth_of[f["family_key"]] = 0
    changed = True
    while changed:
        changed = False
        for f in families:
            p = f.get("parent_key")
            if p and depth_of.get(f["family_key"], 0) <= depth_of.get(p, -1):
                depth_of[f["family_key"]] = depth_of.get(p, 0) + 1
                changed = True

    matches: list[tuple[int, int, str]] = []
    for f in families:
        rule = f.get("rule") or {}
        if evaluate(rule, ctx):
            matches.append((depth_of.get(f["family_key"], 0), _conditions(rule), f["family_key"]))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][2]
