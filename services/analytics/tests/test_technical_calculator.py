"""Tests for calculators/technical_calculator.py — RSI, SMA, EMA, MACD, Bollinger."""
from calculators.technical_calculator import TechnicalCalculator


class TestTechnicalCalculatorCompute:
    """TechnicalCalculator.compute() returns indicators from bar dicts."""

    def test_all_indicators_present(self, sample_bars_300):
        calc = TechnicalCalculator()
        result = calc.compute(sample_bars_300)

        assert result["rsi_14"] is not None
        assert result["sma_20"] is not None
        assert result["sma_50"] is not None
        assert result["sma_200"] is not None
        assert result["ema_20"] is not None
        assert result["ema_50"] is not None
        assert result["macd_line"] is not None
        assert result["macd_signal"] is not None
        assert result["macd_histogram"] is not None
        assert result["bb_upper"] is not None
        assert result["bb_middle"] is not None
        assert result["bb_lower"] is not None

    def test_rsi_in_valid_range(self, sample_bars_300):
        calc = TechnicalCalculator()
        result = calc.compute(sample_bars_300)
        assert 0 <= result["rsi_14"] <= 100

    def test_bollinger_bands_order(self, sample_bars_300):
        calc = TechnicalCalculator()
        result = calc.compute(sample_bars_300)
        assert result["bb_lower"] < result["bb_middle"] < result["bb_upper"]

    def test_insufficient_data(self, sample_bars_short):
        calc = TechnicalCalculator()
        result = calc.compute(sample_bars_short)

        assert result["rsi_14"] is None
        assert result["sma_50"] is None
        assert result["sma_200"] is None
        assert result["macd_line"] is None
        assert result["bb_upper"] is None

    def test_sma20_available_with_20_bars(self):
        bars = [{"close": 100 + i} for i in range(20)]
        calc = TechnicalCalculator()
        result = calc.compute(bars)
        assert result["sma_20"] is not None
        assert result["sma_50"] is None


class TestTechnicalCalculatorSignals:
    """_derive_signals and compute_signals."""

    def test_bullish_signals(self, sample_bars_300):
        calc = TechnicalCalculator()
        result = calc.compute(sample_bars_300)
        signals = result["_signals"]
        # Upward trending data should produce bullish signals
        assert signals["overall_signal"] in ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]
        assert isinstance(signals["buy_signals"], int)
        assert isinstance(signals["sell_signals"], int)

    def test_compute_signals_from_indicator_row(self):
        calc = TechnicalCalculator()
        ind = {"rsi_14": 25, "sma_50": 150, "sma_200": 140, "macd_histogram": 0.5}
        signals = calc.compute_signals(ind, current_price=160)
        assert signals["rsi_signal"] == "Oversold"
        assert signals["trend_signal"] == "Bullish"
        assert signals["macd_signal"] == "Bullish"
        assert signals["overall_signal"] == "Strong Buy"

    def test_bearish_signals(self):
        calc = TechnicalCalculator()
        ind = {"rsi_14": 75, "sma_50": 140, "sma_200": 150, "macd_histogram": -0.5}
        signals = calc.compute_signals(ind, current_price=130)
        assert signals["rsi_signal"] == "Overbought"
        assert signals["trend_signal"] == "Bearish"
        assert signals["macd_signal"] == "Bearish"
        assert signals["overall_signal"] == "Strong Sell"

    def test_neutral_when_no_data(self):
        calc = TechnicalCalculator()
        signals = calc.compute_signals({}, current_price=0)
        assert signals["overall_signal"] == "Neutral"
