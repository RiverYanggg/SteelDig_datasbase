"""自由文本数值归一化。

材料文献里的性能值几乎都是自由字符串::

    "427–513 MPa"   "~350-450"      "up to 950 MPa"
    "3.5 μm"        "56.9%"         "1050 °C"
    "1 × 10^-3 s^-1"                "not less than 40%"

如果直接按字符串入库，就只能 LIKE，无法做"屈服强度 > 600 MPa"这类查询。
本模块把它们解析为 (kind, low, high, unit) 并换算到统一的规范单位：

    应力 → MPa      尺寸 → μm      温度 → K      分数 → %      时间 → s
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

# ---------------------------------------------------------------------------
# 文本清洗
# ---------------------------------------------------------------------------
_TRANS = str.maketrans({
    "−": "-", "–": "-", "—": "-", "‒": "-", "―": "-", "～": "-", "~": "-",
    "％": "%", "µ": "μ", "μ": "μ", "·": "·", "×": "×",
    "\u00a0": " ", "\u2009": " ", "\u202f": " ",
    "≦": "≤", "≧": "≥", "＜": "<", "＞": ">",
})

_MISSING = {
    "", "-", "n/a", "na", "n.a.", "nr", "not reported", "none", "null", "unknown",
    "not available", "not measured", "not specified", "not given", "未报道", "无", "--",
}

# 限定词：不是数值本身的一部分，但会改变语义
_QUALIFIERS: list[tuple[str, re.Pattern]] = [
    ("not_less_than", re.compile(r"^(?:not\s+less\s+than|no\s+less\s+than|at\s+least|minimum\s+of|≥|>=|>)\s*", re.I)),
    ("not_more_than", re.compile(r"^(?:not\s+more\s+than|at\s+most|maximum\s+of|≤|<=|<)\s*", re.I)),
    ("up_to", re.compile(r"^(?:up\s+to|as\s+high\s+as|reaches?|until)\s*", re.I)),
    ("approximate", re.compile(r"^(?:about|approx\.?|approximately|around|roughly|ca\.|circa|~|≈|∼)\s*", re.I)),
    ("exact", re.compile(r"^(?:exactly|precisely)\s*", re.I)),
]

_FILLER_WORDS = {
    "mpa", "gpa", "kpa", "pa", "kgf", "psi", "ksi",
    "um", "μm", "nm", "mm", "cm", "m", "k", "c", "°c", "℃", "f", "°f",
    "s", "sec", "secs", "second", "seconds", "min", "mins", "minute", "minutes",
    "h", "hr", "hrs", "hour", "hours", "day", "days",
    "pct", "percent", "percentage", "vol", "wt", "at",
    "j", "kj", "mj", "ev", "joules", "energy",
    "hv", "hrc", "hrb", "hb", "hv0.1", "hv1", "hv5", "hv10", "hv30",
    "of", "the", "at", "in", "on", "to", "and", "or", "for", "with",
    "room", "temperature", "rt", "ambient", "value", "values", "reported", "measured",
    "engineering", "true", "nominal", "average", "approximately", "about",
    "degrees", "degree", "kelvin", "celsius", "per", "ratio",
}

_NUM_RE = re.compile(
    r"""(?P<mant>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"""
    r"""(?:\s*(?:×|x|\*)\s*10\s*(?:\^|\*\*)?\s*(?P<exp>[-+]?\d+))?"""
)
_RANGE_SEP = re.compile(r"^\s*(?:-|to|至|/|\.\.\.?)\s*$", re.I)

# ---------------------------------------------------------------------------
# 单位表：(维度, 归一化到该维度基准单位的 scale, offset)
# ---------------------------------------------------------------------------
UNITS: dict[str, tuple[str, float, float]] = {
    # --- 应力/压强 → MPa
    "pa": ("stress", 1e-6, 0.0), "kpa": ("stress", 1e-3, 0.0), "mpa": ("stress", 1.0, 0.0),
    "gpa": ("stress", 1e3, 0.0), "kgf/mm2": ("stress", 9.80665, 0.0),
    "kg/mm2": ("stress", 9.80665, 0.0), "n/mm2": ("stress", 1.0, 0.0),
    "psi": ("stress", 0.00689476, 0.0), "ksi": ("stress", 6.89476, 0.0),
    # --- 长度 → μm
    "nm": ("length", 1e-3, 0.0), "μm": ("length", 1.0, 0.0), "um": ("length", 1.0, 0.0),
    "mm": ("length", 1e3, 0.0), "cm": ("length", 1e4, 0.0), "m": ("length", 1e6, 0.0),
    "å": ("length", 1e-4, 0.0),
    # --- 温度 → K
    "k": ("temperature", 1.0, 0.0), "°c": ("temperature", 1.0, 273.15),
    "℃": ("temperature", 1.0, 273.15), "c": ("temperature", 1.0, 273.15),
    "°f": ("temperature", 5 / 9, 255.372222),
    # --- 分数 → %
    "%": ("fraction", 1.0, 0.0), "pct": ("fraction", 1.0, 0.0),
    "percent": ("fraction", 1.0, 0.0), "at.%": ("fraction", 1.0, 0.0),
    "vol.%": ("fraction", 1.0, 0.0), "wt.%": ("fraction", 1.0, 0.0),
    # --- 能量 → J
    "j": ("energy", 1.0, 0.0), "kj": ("energy", 1e3, 0.0), "mj": ("energy", 1e-3, 0.0),
    "ev": ("energy", 1.602176634e-19, 0.0),
    # --- 时间 → s
    "s": ("time", 1.0, 0.0), "ms": ("time", 1e-3, 0.0), "min": ("time", 60.0, 0.0),
    "h": ("time", 3600.0, 0.0), "hr": ("time", 3600.0, 0.0), "day": ("time", 86400.0, 0.0),
    # --- 密度 → g/cm3
    "g/cm3": ("density", 1.0, 0.0), "g·cm-3": ("density", 1.0, 0.0),
    "kg/m3": ("density", 1e-3, 0.0), "mg/m3": ("density", 1e-6, 0.0),
    # --- 无量纲硬度标尺（不做换算，仅标注）
    "hv": ("hardness_hv", 1.0, 0.0), "hv0.1": ("hardness_hv", 1.0, 0.0),
    "hv0.2": ("hardness_hv", 1.0, 0.0), "hv0.5": ("hardness_hv", 1.0, 0.0),
    "hv1": ("hardness_hv", 1.0, 0.0), "hv5": ("hardness_hv", 1.0, 0.0),
    "hv10": ("hardness_hv", 1.0, 0.0), "hv30": ("hardness_hv", 1.0, 0.0),
    "hrc": ("hardness_hrc", 1.0, 0.0),
    "hrb": ("hardness_hrb", 1.0, 0.0), "hb": ("hardness_hb", 1.0, 0.0),
}

# 展示用符号（匹配用小写 key，存储用标准写法）
UNIT_SYMBOL = {
    "pa": "Pa", "kpa": "kPa", "mpa": "MPa", "gpa": "GPa",
    "kgf/mm2": "kgf/mm²", "kg/mm2": "kg/mm²", "n/mm2": "N/mm²",
    "psi": "psi", "ksi": "ksi",
    "nm": "nm", "μm": "μm", "um": "μm", "mm": "mm", "cm": "cm", "m": "m", "å": "Å",
    "k": "K", "°c": "°C", "℃": "°C", "c": "°C", "°f": "°F",
    "%": "%", "pct": "%", "percent": "%",
    "j": "J", "kj": "kJ", "mj": "mJ", "ev": "eV",
    "s": "s", "ms": "ms", "min": "min", "h": "h", "hr": "h", "day": "day",
    "g/cm3": "g/cm³", "kg/m3": "kg/m³",
    "hv": "HV", "hrc": "HRC", "hrb": "HRB", "hb": "HB",
}

CANONICAL_UNIT = {
    "stress": "MPa", "length": "μm", "temperature": "K",
    "fraction": "%", "energy": "J", "time": "s", "density": "g/cm3",
}

# 指标名 → 维度。
# 用"按下划线/驼峰切词后的精确词匹配"，而不是子串正则——
# 否则 "du-ratio-n" 会被误判成 ratio，"grain_size" 又会被 size 抢先命中。
_DIMENSION_WORDS: dict[str, set[str]] = {
    "length": {"grain", "grain_size", "size", "diameter", "thickness", "width", "length",
               "spacing", "particle", "precipitate", "inclusion", "depth", "height",
               "radius", "distance", "scale", "wavelength", "roughness", "film", "layer"},
    "stress": {"strength", "stress", "modulus", "proof", "uts", "ys", "hardness_mpa",
               "fatigue_limit", "pressure"},
    "fraction": {"elongation", "reduction", "fraction", "fraction_pct", "percentage",
                 "pct", "ductility", "ratio", "area", "volume"},
    "temperature": {"temperature", "temp", "austenitization", "homogenization"},
    "density": {"density"},
    "energy": {"energy", "toughness", "absorbed", "impact_energy"},
    "time": {"duration", "time", "holding", "aging", "annealing_time"},
    "hardness": {"hardness"},
}
# 优先检查顺序：具体维度优先于 length（size 太泛）
_DIM_ORDER = ("temperature", "density", "hardness", "stress", "fraction", "energy",
              "time", "length")


def _words(name: str) -> list[str]:
    parts = re.split(r"[^a-zA-Z0-9]+|(?<=[a-z])(?=[A-Z])", name or "")
    return [p.lower() for p in parts if p]



@dataclass
class Quantity:
    raw: str
    kind: str            # numeric | range | open_low | open_high | qualitative | missing
    low: float | None = None
    high: float | None = None
    mid: float | None = None
    unit: str | None = None
    qualifier: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, (int, float)):
        return str(text)
    return str(text).translate(_TRANS).strip()


def _match_unit(token: str) -> str | None:
    """在候选片段里找最长的已知单位写法。"""
    t = token.lower().strip().strip("()[],;")
    t = re.sub(r"\s+", "", t)
    if not t:
        return None
    best: str | None = None
    for key in sorted(UNITS, key=len, reverse=True):
        if t == key or t.endswith(key) or t.startswith(key):
            # 允许 "mpa(calculated)" "mpa," 这类噪声，但不允许 "mpa/m"
            if best is None or len(key) > len(best):
                best = key
    return best


def _dimension_for(metric: str | None, section: str | None = None) -> str | None:
    if not metric:
        return None
    words = _words(metric)
    for dim in _DIM_ORDER:
        if any(w in _DIMENSION_WORDS[dim] for w in words):
            return dim
    return None


def parse_quantity(raw: Any, unit_hint: str | None = None) -> Quantity:
    """解析单个数值字段。无法解析时返回 qualitative，保留原文，绝不臆造数值。"""
    s = clean(raw)
    if s.lower() in _MISSING:
        return Quantity(raw=s, kind="missing")

    # 欧洲写法 "1 295 MPa"：空格做千分位，先合并再解析
    s = re.sub(r"(?<=\d)\s+(?=\d{3}(?!\d))", "", s)

    qualifier: str | None = None
    for name, pat in _QUALIFIERS:
        m = pat.match(s)
        if m:
            qualifier = name
            s = s[m.end():].strip()
            break

    nums: list[tuple[int, int, float]] = []
    for m in _NUM_RE.finditer(s):
        mant = float(m.group("mant").replace(",", ""))
        if m.group("exp"):
            mant *= 10 ** int(m.group("exp"))
        nums.append((m.start(), m.end(), mant))

    if not nums:
        return Quantity(raw=clean(raw), kind="qualitative", qualifier=qualifier)

    unit = _match_unit(unit_hint) if unit_hint else None
    if unit is None:
        unit = _match_unit(s[nums[-1][1]:]) or _match_unit(s)

    # 判断是否为区间：恰好两个数字，且二者之间只有连接符
    kind = "numeric"
    low = high = mid = None
    if len(nums) >= 2:
        gap = s[nums[0][1]:nums[1][0]]
        if _RANGE_SEP.match(gap):
            kind, low, high = "range", nums[0][2], nums[1][2]
            if low is not None and high is not None and low > high:
                low, high = high, low
            mid = (low + high) / 2 if None not in (low, high) else None
        else:
            content = s
            nums_ = nums
            mid = nums_[0][2]
            low = high = mid
    else:
        mid = nums[0][2]
        low = high = mid

    if qualifier in ("up_to", "not_more_than") and kind == "numeric":
        kind, low, high = "open_high", None, mid
    elif qualifier == "not_less_than" and kind == "numeric":
        kind, low, high = "open_low", mid, None

    # 噪声过滤：剩余文本里如果还有多个实词，说明这不是纯数值（如
    # "increases with Al content in the range 2-11 wt.%"），按定性处理
    residue = _NUM_RE.sub(" ", s).lower()
    residue = re.sub(r"[%°·/^+\-.,;:()\[\]]", " ", residue)
    words = [w for w in re.findall(r"[a-zμ]{2,}", residue) if w not in _FILLER_WORDS]
    if len(words) >= 2:
        return Quantity(raw=clean(raw), kind="qualitative", qualifier=qualifier)

    return Quantity(raw=clean(raw), kind=kind, low=low, high=high, mid=mid,
                    unit=unit, qualifier=qualifier)


def canonicalize(q: Quantity, metric: str | None, section: str | None = None) -> dict[str, Any]:
    """把 Quantity 换算到规范单位，返回可直接写库的字段字典。"""
    dim = _dimension_for(metric, section)
    unit_raw = q.unit
    unit_canon = UNIT_SYMBOL.get(unit_raw or "", unit_raw)
    value_c = q.mid
    low_c, high_c = q.low, q.high

    if dim is None or q.kind in ("qualitative", "missing"):
        return {
            "value_kind": "qualitative" if q.kind == "qualitative" else q.kind,
            "value_num": q.mid, "value_low": q.low, "value_high": q.high,
            "value_unit": unit_raw, "unit_canonical": unit_canon,
            "value_canonical": None, "value_low_canonical": None,
            "value_high_canonical": None,
        }

    if dim == "hardness":
        meta_h = UNITS.get(unit_raw or "")
        if meta_h and meta_h[0] == "stress":
            # 以应力单位报告的硬度（如 8897 MPa ≈ 900 HV）：换算到 MPa 并标注
            conv = lambda v: None if v is None else round(v * meta_h[1] + meta_h[2], 6)
            return {
                "value_kind": q.kind,
                "value_num": q.mid, "value_low": q.low, "value_high": q.high,
                "value_unit": unit_raw, "unit_canonical": "MPa",
                "value_canonical": conv(q.mid), "value_low_canonical": conv(q.low),
                "value_high_canonical": conv(q.high),
            }
        # 硬度标尺不可互转（HV/HRC/HB 之间是非线性的），只统一记录数值与标尺名
        return {
            "value_kind": q.kind,
            "value_num": q.mid, "value_low": q.low, "value_high": q.high,
            "value_unit": unit_raw, "unit_canonical": (unit_raw or "").upper() or None,
            "value_canonical": q.mid, "value_low_canonical": q.low,
            "value_high_canonical": q.high,
        }

    target = CANONICAL_UNIT.get(dim)
    meta = UNITS.get(unit_raw or "")
    if meta and meta[0] == dim:
        scale, offset = meta[1], meta[2]
        conv = lambda v: None if v is None else round(v * scale + offset, 6)
        value_c, low_c, high_c = conv(q.mid), conv(q.low), conv(q.high)
        unit_canon = target
    elif unit_raw is None:
        # 无单位时按维度的默认单位解释（文献里 "685" + 指标 yield_strength 极常见）
        unit_canon = target
    else:
        # 单位与指标维度不匹配（如"硬度 HV300"），保留原值不做换算
        value_c, low_c, high_c = q.mid, q.low, q.high
        unit_canon = UNIT_SYMBOL.get(unit_raw or "", unit_raw)

    return {
        "value_kind": q.kind,
        "value_num": q.mid, "value_low": q.low, "value_high": q.high,
        "value_unit": unit_raw, "unit_canonical": unit_canon,
        "value_canonical": value_c, "value_low_canonical": low_c,
        "value_high_canonical": high_c,
    }


def normalize(raw: Any, unit_hint: str | None, metric: str | None,
              section: str | None = None) -> dict[str, Any]:
    """一步到位：文本 → 解析 → 单位归一化。"""
    q = parse_quantity(raw, unit_hint)
    out = canonicalize(q, metric, section)
    out["qualifier"] = q.qualifier
    out["value_raw"] = q.raw
    return out
