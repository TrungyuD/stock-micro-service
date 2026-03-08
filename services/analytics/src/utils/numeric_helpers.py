"""
numeric_helpers.py — Shared numeric casting and safe division utilities.
Used by valuation_calculator, proto_mappers, and screening_helpers.
"""
from typing import Any


def safe_float(v: Any) -> float | None:
    """Cast to float; return None if value is None or non-numeric."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def safe_int(v: Any) -> int | None:
    """Cast to int; return None if value is None or non-numeric."""
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    """Return numerator / denominator rounded to 4 dp, or None on zero/None."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def safe_float_or_zero(v: Any) -> float:
    """Cast to float with 0.0 fallback — used for proto fields that must be numeric."""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0
