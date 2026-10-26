"""block_id 对齐：把产物里的"合成 id"还原成真实的证据块。

现状（《数据库建立》2.5 已指出）：

    evidence_blocks.json 里的真实 id 只有一种形态：b0001 … bNNNN
    figure/*.json 的 observation.evidence[].id 里却混进了大量合成 id：
        b_caption_002 / b_citing_2 / caption_figure_003 / citing_sentence_…
        figure_008 / table_003 / fig7_caption / cite_fig11_1 …

直接入库会导致 provenance 断链。本模块用三级策略还原：

    1. direct     —— 本身就是 bNNNN 且真实存在（含 b013 → b0013 补零）
    2. figure_group —— 依据"角色 + 图表序号"，回查 image_groups.json 的
                       caption_block_ids / citation_block_ids（这些是真实 id）
    3. fuzzy      —— 从杂串里抽出 bNNNN 片段再校验

还原不了的保留原样并标记 unresolved，绝不臆造。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

REAL_ID_RE = re.compile(r"^b(\d{4})$")
SHORT_ID_RE = re.compile(r"^b(\d{1,3})$")
EMBEDDED_ID_RE = re.compile(r"\bb(\d{4})\b")

_REF_RE = re.compile(r"(figure|fig|table|tab|equation|eq)[\s_\-.]*0*(\d{1,3})", re.I)
_CAPTION_RE = re.compile(r"(caption|cap\b|cap_|_cap|题注|图注)", re.I)
_CITATION_RE = re.compile(r"(cit|citing|cite|citation|cited|引用|正文)", re.I)
_NOISE = {"none", "unspecified", "unknown", "n/a", "null", "na", ""}


@dataclass
class Resolution:
    raw: str
    method: str
    confidence: float
    block_ids: list[str] = field(default_factory=list)
    note: str | None = None

    @property
    def status(self) -> str:
        if self.method == "direct":
            return "ok"
        if self.block_ids:
            return "partial"
        return "unresolved"


class BlockResolver:
    """单篇论文范围内的 id 解析器。"""

    def __init__(self, real_ids: set[str], groups: list[dict],
                 sections: dict[str, str] | None = None):
        self.real_ids = real_ids
        self.sections = sections or {}
        # figure_id → {"caption": [...], "citation": [...], "ordinal": n}
        self.groups: dict[str, dict] = {}
        self.by_ordinal: dict[int, str] = {}
        for g in groups:
            fid = g.get("figure_id")
            if not fid:
                continue
            self.groups[fid] = {
                "caption": [b for b in (g.get("caption_block_ids") or []) if b in real_ids],
                "citation": [b for b in (g.get("citation_block_ids") or []) if b in real_ids],
                "ordinal": g.get("ordinal"),
            }
            if isinstance(g.get("ordinal"), int):
                self.by_ordinal[g["ordinal"]] = fid

    # -- 内部 --------------------------------------------------------------
    def _lookup_group(self, keyword: str, number: int) -> str | None:
        """按 'figure/table + 序号' 找 image_groups 里的 figure_id。"""
        prefix = "table" if keyword.lower().startswith(("table", "tab")) else "figure"
        for fid in self.groups:
            if not fid.startswith(prefix):
                continue
            m = re.search(r"(\d+)$", fid)
            if m and int(m.group(1)) == number:
                return fid
        return None

    def _from_group(self, fid: str, role: str | None) -> list[str]:
        g = self.groups.get(fid)
        if not g:
            return []
        if role == "caption":
            return g["caption"] or g["citation"]
        if role == "citation":
            return g["citation"] or g["caption"]
        # 角色不明：两类都给，宁可多不可断
        return list(dict.fromkeys(g["caption"] + g["citation"]))

    # -- 对外 --------------------------------------------------------------
    def _abstract_block(self) -> str | None:
        for bid, sec in self.sections.items():
            if sec and "abstract" in sec.lower():
                return bid
        return None

    def resolve(self, raw_id: str, role_hint: str | None = None,
                context_fid: str | None = None) -> Resolution:
        raw = (raw_id or "").strip()
        if raw.lower() in _NOISE:
            return Resolution(raw, "unresolved", 0.0, [], "空/占位 id")

        # 1) 直接命中
        m = REAL_ID_RE.match(raw)
        if m and raw in self.real_ids:
            return Resolution(raw, "direct", 1.0, [raw])
        m = SHORT_ID_RE.match(raw)
        if m:
            padded = f"b{int(m.group(1)):04d}"
            if padded in self.real_ids:
                return Resolution(raw, "direct", 0.95, [padded], f"补零 → {padded}")

        # 2) 角色 + 图表序号 → image_groups
        role = role_hint
        if role not in ("caption", "citation"):
            if _CAPTION_RE.search(raw):
                role = "caption"
            elif _CITATION_RE.search(raw):
                role = "citation"
            else:
                role = None

        ref = _REF_RE.search(raw)
        if ref:
            keyword, number = ref.group(1), int(ref.group(2))
            fid = self._lookup_group(keyword, number)
            if fid:
                ids = self._from_group(fid, role)
                if ids:
                    conf = 0.9 if role else 0.7
                    return Resolution(raw, "figure_group", conf, ids,
                                      f"{raw} → {fid} ({role or 'caption+citation'})")

        # 3) 裸 figure_id（"figure_008" 直接就是组 id）
        if raw in self.groups:
            ids = self._from_group(raw, role)
            if ids:
                return Resolution(raw, "figure_group", 0.85, ids, f"{raw} 命中同名组")

        # 4) 同一图表上下文兜底：b_caption / b_cite1 这类没有图表序号，
        #    但出现在 figure_002 的 JSON 里，按"本图组的题注/引用"解释。
        if context_fid and context_fid in self.groups:
            ids = self._from_group(context_fid, role)
            if ids and (role or re.search(r"(caption|fig|cite|cit|observ)", raw, re.I)):
                return Resolution(raw, "figure_group", 0.75, ids,
                                  f"{raw} 按 {context_fid} 上下文还原({role or 'caption+citation'})")

        # 5) "abstract" 类 id → 摘要块
        if "abstract" in raw.lower():
            bid = self._abstract_block()
            if bid:
                return Resolution(raw, "fuzzy", 0.65, [bid], "按 abstract 语义定位")

        # 6) 杂串里抽取 bNNNN
        for cand in EMBEDDED_ID_RE.findall(raw):
            cid = f"b{cand}"
            if cid in self.real_ids:
                return Resolution(raw, "fuzzy", 0.6, [cid], f"从杂串抽取 {cid}")

        return Resolution(raw, "unresolved", 0.0, [], "无法还原")


def dedupe(ids: list[str]) -> list[str]:
    return list(dict.fromkeys(i for i in ids if i))
