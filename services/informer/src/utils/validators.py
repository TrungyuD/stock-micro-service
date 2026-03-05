"""
validators.py — Input validation helpers for symbols, OHLCV candles, and date ranges.
Regex allows dots so BRK.B / BF.B style symbols are accepted.
"""
import re
from datetime import date, datetime
from typing import Union

# Allows 1-10 uppercase letters or dots — covers BRK.B, BF.B, etc.
_SYMBOL_RE = re.compile(r'^[A-Z.]{1,10}$')

DateLike = Union[str, date, datetime]


def validate_symbol(symbol: str) -> bool:
    """
    Return True if `symbol` is a valid ticker (1-10 uppercase letters/dots).

    Examples:
        validate_symbol("AAPL")   → True
        validate_symbol("BRK.B")  → True
        validate_symbol("aapl")   → False
        validate_symbol("")       → False
    """
    if not isinstance(symbol, str):
        return False
    return bool(_SYMBOL_RE.match(symbol))


def validate_ohlcv(candle: dict) -> bool:
    """
    Return True when the candle dict passes basic OHLCV sanity checks.

    Rules:
      - low  ≤ open  ≤ high
      - low  ≤ close ≤ high
      - volume ≥ 0
      - All price fields must be present and > 0
    """
    try:
        o = float(candle["open"])
        h = float(candle["high"])
        l = float(candle["low"])
        c = float(candle["close"])
        v = int(candle["volume"])
    except (KeyError, TypeError, ValueError):
        return False

    if any(p <= 0 for p in (o, h, l, c)):
        return False
    if v < 0:
        return False
    if not (l <= o <= h):
        return False
    if not (l <= c <= h):
        return False
    return True


def validate_date_range(start: DateLike, end: DateLike) -> bool:
    """
    Return True when start < end and both are valid dates.

    Accepts str ('YYYY-MM-DD'), date, or datetime objects.
    """
    def _to_date(val: DateLike) -> date:
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()

    try:
        s = _to_date(start)
        e = _to_date(end)
    except (ValueError, TypeError):
        return False

    return s < e
