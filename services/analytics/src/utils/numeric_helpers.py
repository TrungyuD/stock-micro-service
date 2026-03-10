"""
numeric_helpers.py — Shared numeric casting and safe division utilities.
Used by valuation_calculator, proto_mappers, screening_helpers, and repositories.
"""
from typing import Any

import numpy as np


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


def to_native(v: Any) -> Any:
    """Convert numpy scalars to native Python types for psycopg2 compatibility."""
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v
