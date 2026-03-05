"""
technical_indicators.py — Compute RSI, MACD, Bollinger Bands, EMA, SMA
using pandas-ta on OHLCV DataFrames. Full implementation in Phase 5.
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compute_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Compute RSI (Relative Strength Index) for a given OHLCV DataFrame.
    Requires 'close' column.
    TODO Phase 5: implement using pandas_ta.rsi()
    """
    raise NotImplementedError("RSI computation implemented in Phase 5")


def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Compute MACD (Moving Average Convergence Divergence).
    Returns DataFrame with macd, macd_signal, macd_hist columns.
    TODO Phase 5: implement using pandas_ta.macd()
    """
    raise NotImplementedError("MACD computation implemented in Phase 5")


def compute_bollinger_bands(
    df: pd.DataFrame, length: int = 20, std: float = 2.0
) -> pd.DataFrame:
    """
    Compute Bollinger Bands (upper, mid, lower).
    TODO Phase 5: implement using pandas_ta.bbands()
    """
    raise NotImplementedError("Bollinger Bands computation implemented in Phase 5")


def compute_ema(df: pd.DataFrame, length: int = 20) -> pd.Series:
    """
    Compute EMA (Exponential Moving Average).
    TODO Phase 5: implement using pandas_ta.ema()
    """
    raise NotImplementedError("EMA computation implemented in Phase 5")
