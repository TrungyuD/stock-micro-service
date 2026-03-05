"""
recommendation_helpers.py — Combines valuation + technical signals into a
final recommendation string and builds the rationale text for StockAnalysis.
"""


def combine_recommendation(
    val: dict | None, tech: dict | None
) -> tuple[str, float]:
    """
    Combine valuation signal and technical overall_signal into a final recommendation.
    Returns (recommendation_str, confidence_0_to_100).
    """
    val_signal = (val or {}).get("valuation_signal", "Fair Value")
    tech_signals = (tech or {}).get("_signals", {})
    overall = tech_signals.get("overall_signal", "Neutral")
    buy = tech_signals.get("buy_signals", 0)
    sell = tech_signals.get("sell_signals", 0)

    # Map valuation signal to score delta
    val_delta = {"Undervalued": 1, "Fair Value": 0, "Overvalued": -1}.get(val_signal, 0)

    # Map tech signal to score delta
    tech_score_map = {
        "Strong Buy": 2, "Buy": 1, "Neutral": 0, "Sell": -1, "Strong Sell": -2,
    }
    tech_delta = tech_score_map.get(overall, 0)
    combined = val_delta + tech_delta

    if combined >= 3:
        rec = "Strong Buy"
    elif combined >= 1:
        rec = "Buy"
    elif combined <= -3:
        rec = "Strong Sell"
    elif combined <= -1:
        rec = "Sell"
    else:
        rec = "Neutral"

    total_signals = max(buy + sell, 1)
    confidence = round(
        min(100.0, (abs(combined) / 4.0) * 100.0 + (buy / total_signals) * 20.0), 1
    )
    return rec, confidence


def build_rationale(
    symbol: str, val: dict | None, tech: dict | None, recommendation: str
) -> str:
    """Build a human-readable rationale string from valuation and technical data."""
    parts = [f"{symbol} — {recommendation}."]
    v = val or {}
    t = tech or {}
    signals = t.get("_signals", {})

    if v.get("trailing_pe"):
        parts.append(f"P/E: {v['trailing_pe']:.1f}")
    if v.get("valuation_signal"):
        parts.append(f"Valuation: {v['valuation_signal']}")
    if t.get("rsi_14"):
        parts.append(f"RSI(14): {t['rsi_14']:.1f} ({signals.get('rsi_signal', '')})")
    if signals.get("trend_signal"):
        parts.append(f"Trend: {signals['trend_signal']}")

    return " | ".join(parts)
