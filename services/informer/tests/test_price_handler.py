"""Tests for handlers/price_handler.py — PriceService RPCs with v1 proto types."""
from unittest.mock import MagicMock, patch

import grpc
import pandas as pd
import pytest

from handlers.price_handler import PriceHandler
from generated.informer.v1 import price_pb2


@pytest.fixture
def mock_provider():
    return MagicMock()


@pytest.fixture
def mock_ohlcv_repo():
    return MagicMock()


@pytest.fixture
def price_handler(mock_provider, mock_ohlcv_repo):
    return PriceHandler(mock_provider, mock_ohlcv_repo)


# ─── GetLatestPrice ───────────────────────────────────────────────────────────

class TestGetLatestPrice:
    def _make_fast_info(self, last_price=150.0, previous_close=148.0):
        fi = MagicMock()
        fi.last_price = last_price
        fi.previous_close = previous_close
        return fi

    def test_valid_symbol_returns_price_point(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "AAPL"

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter") as mock_rl:
            mock_ticker.return_value.fast_info = self._make_fast_info()

            resp = price_handler.GetLatestPrice(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert resp.last_price == 150.0
        assert resp.previous_close == 148.0
        assert abs(resp.change_pct - ((150.0 - 148.0) / 148.0 * 100)) < 0.001
        mock_grpc_context.set_code.assert_not_called()

    def test_invalid_symbol_returns_invalid_argument(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "!!!"

        resp = price_handler.GetLatestPrice(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_missing_price_data_returns_not_found(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "AAPL"

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"):
            fi = MagicMock()
            fi.last_price = None
            fi.previous_close = 148.0
            mock_ticker.return_value.fast_info = fi

            price_handler.GetLatestPrice(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_yfinance_error_returns_internal(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "AAPL"

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"):
            mock_ticker.side_effect = RuntimeError("network error")

            price_handler.GetLatestPrice(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── GetLatestPrices ──────────────────────────────────────────────────────────

class TestGetLatestPrices:
    def _make_fast_info(self, last_price=150.0, previous_close=148.0):
        fi = MagicMock()
        fi.last_price = last_price
        fi.previous_close = previous_close
        return fi

    def test_batch_returns_price_points(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbols = ["AAPL", "MSFT"]

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"):
            mock_ticker.return_value.fast_info = self._make_fast_info()

            resp = price_handler.GetLatestPrices(request, mock_grpc_context)

        assert len(resp.prices) == 2
        assert resp.prices[0].symbol == "AAPL"
        assert resp.prices[1].symbol == "MSFT"
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbols_returns_invalid_argument(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbols = []

        price_handler.GetLatestPrices(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_failed_symbol_goes_to_failed_list(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbols = ["AAPL", "BADINPUT"]

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"):
            def _ticker_side_effect(sym):
                t = MagicMock()
                if sym == "AAPL":
                    t.fast_info = self._make_fast_info()
                else:
                    t.fast_info = MagicMock()
                    t.fast_info.last_price = None
                    t.fast_info.previous_close = None
                return t
            mock_ticker.side_effect = _ticker_side_effect

            resp = price_handler.GetLatestPrices(request, mock_grpc_context)

        assert len(resp.prices) == 1
        assert "BADINPUT" in resp.failed

    def test_deduplicates_symbols(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbols = ["AAPL", "aapl", "AAPL"]

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"):
            mock_ticker.return_value.fast_info = self._make_fast_info()

            resp = price_handler.GetLatestPrices(request, mock_grpc_context)

        # yfinance called only once for the deduplicated symbol
        assert mock_ticker.call_count == 1


# ─── GetOHLCV ─────────────────────────────────────────────────────────────────

class TestGetOHLCV:
    def _make_ohlcv_df(self):
        return pd.DataFrame([{
            "time": "2025-06-15",
            "open": 150.0, "high": 155.0, "low": 148.0,
            "close": 153.0, "volume": 1000000, "adjusted_close": 153.0,
        }])

    def test_returns_ohlcv_candles(self, price_handler, mock_provider, mock_grpc_context):
        mock_provider.get_historical_ohlcv.return_value = self._make_ohlcv_df()
        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-01-01"
        request.end_date = "2025-12-31"
        request.limit = 0

        resp = price_handler.GetOHLCV(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.candles) == 1
        assert resp.candles[0].close == 153.0
        assert resp.total_records == 1
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_data_returns_empty_response(self, price_handler, mock_provider, mock_grpc_context):
        mock_provider.get_historical_ohlcv.return_value = pd.DataFrame()
        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-01-01"
        request.end_date = "2025-12-31"
        request.limit = 0

        resp = price_handler.GetOHLCV(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.candles) == 0
        mock_grpc_context.set_code.assert_not_called()

    def test_limit_truncates_to_most_recent(self, price_handler, mock_provider, mock_grpc_context):
        rows = [{"time": f"2025-06-{i:02d}", "open": 1.0, "high": 2.0,
                 "low": 0.5, "close": 1.5, "volume": 100, "adjusted_close": 1.5}
                for i in range(1, 6)]
        mock_provider.get_historical_ohlcv.return_value = pd.DataFrame(rows)
        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-06-01"
        request.end_date = "2025-06-05"
        request.limit = 2

        resp = price_handler.GetOHLCV(request, mock_grpc_context)

        assert len(resp.candles) == 2
        assert resp.candles[0].date == "2025-06-04"

    def test_invalid_symbol_returns_invalid_argument(self, price_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "!BAD"

        price_handler.GetOHLCV(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_provider_error_returns_internal(self, price_handler, mock_provider, mock_grpc_context):
        mock_provider.get_historical_ohlcv.side_effect = RuntimeError("provider down")
        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-01-01"
        request.end_date = "2025-12-31"
        request.limit = 0

        price_handler.GetOHLCV(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── StreamPrices ─────────────────────────────────────────────────────────────

class MockStreamContext:
    """Minimal gRPC context mock for server-side streaming tests.

    is_active() returns True for the first `active_cycles` calls, then False.
    For a stream with N symbols, each loop iteration consumes 1 (while) + N (inner guards) calls.
    Use active_cycles = 1 + N to get one full round for N symbols.
    """

    def __init__(self, active_cycles: int = 3):
        self._active_cycles = active_cycles
        self._call_count = 0
        self._code = None
        self._details = None

    def is_active(self) -> bool:
        self._call_count += 1
        return self._call_count <= self._active_cycles

    def set_code(self, code):
        self._code = code

    def set_details(self, details):
        self._details = details


def _make_fast_info(last_price=150.0, previous_close=148.0):
    fi = MagicMock()
    fi.last_price = last_price
    fi.previous_close = previous_close
    return fi


class TestStreamPrices:
    def test_stream_prices_yields_updates(self, price_handler):
        """Should yield PriceUpdate messages for each symbol each active cycle."""
        request = MagicMock()
        request.symbols = ["AAPL", "MSFT"]
        request.interval_ms = 5000
        # 1 while-check + 2 inner-guard checks for 2 symbols = 3 total active calls
        ctx = MockStreamContext(active_cycles=3)

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"), \
             patch("handlers.price_handler.time.sleep"):
            mock_ticker.return_value.fast_info = _make_fast_info()

            updates = list(price_handler.StreamPrices(request, ctx))

        assert len(updates) == 2
        assert updates[0].symbol == "AAPL"
        assert updates[0].last_price == 150.0
        assert updates[1].symbol == "MSFT"

    def test_stream_prices_empty_symbols_sets_invalid_argument(self, price_handler):
        """Empty symbols list must set INVALID_ARGUMENT and return without yielding."""
        request = MagicMock()
        request.symbols = []
        request.interval_ms = 5000
        ctx = MockStreamContext(active_cycles=0)

        result = list(price_handler.StreamPrices(request, ctx) or [])

        assert result == []
        assert ctx._code == grpc.StatusCode.INVALID_ARGUMENT

    def test_stream_prices_stops_when_cancelled(self, price_handler):
        """Generator should stop as soon as context.is_active() returns False."""
        request = MagicMock()
        request.symbols = ["AAPL"]
        request.interval_ms = 5000
        # 1 while-check + 1 inner-guard = 2 total active calls for 1 symbol per round
        ctx = MockStreamContext(active_cycles=2)

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"), \
             patch("handlers.price_handler.time.sleep"):
            mock_ticker.return_value.fast_info = _make_fast_info()

            updates = list(price_handler.StreamPrices(request, ctx))

        # No second round since is_active() returns False after first cycle
        assert len(updates) == 1

    def test_stream_prices_skips_bad_symbol_and_continues(self, price_handler):
        """A single symbol fetch failure should be logged and skipped, not kill the stream."""
        request = MagicMock()
        request.symbols = ["AAPL", "BADINPUT"]
        request.interval_ms = 5000
        # 2 symbols → 1 + 2 = 3 active calls
        ctx = MockStreamContext(active_cycles=3)

        def ticker_side_effect(sym):
            t = MagicMock()
            if sym == "AAPL":
                t.fast_info = _make_fast_info()
            else:
                t.fast_info.last_price = None
                t.fast_info.previous_close = None
            return t

        with patch("handlers.price_handler.yf.Ticker", side_effect=ticker_side_effect), \
             patch("handlers.price_handler._rate_limiter"), \
             patch("handlers.price_handler.time.sleep"):
            updates = list(price_handler.StreamPrices(request, ctx))

        assert len(updates) == 1
        assert updates[0].symbol == "AAPL"


# ─── WatchStockUpdates ────────────────────────────────────────────────────────

class TestWatchStockUpdates:
    def test_watch_stock_updates_yields(self, price_handler):
        """Should yield StockUpdate messages for each symbol."""
        request = MagicMock()
        request.symbols = ["AAPL"]
        # 1 symbol → 1 (while) + 1 (inner guard) = 2 active calls
        ctx = MockStreamContext(active_cycles=2)

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"), \
             patch("handlers.price_handler.time.sleep"):
            mock_ticker.return_value.fast_info = _make_fast_info()

            updates = list(price_handler.WatchStockUpdates(request, ctx))

        assert len(updates) == 1
        assert updates[0].symbol == "AAPL"

    def test_watch_stock_updates_has_price_field(self, price_handler):
        """Each StockUpdate must carry update_type='price' and a populated price sub-message."""
        request = MagicMock()
        request.symbols = ["AAPL"]
        ctx = MockStreamContext(active_cycles=2)

        with patch("handlers.price_handler.yf.Ticker") as mock_ticker, \
             patch("handlers.price_handler._rate_limiter"), \
             patch("handlers.price_handler.time.sleep"):
            mock_ticker.return_value.fast_info = _make_fast_info()

            updates = list(price_handler.WatchStockUpdates(request, ctx))

        assert updates[0].update_type == "price"
        assert updates[0].price.last_price == 150.0
        assert updates[0].price.previous_close == 148.0

    def test_watch_stock_updates_empty_symbols_sets_invalid_argument(self, price_handler):
        """Empty symbols list must set INVALID_ARGUMENT without yielding."""
        request = MagicMock()
        request.symbols = []
        ctx = MockStreamContext(active_cycles=0)

        result = list(price_handler.WatchStockUpdates(request, ctx) or [])

        assert result == []
        assert ctx._code == grpc.StatusCode.INVALID_ARGUMENT
