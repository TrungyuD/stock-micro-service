"""
technical-calculator.py — Computes RSI, SMA, EMA, MACD, and Bollinger Bands
from a list of OHLCV bar dicts using pure numpy (no external TA library required).

All methods accept a list[dict] with at least a 'close' key and return a dict
of indicator values for the most-recent bar.  Returns None for any indicator
when there is insufficient data.
"""
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Minimum bar counts required before each indicator is meaningful
_MIN_RSI = 15       # 14-period + 1 seed bar
_MIN_SMA200 = 200
_MIN_SMA50 = 50
_MIN_SMA20 = 20
_MIN_EMA50 = 50
_MIN_EMA20 = 20
_MIN_MACD = 35      # EMA26 + EMA9 signal
_MIN_BB = 20        # Bollinger Bands 20-period


def _closes(bars: list[dict]) -> np.ndarray:
    """Extract close prices as a float64 numpy array (oldest-first)."""
    return np.array([float(b["close"]) for b in bars], dtype=np.float64)


def _ema(series: np.ndarray, period: int) -> np.ndarray:
    """
    Exponential Moving Average using Wilder-style seed (simple average of first `period` bars)
    followed by standard EMA multiplier k = 2 / (period + 1).
    Returns same-length array; leading values before the seed window are NaN.
    """
    result = np.full(len(series), np.nan)
    if len(series) < period:
        return result
    k = 2.0 / (period + 1)
    # Seed with SMA of first `period` values
    result[period - 1] = np.mean(series[:period])
    for i in range(period, len(series)):
        result[i] = series[i] * k + result[i - 1] * (1 - k)
    return result


def _sma(series: np.ndarray, period: int) -> np.ndarray:
    """Simple Moving Average — returns NaN for positions before `period`."""
    result = np.full(len(series), np.nan)
    for i in range(period - 1, len(series)):
        result[i] = np.mean(series[i - period + 1 : i + 1])
    return result


