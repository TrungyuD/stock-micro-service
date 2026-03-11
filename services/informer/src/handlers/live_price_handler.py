"""
live_price_handler.py — gRPC handler for GetLivePrice RPC.
Fetches real-time price snapshots via yfinance fast_info for up to 20 symbols.
"""
import logging
import time

import yfinance as yf

from generated import informer_pb2
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Cap symbols per call and rate-limit yfinance requests
_MAX_SYMBOLS = 20
# Conservative limit: 5 calls/second to avoid Yahoo Finance throttling
_rate_limiter = RateLimiter(max_calls=5, period=1.0)


def get_live_prices(symbols: list[str]) -> informer_pb2.GetLivePriceResponse:
    """
    Fetch live price snapshots for a list of symbols using yfinance fast_info.

    - Caps input at MAX_SYMBOLS (extras silently ignored)
    - Per-symbol errors are logged and skipped (batch never aborts)
    - change_pct = ((last_price - previous_close) / previous_close) * 100

    Returns:
        GetLivePriceResponse with populated LivePrice entries for successful symbols.
    """
    # Deduplicate and cap symbols
    seen: set[str] = set()
    unique_symbols: list[str] = []
    for sym in symbols:
        normalized = sym.strip().upper()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_symbols.append(normalized)
            if len(unique_symbols) >= _MAX_SYMBOLS:
                break

    if not unique_symbols:
        return informer_pb2.GetLivePriceResponse()

    prices: list[informer_pb2.LivePrice] = []
    now_epoch = int(time.time())

    for symbol in unique_symbols:
        try:
            _rate_limiter.acquire()
            fast_info = yf.Ticker(symbol).fast_info

            last_price = _safe_float(fast_info, "last_price")
            previous_close = _safe_float(fast_info, "previous_close")

            # Skip symbol if either price value is missing/invalid
            if last_price is None or previous_close is None or previous_close == 0.0:
                logger.warning("GetLivePrice: incomplete data for %s, skipping", symbol)
                continue

            change_pct = ((last_price - previous_close) / previous_close) * 100.0

            prices.append(
                informer_pb2.LivePrice(
                    symbol=symbol,
                    last_price=last_price,
                    previous_close=previous_close,
                    change_pct=change_pct,
                    timestamp=now_epoch,
                )
            )
            logger.debug(
                "GetLivePrice: %s last=%.4f prev_close=%.4f chg=%.2f%%",
                symbol, last_price, previous_close, change_pct,
            )
        except Exception as exc:
            # Log and continue — a single bad symbol must not crash the batch
            logger.error("GetLivePrice: failed to fetch %s: %s", symbol, exc)

    return informer_pb2.GetLivePriceResponse(prices=prices)


def _safe_float(fast_info, attr: str) -> float | None:
    """
    Extract a float attribute from yfinance fast_info safely.
    Returns None if the attribute is missing, None, or NaN.
    """
    try:
        val = getattr(fast_info, attr, None)
        if val is None:
            return None
        fval = float(val)
        # Reject NaN / Inf which cannot be serialized into proto double
        if fval != fval or fval == float("inf") or fval == float("-inf"):
            return None
        return fval
    except (TypeError, ValueError):
        return None
