"""
screening_helpers.py — Filter and sort functions for the ScreenStocks RPC.
Keeps _passes_*_criteria logic separate from the main handler.

proto3 convention: numeric criteria fields default to 0.0 when not set by the
caller.  We treat 0.0 as "no filter applied" throughout this module because
real PE/PEG/dividend values of exactly 0.0 are meaningless as filter bounds.

NOTE: Uses duck-typed `criteria` parameter (Any) so this module works with both
legacy analytics_pb2.ScreeningCriteria and v1 screening_pb2.ScreeningCriteria
without importing either — avoiding protobuf descriptor pool collisions.
"""
from typing import Any

from utils.numeric_helpers import safe_float_or_zero


def passes_valuation_criteria(row: dict, c: Any) -> bool:
    """
    Return True if the valuation row satisfies PE/PEG/dividend criteria.

    proto3 zero-value convention:
      - min_* == 0.0  →  no lower-bound filter (skip check)
      - max_* == 0.0  →  no upper-bound filter (skip check)
    A stock with an actual 0.0 PE is treated as unfiltered (no valid PE).
    """
    pe = safe_float_or_zero(row.get("trailing_pe"))
    peg = safe_float_or_zero(row.get("peg_ratio"))
    div = safe_float_or_zero(row.get("dividend_yield"))

    # min_pe != 0 means caller wants a lower-bound PE filter
    if c.min_pe != 0 and pe != 0 and pe < c.min_pe:
        return False
    if c.max_pe != 0 and pe != 0 and pe > c.max_pe:
        return False
    if c.min_peg != 0 and peg != 0 and peg < c.min_peg:
        return False
    if c.max_peg != 0 and peg != 0 and peg > c.max_peg:
        return False
    if c.min_dividend_yield != 0 and div != 0 and div < c.min_dividend_yield:
        return False
    if c.max_dividend_yield != 0 and div != 0 and div > c.max_dividend_yield:
        return False
    return True


def passes_technical_criteria(ind_row: dict | None, c: Any) -> bool:
    """
    Return True if the indicator row satisfies RSI / trend criteria.
    Missing indicator data is treated as a pass (don't filter out uncalculated stocks).
    """
    if not ind_row:
        return True  # no data → don't filter out

    rsi = safe_float_or_zero(ind_row.get("rsi_14"))
    # Keep only RSI < 30 stocks when oversold filter is active
    if c.rsi_oversold and rsi != 0 and rsi >= 30:
        return False
    # Keep only RSI > 70 stocks when overbought filter is active
    if c.rsi_overbought and rsi != 0 and rsi <= 70:
        return False

    if c.trend_direction:
        signals = ind_row.get("_signals", {})
        if signals.get("trend_signal", "Neutral") != c.trend_direction:
            return False
    return True


def compute_match_score(val_row: dict, ind_row: dict | None, c: Any) -> float:
    """Simple 0-100 match score: invert valuation_score (lower score = better value)."""
    val_score = safe_float_or_zero(val_row.get("valuation_score") or 50.0)
    return round(100.0 - val_score, 2)


def sort_screened(
    stocks: list[Any], sort_by: str
) -> list[Any]:
    """Sort a list of ScreenedStock protos by the requested field."""
    if sort_by == "pe_ratio":
        return sorted(stocks, key=lambda s: s.valuation.trailing_pe or 999)
    if sort_by == "dividend_yield":
        return sorted(stocks, key=lambda s: s.valuation.dividend_yield, reverse=True)
    # Default: sort by match_score descending
    return sorted(stocks, key=lambda s: s.match_score, reverse=True)
