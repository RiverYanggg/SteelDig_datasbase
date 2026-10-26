"""数值归一化单元测试（不依赖数据库）。"""
from __future__ import annotations

import pytest
from steeldig_db.quantity import normalize, parse_quantity


@pytest.mark.parametrize("raw,unit,metric,kind,cvalue,unit_canon", [
    ("685", "MPa", "yield_strength", "numeric", 685.0, "MPa"),
    ("685", None, "yield_strength", "numeric", 685.0, "MPa"),      # 无单位按指标推断
    ("1 GPa", None, "yield_strength", "numeric", 1000.0, "MPa"),
    ("427–513 MPa", None, "yield_strength", "range", 470.0, "MPa"),
    ("~350-450", None, "yield_strength", "range", 400.0, "MPa"),
    ("up to 950 MPa", None, "yield_strength", "open_high", 950.0, "MPa"),
    ("not less than 40%", None, "elongation", "open_low", 40.0, "%"),
    ("56.9%", None, "elongation", "numeric", 56.9, "%"),
    ("1050 °C", None, "temperature", "numeric", 1323.15, "K"),
    ("2 h", None, "duration", "numeric", 7200.0, "s"),
    ("3.5 μm", None, "grain_size", "numeric", 3.5, "μm"),
    ("5.08%", None, "volume_fraction", "numeric", 5.08, "%"),
])
def test_normalize(raw, unit, metric, kind, cvalue, unit_canon):
    r = normalize(raw, unit, metric)
    assert r["value_kind"] == kind
    assert r["unit_canonical"] == unit_canon
    if cvalue is None:
        assert r["value_canonical"] is None
    else:
        assert r["value_canonical"] == pytest.approx(cvalue, rel=1e-6)


@pytest.mark.parametrize("raw,metric", [
    ("increases with Al content in the range 2–11 wt.% Al", "yield_strength"),
    ("room temperature", "temperature"),
    ("Bal.", "weight_percent"),
    ("not reported", "yield_strength"),
    ("", "yield_strength"),
])
def test_non_numeric_is_not_fabricated(raw, metric):
    """不能把自由文本硬解析成数值——宁可标定性。"""
    r = normalize(raw, None, metric)
    assert r["value_canonical"] is None
    assert r["value_kind"] in ("qualitative", "missing")


def test_range_bounds_are_ordered():
    q = parse_quantity("513–427 MPa")
    assert q.kind == "range"
    assert q.low == 427 and q.high == 513


def test_scientific_notation():
    q = parse_quantity("1 × 10^-3 s^-1")
    assert q.mid == pytest.approx(0.001)
