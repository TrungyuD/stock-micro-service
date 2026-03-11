"""
test_technical_handler.py — Tests for TechnicalHandler (TechnicalAnalysisService).
Covers GetTechnicalIndicators, GetMultipleIndicators, GetIndicatorBatch.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import grpc
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from handlers.technical_handler import TechnicalHandler
from handlers.compute_helpers import ComputeService
from generated.analyzer.v1 import technical_pb2


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_ind():
    """Realistic indicator dict returned by ComputeService."""
    return {
        "rsi_14": 55.0,
        "sma_20": 150.0, "sma_50": 148.0, "sma_200": 140.0,
        "ema_20": 151.0, "ema_50": 149.0,
        "macd_line": 1.2, "macd_signal": 0.8, "macd_histogram": 0.4,
        "bb_upper": 160.0, "bb_middle": 150.0, "bb_lower": 140.0,
        "_signals": {
            "rsi_signal": "Neutral",
            "trend_signal": "Bullish",
            "macd_signal": "Buy",
            "overall_signal": "Buy",
            "buy_signals": 2,
            "sell_signals": 1,
        },
    }


@pytest.fixture
def mock_stock():
    return {"id": 1, "symbol": "AAPL", "name": "Apple Inc."}


@pytest.fixture
def make_handler(mock_stock, sample_ind):
    """Factory that builds a TechnicalHandler with all dependencies mocked."""
    def _build(ind=sample_ind, stock=mock_stock, price=155.0):
        stock_repo = MagicMock()
        stock_repo.get_stock_by_symbol.return_value = stock
        stock_repo.get_latest_close.return_value = price

        svc = MagicMock(spec=ComputeService)
        svc.get_or_compute_technicals.return_value = ind
        svc.resolve_signals.return_value = ind["_signals"]

        return TechnicalHandler(stock_repo, svc)
    return _build


# ─── GetTechnicalIndicators ────────────────────────────────────────────────────

class TestGetTechnicalIndicators:
    def test_success_returns_indicators(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetTechnicalIndicatorsRequest(symbol="aapl")
        resp = handler.GetTechnicalIndicators(req, mock_grpc_context)
        assert resp.indicators.symbol == "AAPL"
        assert resp.indicators.rsi.value == pytest.approx(55.0)
        assert resp.indicators.overall_signal == "Buy"
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbol_returns_invalid_argument(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetTechnicalIndicatorsRequest(symbol="  ")
        handler.GetTechnicalIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = technical_pb2.GetTechnicalIndicatorsRequest(symbol="ZZZZ")
        handler.GetTechnicalIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_insufficient_data_returns_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_technicals.return_value = None
        req = technical_pb2.GetTechnicalIndicatorsRequest(symbol="AAPL")
        handler.GetTechnicalIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_internal_error_is_caught(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_technicals.side_effect = RuntimeError("DB down")
        req = technical_pb2.GetTechnicalIndicatorsRequest(symbol="AAPL")
        handler.GetTechnicalIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── GetMultipleIndicators ─────────────────────────────────────────────────────

class TestGetMultipleIndicators:
    def test_rsi_only(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetMultipleIndicatorsRequest(symbol="AAPL", indicator_names=["rsi"])
        resp = handler.GetMultipleIndicators(req, mock_grpc_context)
        assert resp.symbol == "AAPL"
        assert resp.indicators.rsi.value == pytest.approx(55.0)
        # moving_averages should not be populated
        assert resp.indicators.moving_averages.sma_20 == 0.0

    def test_all_indicators_when_no_filter(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetMultipleIndicatorsRequest(symbol="AAPL", indicator_names=[])
        resp = handler.GetMultipleIndicators(req, mock_grpc_context)
        # All groups populated when no filter
        assert resp.indicators.rsi.value == pytest.approx(55.0)
        assert resp.indicators.moving_averages.sma_20 == pytest.approx(150.0)

    def test_empty_symbol(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetMultipleIndicatorsRequest(symbol="")
        handler.GetMultipleIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = technical_pb2.GetMultipleIndicatorsRequest(symbol="ZZZZ")
        handler.GetMultipleIndicators(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)


# ─── GetIndicatorBatch ─────────────────────────────────────────────────────────

class TestGetIndicatorBatch:
    def test_batch_returns_results(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetIndicatorBatchRequest(symbols=["AAPL", "MSFT"])
        resp = handler.GetIndicatorBatch(req, mock_grpc_context)
        # Both succeed with mocked data
        assert len(resp.results) == 2
        assert len(resp.failed_symbols) == 0

    def test_empty_symbols_returns_empty(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = technical_pb2.GetIndicatorBatchRequest(symbols=[])
        resp = handler.GetIndicatorBatch(req, mock_grpc_context)
        assert len(resp.results) == 0

    def test_batch_caps_at_20_symbols(self, make_handler, mock_grpc_context):
        handler = make_handler()
        symbols = [f"SYM{i}" for i in range(30)]
        req = technical_pb2.GetIndicatorBatchRequest(symbols=symbols)
        resp = handler.GetIndicatorBatch(req, mock_grpc_context)
        # Only 20 processed; all succeed with mock
        assert len(resp.results) + len(resp.failed_symbols) <= 20

    def test_partial_failure_tracked(self, make_handler, mock_stock, sample_ind, mock_grpc_context):
        handler = make_handler()
        # AAPL succeeds, ZZZZ not found
        def side_by_sym(sym):
            return mock_stock if sym == "AAPL" else None
        handler._stock_repo.get_stock_by_symbol.side_effect = side_by_sym
        req = technical_pb2.GetIndicatorBatchRequest(symbols=["AAPL", "ZZZZ"])
        resp = handler.GetIndicatorBatch(req, mock_grpc_context)
        symbols_got = [r.symbol for r in resp.results]
        assert "AAPL" in symbols_got
        assert "ZZZZ" in resp.failed_symbols
