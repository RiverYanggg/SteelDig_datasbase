"""成分解析：nominal_composition → 元素长表 + 化学式 + 元素体系（chemsys）。

仿 Materials Project 的可聚合维度：

    formula   FeMn28Al10C0.8   人类可读，基体元素在前，其余按质量分数降序
    chemsys   Al-C-Fe-Mn       字母序元素体系，天然的"材料体系"分面
    elements  {Fe, Mn, Al, C}  数组列 + GIN，支持"含 Al 且含 Si"这类过滤
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .quantity import clean, parse_quantity

_ELEM_RE = re.compile(r"^[A-Z][a-z]?$")


@dataclass
class Composition:
    elements: list[str] = field(default_factory=list)
    weight_pct: dict[str, float] = field(default_factory=dict)
    atomic_pct: dict[str, float] = field(default_factory=dict)
    balance: str | None = None
    rows: list[dict] = field(default_factory=list)
    formula: str | None = None
    formula_alpha: str | None = None
    chemsys: str | None = None

    @property
    def n_elements(self) -> int:
        return len(self.elements)


def _to_float(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    q = parse_quantity(v)
    return q.mid


def _fmt(x: float) -> str:
    """28.0 → '28'，0.8 → '0.8'，0.0025 → '0.0025'。"""
    if x == int(x):
        return str(int(x))
    return f"{x:g}"


def parse_composition(nominal: list[dict] | None, base_element: str | None = None) -> Composition:
    comp = Composition()
    for row in nominal or []:
        if not isinstance(row, dict):
            continue
        el = (row.get("element") or "").strip()
        if not el:
            continue
        # 统一符号大小写：fe → Fe，MN → Mn
        el = el[0].upper() + el[1:].lower()
        if not _ELEM_RE.match(el):
            continue
        raw_wt = clean(row.get("weight_percent"))
        is_balance = bool(re.match(r"^(bal\.?|balance|rest|余量)", raw_wt, re.I))
        wt = None if is_balance else _to_float(row.get("weight_percent"))
        at = _to_float(row.get("atomic_percent"))

        comp.rows.append({
            "element": el, "weight_pct": wt, "atomic_pct": at,
            "raw_wt": raw_wt or None, "is_balance": is_balance,
        })
        if el not in comp.elements:
            comp.elements.append(el)
        if wt is not None:
            comp.weight_pct[el] = wt
        if at is not None:
            comp.atomic_pct[el] = at
        if is_balance and comp.balance is None:
            comp.balance = el

    base = (base_element or comp.balance or "").strip()
    base = base[0].upper() + base[1:].lower() if base else None
    if base and base not in comp.elements:
        comp.elements.insert(0, base)

    # --- formula：基体元素在前，其余按 wt 降序；无系数的元素只写符号
    ordered = [e for e in ([base] if base else []) + sorted(
        (e for e in comp.elements if e != base),
        key=lambda e: comp.weight_pct.get(e, -1), reverse=True)]
    ordered = list(dict.fromkeys(ordered))
    parts = []
    for e in ordered:
        v = comp.weight_pct.get(e)
        parts.append(e if v is None else f"{e}{_fmt(v)}")
    comp.formula = "".join(parts) if parts else None

    # --- formula_alpha：字母序（跨论文合并/去重时用）
    comp.formula_alpha = "".join(
        e if comp.weight_pct.get(e) is None else f"{e}{_fmt(comp.weight_pct[e])}"
        for e in sorted(comp.elements)
    ) or None

    comp.chemsys = "-".join(sorted(comp.elements)) if comp.elements else None
    return comp
