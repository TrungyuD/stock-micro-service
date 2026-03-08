"""Tests for handlers/recommendation_helpers.py — combine signals + build rationale."""
from handlers.recommendation_helpers import build_rationale, combine_recommendation


class TestCombineRecommendation:
    """combine_recommendation merges valuation + technical signals."""

    def test_strong_buy(self):
        val = {"valuation_signal": "Undervalued"}
        tech = {"_signals": {"overall_signal": "Strong Buy", "buy_signals": 3, "sell_signals": 0}}
        rec, conf = combine_recommendation(val, tech)
        assert rec == "Strong Buy"
        assert conf > 0

    def test_strong_sell(self):
        val = {"valuation_signal": "Overvalued"}
        tech = {"_signals": {"overall_signal": "Strong Sell", "buy_signals": 0, "sell_signals": 3}}
        rec, conf = combine_recommendation(val, tech)
        assert rec == "Strong Sell"

    def test_neutral(self):
        val = {"valuation_signal": "Fair Value"}
        tech = {"_signals": {"overall_signal": "Neutral", "buy_signals": 0, "sell_signals": 0}}
        rec, conf = combine_recommendation(val, tech)
        assert rec == "Neutral"

    def test_none_inputs(self):
        rec, conf = combine_recommendation(None, None)
        assert rec == "Neutral"
        assert conf >= 0

    def test_mixed_signals_buy(self):
        val = {"valuation_signal": "Undervalued"}
        tech = {"_signals": {"overall_signal": "Neutral", "buy_signals": 1, "sell_signals": 1}}
        rec, conf = combine_recommendation(val, tech)
        assert rec == "Buy"


class TestBuildRationale:
    """build_rationale produces human-readable summary."""

    def test_full_data(self):
        val = {"trailing_pe": 23.4, "valuation_signal": "Fair Value"}
        tech = {"rsi_14": 55.0, "_signals": {"rsi_signal": "Neutral", "trend_signal": "Bullish"}}
        text = build_rationale("AAPL", val, tech, "Buy")
        assert "AAPL" in text
        assert "Buy" in text
        assert "P/E" in text
        assert "RSI" in text

    def test_empty_data(self):
        text = build_rationale("TEST", None, None, "Neutral")
        assert "TEST" in text
        assert "Neutral" in text