class TechnicalCalculator:
    """
    Stateless calculator — call compute() with a list of OHLCV bar dicts.
    Bars must be sorted oldest-first.  At least 300 bars recommended for SMA-200.
    """

    def compute(self, bars: list[dict]) -> dict[str, Any]:
        """
        Compute all technical indicators from the provided price history.

        Returns a flat dict with keys matching the `indicators` table columns plus
        derived signal fields used by the gRPC handler.
        """
        closes = _closes(bars)
        n = len(closes)
        result: dict[str, Any] = {}

        # ── RSI 14 ────────────────────────────────────────────────────────────
        result["rsi_14"] = self._rsi(closes, 14) if n >= _MIN_RSI else None

        # ── Simple Moving Averages ─────────────────────────────────────────────
        result["sma_20"] = float(np.mean(closes[-20:])) if n >= _MIN_SMA20 else None
        result["sma_50"] = float(np.mean(closes[-50:])) if n >= _MIN_SMA50 else None
        result["sma_200"] = float(np.mean(closes[-200:])) if n >= _MIN_SMA200 else None

        # ── Exponential Moving Averages ────────────────────────────────────────
        result["ema_20"] = self._last_ema(closes, 20) if n >= _MIN_EMA20 else None
        result["ema_50"] = self._last_ema(closes, 50) if n >= _MIN_EMA50 else None

        # ── MACD (12 / 26 / 9) ────────────────────────────────────────────────
        if n >= _MIN_MACD:
            macd_line, signal_line, histogram = self._macd(closes)
            result["macd_line"] = macd_line
            result["macd_signal"] = signal_line
            result["macd_histogram"] = histogram
        else:
            result["macd_line"] = result["macd_signal"] = result["macd_histogram"] = None

        # ── Bollinger Bands (20 / 2σ) ─────────────────────────────────────────
        if n >= _MIN_BB:
            bb_upper, bb_middle, bb_lower = self._bollinger(closes, 20, 2.0)
            result["bb_upper"] = bb_upper
            result["bb_middle"] = bb_middle
            result["bb_lower"] = bb_lower
        else:
            result["bb_upper"] = result["bb_middle"] = result["bb_lower"] = None

        # ── Derived signals (used by handler, not persisted in indicators table) ──
        result["_signals"] = self._derive_signals(closes[-1] if n else 0.0, result)

        return result

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _rsi(self, closes: np.ndarray, period: int = 14) -> float:
        """
        Wilder's RSI using exponential smoothing (true Wilder method).
        RS = avg_gain / avg_loss over `period` bars.
        """
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Seed averages from first `period` deltas
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Wilder smoothing for remaining deltas
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100.0 - (100.0 / (1.0 + rs)), 4)

    def _last_ema(self, closes: np.ndarray, period: int) -> float:
        """Return the last (most-recent) EMA value for the given period."""
        arr = _ema(closes, period)
        last = arr[-1]
        return round(float(last), 4) if not np.isnan(last) else None

    def _macd(self, closes: np.ndarray) -> tuple[float, float, float]:
        """
        MACD = EMA12 - EMA26
        Signal = EMA9 of MACD line
        Histogram = MACD - Signal
        """
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        macd_arr = ema12 - ema26

        # EMA9 of the MACD line (only valid positions)
        valid_start = 25  # EMA26 needs 26 bars → first valid index is 25
        macd_valid = macd_arr[valid_start:]
        signal_arr_valid = _ema(macd_valid, 9)
        signal_full = np.full(len(closes), np.nan)
        signal_full[valid_start:] = signal_arr_valid

        macd_last = float(macd_arr[-1])
        signal_last = float(signal_full[-1])
        histogram_last = macd_last - signal_last

        return round(macd_last, 4), round(signal_last, 4), round(histogram_last, 4)

    def _bollinger(
        self, closes: np.ndarray, period: int = 20, num_std: float = 2.0
    ) -> tuple[float, float, float]:
        """
        Bollinger Bands:
          middle = SMA20 of last `period` closes
          upper  = middle + num_std * stddev
          lower  = middle - num_std * stddev
        """
        window = closes[-period:]
        middle = float(np.mean(window))
        std = float(np.std(window, ddof=1))  # sample std dev
        upper = middle + num_std * std
        lower = middle - num_std * std
        return round(upper, 4), round(middle, 4), round(lower, 4)

    def compute_signals(self, indicator_row: dict, current_price: float = 0.0) -> dict:
        """
        Derive trading signals from a stored indicator row (e.g. fetched from DB).

        DB rows only carry numeric values — _signals is not persisted.  This method
        re-derives them so cached rows return correct signal strings rather than
        defaulting to "Neutral"/0.

        Rules mirror _derive_signals():
          RSI  < 30            → "Oversold"  (buy signal)
          RSI  > 70            → "Overbought" (sell signal)
          price > SMA50 > SMA200 → "Bullish" trend
          price < SMA50 < SMA200 → "Bearish" trend
          MACD histogram > 0   → "Bullish" MACD
        """
        return self._derive_signals(current_price, indicator_row)

    def _derive_signals(self, current_price: float, ind: dict) -> dict:
        """
        Derive trading signals from computed indicators.
        Returns a dict with rsi_signal, trend_signal, macd_signal, overall_signal,
        buy_signals, sell_signals for use in proto responses.
        """
        buy = 0
        sell = 0

        # RSI signal
        rsi = ind.get("rsi_14")
        if rsi is not None:
            if rsi < 30:
                rsi_signal = "Oversold"
                buy += 1
            elif rsi > 70:
                rsi_signal = "Overbought"
                sell += 1
            else:
                rsi_signal = "Neutral"
        else:
            rsi_signal = "Neutral"

        # Trend signal (price vs SMA200 and SMA50)
        sma50 = ind.get("sma_50")
        sma200 = ind.get("sma_200")
        if sma50 is not None and sma200 is not None and current_price > 0:
            if current_price > sma50 and sma50 > sma200:
                trend_signal = "Bullish"
                buy += 1
            elif current_price < sma50 and sma50 < sma200:
                trend_signal = "Bearish"
                sell += 1
            else:
                trend_signal = "Neutral"
        else:
            trend_signal = "Neutral"

        # MACD signal
        histogram = ind.get("macd_histogram")
        if histogram is not None:
            if histogram > 0:
                macd_signal = "Bullish"
                buy += 1
            else:
                macd_signal = "Bearish"
                sell += 1
        else:
            macd_signal = "Neutral"

        # Overall signal based on buy vs sell score
        net = buy - sell
        if net >= 2:
            overall = "Strong Buy"
        elif net == 1:
            overall = "Buy"
        elif net == 0:
            overall = "Neutral"
        elif net == -1:
            overall = "Sell"
        else:
            overall = "Strong Sell"

        return {
            "rsi_signal": rsi_signal,
            "trend_signal": trend_signal,
            "macd_signal": macd_signal,
            "overall_signal": overall,
            "buy_signals": buy,
            "sell_signals": sell,
        }
