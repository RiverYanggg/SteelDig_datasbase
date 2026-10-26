"""受控词表匹配：把自由的相名 / 表征手段对齐到 canon 词表。

原则：只做"高置信度"匹配，宁缺毋滥。
    * 归一化后完全相同 → 1.0
    * 别名作为子串出现（别名长度 ≥ 3） → 0.8 ~ 0.9，按别名长度加权
    * 单字符别名（α / γ / δ）只在整体完全相等时才采用，避免误伤

匹配不上就留 NULL —— 留给人工/后续规则迭代，绝不猜。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

_GREEK = "αβγδεζηθικλμνξοπρστυφχψω"
_NON_WORD = re.compile(rf"[^0-9a-zA-Z{_GREEK}]+")


def normalize(text: str | None) -> str:
    if not text:
        return ""
    t = str(text).lower()
    t = t.replace("í", "i").replace("é", "e")
    return _NON_WORD.sub("", t)


@dataclass(frozen=True)
class Match:
    key: str | None
    score: float
    term: str | None = None


class _Vocabulary:
    """通用词表匹配器。"""

    def __init__(self, entries: Iterable[tuple[str, list[str]]]):
        # [(key, aliases)]，aliases 已包含主名称
        self.terms: list[tuple[str, str, str]] = []   # (key, alias_norm, alias_raw)
        for key, aliases in entries:
            for a in aliases:
                n = normalize(a)
                if n:
                    self.terms.append((key, n, a))
        # 长别名优先，减少"被短别名抢先"的概率
        self.terms.sort(key=lambda x: len(x[1]), reverse=True)
        self.max_len = max((len(t[1]) for t in self.terms), default=0)

    def match(self, text: str | None, min_score: float = 0.75) -> Match:
        n = normalize(text)
        if not n:
            return Match(None, 0.0)

        # 1) 完全相等（最可靠）
        for key, alias, raw in self.terms:
            if n == alias:
                return Match(key, 1.0, raw)

        # 2) 子串匹配：别名必须够长，避免 α / γ 这类单字符误伤
        best = Match(None, 0.0)
        for key, alias, raw in self.terms:
            if len(alias) < 3:
                continue
            if alias in n:
                score = 0.8 + 0.1 * min(len(alias) / 12.0, 1.0)
                if score > best.score:
                    best = Match(key, round(score, 3), raw)
        return best if best.score >= min_score else Match(None, 0.0)


class PhaseResolver(_Vocabulary):
    def __init__(self, rows: list[dict]):
        super().__init__(
            (r["phase_key"], [r["name"], *(r.get("aliases") or [])]) for r in rows)


class TechniqueResolver(_Vocabulary):
    def __init__(self, rows: list[dict]):
        super().__init__(
            (r["technique_key"],
             [r["name"], r.get("abbreviation") or "", *(r.get("aliases") or [])])
            for r in rows)


def load_resolvers(conn) -> tuple[PhaseResolver, TechniqueResolver]:
    phases = [
        {"phase_key": k, "name": n, "aliases": list(a or [])}
        for k, n, a in conn.execute(
            "SELECT phase_key, name, aliases FROM canon.phase").fetchall()
    ]
    techniques = [
        {"technique_key": k, "name": n, "abbreviation": ab, "aliases": list(a or [])}
        for k, n, ab, a in conn.execute(
            "SELECT technique_key, name, abbreviation, aliases"
            " FROM canon.characterization_technique").fetchall()
    ]
    return PhaseResolver(phases), TechniqueResolver(techniques)
