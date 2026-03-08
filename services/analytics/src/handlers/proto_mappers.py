"""
proto_mappers.py — Converts internal dicts to proto message objects.
All dict_to_*_proto helpers live here, keeping the main handler
free of proto construction details.
"""
from generated import analytics_pb2
from utils.numeric_helpers import safe_float_or_zero


def dict_to_valuation_proto(symbol: str, d: dict) -> analytics_pb2.ValuationMetrics:
    """Convert a valuation metrics dict (DB row or computed) to ValuationMetrics proto."""
    calculated_at = d.get("calculated_at")
    ts = (
        calculated_at.isoformat()
        if hasattr(calculated_at, "isoformat")
        else str(calculated_at or "")
    )
    return analytics_pb2.ValuationMetrics(
        symbol=symbol,
        trailing_pe=safe_float_or_zero(d.get("trailing_pe")),
        forward_pe=safe_float_or_zero(d.get("forward_pe")),
        current_eps=safe_float_or_zero(d.get("current_eps")),
        price_to_book=safe_float_or_zero(d.get("price_to_book")),
        book_value_per_share=safe_float_or_zero(d.get("book_value_per_share")),
        peg_ratio=safe_float_or_zero(d.get("peg_ratio")),
        earnings_growth_rate=safe_float_or_zero(d.get("earnings_growth_rate")),
        dividend_yield=safe_float_or_zero(d.get("dividend_yield")),
        payout_ratio=safe_float_or_zero(d.get("payout_ratio")),
        price_to_sales=safe_float_or_zero(d.get("price_to_sales")),
        ev_to_ebitda=safe_float_or_zero(d.get("ev_to_ebitda")),
        valuation_signal=str(d.get("valuation_signal") or ""),
        valuation_score=safe_float_or_zero(d.get("valuation_score")),
        calculated_at=ts,
    )


def dict_to_technicals_proto(
    symbol: str, d: dict, current_price: float, signals: dict | None = None
) -> analytics_pb2.TechnicalIndicators:
    """
    Convert a technical indicators dict to TechnicalIndicators proto.

    ``signals`` may be passed explicitly (e.g. freshly recomputed from a cached DB row
    via TechnicalCalculator.compute_signals); if omitted falls back to d['_signals'].
    """
    if signals is None:
        signals = d.get("_signals", {})

    rsi_val = safe_float_or_zero(d.get("rsi_14"))
    bb_upper = safe_float_or_zero(d.get("bb_upper"))
    bb_middle = safe_float_or_zero(d.get("bb_middle"))
    bb_lower = safe_float_or_zero(d.get("bb_lower"))

    band_width = bb_upper - bb_lower if bb_upper and bb_lower else 0.0
    percent_b = (
        (current_price - bb_lower) / (bb_upper - bb_lower)
        if bb_upper and bb_lower and (bb_upper - bb_lower) > 0
        else 0.0
    )

    calculated_at = d.get("time") or d.get("created_at")
    ts = (
        calculated_at.isoformat()
        if hasattr(calculated_at, "isoformat")
        else str(calculated_at or "")
    )

    return analytics_pb2.TechnicalIndicators(
        symbol=symbol,
        rsi=analytics_pb2.RSI(
            period=14,
            value=rsi_val,
            signal=signals.get("rsi_signal", "Neutral"),
        ),
        moving_averages=analytics_pb2.MovingAverages(
            sma_20=safe_float_or_zero(d.get("sma_20")),
            sma_50=safe_float_or_zero(d.get("sma_50")),
            sma_200=safe_float_or_zero(d.get("sma_200")),
            ema_20=safe_float_or_zero(d.get("ema_20")),
            ema_50=safe_float_or_zero(d.get("ema_50")),
            trend_signal=signals.get("trend_signal", "Neutral"),
        ),
        macd=analytics_pb2.MACDIndicator(
            macd_line=safe_float_or_zero(d.get("macd_line")),
            signal_line=safe_float_or_zero(d.get("macd_signal")),
            histogram=safe_float_or_zero(d.get("macd_histogram")),
            signal=signals.get("macd_signal", "Neutral"),
        ),
        bollinger_bands=analytics_pb2.BollingerBands(
            upper_band=bb_upper,
            middle_band=bb_middle,
            lower_band=bb_lower,
            band_width=band_width,
            percent_b=percent_b,
        ),
        overall_signal=signals.get("overall_signal", "Neutral"),
        buy_signals=signals.get("buy_signals", 0),
        sell_signals=signals.get("sell_signals", 0),
        calculated_at=ts,
    )
