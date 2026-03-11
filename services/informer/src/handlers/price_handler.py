"""
price_handler.py — PriceService gRPC handler. Price data retrieval and streaming.
Implements PriceServiceServicer from generated.informer.v1.price_pb2_grpc.
"""
import logging
import time
from datetime import datetime, timezone

import grpc
import yfinance as yf

from generated.informer.v1 import price_pb2, price_pb2_grpc
from utils.rate_limiter import RateLimiter
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)

# Cap symbols per batch call and rate-limit yfinance requests
_MAX_SYMBOLS = 20
_rate_limiter = RateLimiter(max_calls=5, period=1.0)


class PriceHandler(price_pb2_grpc.PriceServiceServicer):
    """
    Implements all RPCs defined in price.proto (PriceService).
    Handles single/batch price snapshots, OHLCV history, and streaming stubs.
    """

    def __init__(self, provider, ohlcv_repo) -> None:
        self._provider = provider
        self._ohlcv_repo = ohlcv_repo

    # ─── GetLatestPrice ───────────────────────────────────────────────────────

    def GetLatestPrice(self, request, context):
        """Fetch real-time price snapshot for a single symbol."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return price_pb2.PricePoint()

        try:
            _rate_limiter.acquire()
            fast_info = yf.Ticker(symbol).fast_info
            last_price = _safe_float(fast_info, "last_price")
            previous_close = _safe_float(fast_info, "previous_close")

            if last_price is None or previous_close is None or previous_close == 0.0:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Price data unavailable for {symbol}")
                return price_pb2.PricePoint()

            change_pct = ((last_price - previous_close) / previous_close) * 100.0
            return price_pb2.PricePoint(
                symbol=symbol,
                last_price=last_price,
                previous_close=previous_close,
                change_pct=change_pct,
                timestamp=int(time.time()),
            )
        except Exception as exc:
            logger.exception("GetLatestPrice failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return price_pb2.PricePoint()

    # ─── GetLatestPrices ──────────────────────────────────────────────────────

    def GetLatestPrices(self, request, context):
        """Batch fetch real-time price snapshots for up to MAX_SYMBOLS symbols."""
        symbols = list(request.symbols)
        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbols list must not be empty")
            return price_pb2.BatchPriceResponse()

        # Deduplicate, normalize, and cap input
        seen: set[str] = set()
        unique: list[str] = []
        for sym in symbols:
            normalized = sym.strip().upper()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)
                if len(unique) >= _MAX_SYMBOLS:
                    break

        price_points: list[price_pb2.PricePoint] = []
        failed: list[str] = []
        now_epoch = int(time.time())

        for symbol in unique:
            try:
                _rate_limiter.acquire()
                fast_info = yf.Ticker(symbol).fast_info
                last_price = _safe_float(fast_info, "last_price")
                previous_close = _safe_float(fast_info, "previous_close")

                if last_price is None or previous_close is None or previous_close == 0.0:
                    logger.warning("GetLatestPrices: incomplete data for %s", symbol)
                    failed.append(symbol)
                    continue

                change_pct = ((last_price - previous_close) / previous_close) * 100.0
                price_points.append(
                    price_pb2.PricePoint(
                        symbol=symbol,
                        last_price=last_price,
                        previous_close=previous_close,
                        change_pct=change_pct,
                        timestamp=now_epoch,
                    )
                )
            except Exception as exc:
                logger.error("GetLatestPrices: failed for %s: %s", symbol, exc)
                failed.append(symbol)

        return price_pb2.BatchPriceResponse(prices=price_points, failed=failed)

    # ─── GetOHLCV ─────────────────────────────────────────────────────────────

    def GetOHLCV(self, request, context):
        """Return historical OHLCV bars for a symbol and optional date range."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return price_pb2.OHLCVResponse()

        start = request.start_date or "2015-01-01"
        end = request.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        limit = request.limit or 0

        try:
            df = self._provider.get_historical_ohlcv(symbol, start, end)
            if df.empty:
                return price_pb2.OHLCVResponse(symbol=symbol)

            rows = df.to_dict("records")
            if limit > 0:
                rows = rows[-limit:]  # keep most-recent N bars

            candles = [
                price_pb2.OHLCV(
                    date=str(r["time"]),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=int(r["volume"]),
                    adjusted_close=float(r["adjusted_close"]) if r.get("adjusted_close") is not None else 0.0,
                )
                for r in rows
            ]
            return price_pb2.OHLCVResponse(
                symbol=symbol,
                candles=candles,
                total_records=len(candles),
                period_start=str(rows[0]["time"]) if rows else "",
                period_end=str(rows[-1]["time"]) if rows else "",
            )
        except Exception as exc:
            logger.exception("GetOHLCV failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return price_pb2.OHLCVResponse()

    # ─── StreamPrices ─────────────────────────────────────────────────────────

    def StreamPrices(self, request, context):
        """
        Server-side streaming: yields PriceUpdate messages at regular intervals.
        Uses yfinance fast_info for real-time price snapshots.
        Runs until the client cancels or the context is terminated.
        """
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        interval_ms = request.interval_ms or 15000
        interval_s = max(interval_ms / 1000.0, 5.0)  # minimum 5-second interval

        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbols list must not be empty")
            return

        unique = _deduplicate(symbols)
        logger.info("StreamPrices started for %d symbols, interval=%ds", len(unique), interval_s)

        try:
            while context.is_active():
                for symbol in unique:
                    if not context.is_active():
                        break
                    try:
                        _rate_limiter.acquire()
                        fast_info = yf.Ticker(symbol).fast_info
                        last_price = _safe_float(fast_info, "last_price")
                        previous_close = _safe_float(fast_info, "previous_close")

                        if last_price is None or previous_close is None or previous_close == 0.0:
                            continue

                        change_pct = ((last_price - previous_close) / previous_close) * 100.0
                        yield price_pb2.PriceUpdate(
                            symbol=symbol,
                            last_price=last_price,
                            previous_close=previous_close,
                            change_pct=change_pct,
                            timestamp=int(time.time()),
                        )
                    except Exception as exc:
                        logger.debug("StreamPrices: %s fetch failed: %s", symbol, exc)

                time.sleep(interval_s)
        except Exception:
            logger.info("StreamPrices terminated for %d symbols", len(unique))

    # ─── WatchStockUpdates ────────────────────────────────────────────────────

    def WatchStockUpdates(self, request, context):
        """
        Server-side streaming: yields StockUpdate messages for price changes.
        Wraps the same fetch logic as StreamPrices but adds update_type metadata.
        """
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbols list must not be empty")
            return

        unique = _deduplicate(symbols)
        logger.info("WatchStockUpdates started for %d symbols", len(unique))

        try:
            while context.is_active():
                for symbol in unique:
                    if not context.is_active():
                        break
                    try:
                        _rate_limiter.acquire()
                        fast_info = yf.Ticker(symbol).fast_info
                        last_price = _safe_float(fast_info, "last_price")
                        previous_close = _safe_float(fast_info, "previous_close")

                        if last_price is None or previous_close is None or previous_close == 0.0:
                            continue

                        change_pct = ((last_price - previous_close) / previous_close) * 100.0
                        price_update = price_pb2.PriceUpdate(
                            symbol=symbol,
                            last_price=last_price,
                            previous_close=previous_close,
                            change_pct=change_pct,
                            timestamp=int(time.time()),
                        )
                        yield price_pb2.StockUpdate(
                            symbol=symbol,
                            update_type="price",
                            price=price_update,
                            timestamp=int(time.time()),
                        )
                    except Exception as exc:
                        logger.debug("WatchStockUpdates: %s failed: %s", symbol, exc)

                time.sleep(15.0)
        except Exception:
            logger.info("WatchStockUpdates terminated for %d symbols", len(unique))


# ─── helpers ─────────────────────────────────────────────────────────────────

def _deduplicate(symbols: list[str]) -> list[str]:
    """Deduplicate a symbol list preserving order; cap at _MAX_SYMBOLS."""
    seen: set[str] = set()
    unique: list[str] = []
    for sym in symbols:
        if sym not in seen:
            seen.add(sym)
            unique.append(sym)
            if len(unique) >= _MAX_SYMBOLS:
                break
    return unique


def _safe_float(fast_info, attr: str) -> float | None:
    """Extract a float attribute from yfinance fast_info safely. Returns None on error/NaN."""
    try:
        val = getattr(fast_info, attr, None)
        if val is None:
            return None
        fval = float(val)
        if fval != fval or fval == float("inf") or fval == float("-inf"):
            return None
        return fval
    except (TypeError, ValueError):
        return None
