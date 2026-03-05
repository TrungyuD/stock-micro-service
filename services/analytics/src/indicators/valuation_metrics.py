"""
valuation_metrics.py — Compute P/E ratio, market cap, and other
fundamental valuation metrics. Full implementation in Phase 5.
"""
import logging

logger = logging.getLogger(__name__)


def compute_pe_ratio(price: float, eps: float) -> float | None:
    """
    Compute Price-to-Earnings ratio.
    Returns None if EPS is zero or negative.
    TODO Phase 5: integrate with Informer data via gRPC call
    """
    if eps <= 0:
        return None
    return round(price / eps, 4)


def compute_market_cap(price: float, shares_outstanding: float) -> float:
    """
    Compute market capitalisation (price × shares outstanding).
    TODO Phase 5: pull shares_outstanding from yfinance metadata
    """
    return price * shares_outstanding
