"""
test_fundamental_handler.py — Tests for FundamentalHandler (FundamentalAnalysisService).
Covers GetValuationMetrics, GetStockAnalysis, CompareStocks.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import grpc
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from handlers.fundamental_handler import FundamentalHandler
from handlers.compute_helpers import ComputeService
from generated.analyzer.v1 import fundamental_pb2


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_val():
    return {
        "trailing_pe": 28.5, "forward_pe": 25.0, "current_eps": 6.42,
        "price_to_book": 45.0, "book_value_per_share": 4.38,
        "peg_ratio": 1.8, "earnings_growth_rate": 0.12,
        "dividend_yield": 0.6, "payout_ratio": 0.15,
        "price_to_sales": 7.5, "ev_to_ebitda": 22.0,
        "valuation_signal": "Fair Value", "valuation_score": 55.0,
    }


@pytest.fixture
def sample_tech():
    return {
        "rsi_14": 58.0,
        "sma_20": 150.0, "sma_50": 148.0, "sma_200": 140.0,
        "ema_20": 151.0, "ema_50": 149.0,
        "macd_line": 1.2, "macd_signal": 0.8, "macd_histogram": 0.4,
        "bb_upper": 162.0, "bb_middle": 152.0, "bb_lower": 142.0,
        "_signals": {
            "rsi_signal": "Neutral", "trend_signal": "Bullish",
            "macd_signal": "Buy", "overall_signal": "Buy",
            "buy_signals": 2, "sell_signals": 1,
        },
    }


@pytest.fixture
def mock_stock():
    return {"id": 1, "symbol": "AAPL", "name": "Apple Inc."}


@pytest.fixture
def make_handler(mock_stock, sample_val, sample_tech):
    def _build(val=None, tech=None, stock=None, price=155.0):
        val = val if val is not None else sample_val
        tech = tech if tech is not None else sample_tech
        stock = stock if stock is not None else mock_stock

        stock_repo = MagicMock()
        stock_repo.get_stock_by_symbol.return_value = stock
        stock_repo.get_latest_close.return_value = price

        svc = MagicMock(spec=ComputeService)
        svc.get_or_compute_valuation.return_value = val
        svc.get_or_compute_technicals.return_value = tech
        svc.resolve_signals.return_value = tech["_signals"]

        return FundamentalHandler(stock_repo, svc)
    return _build


# ─── GetValuationMetrics ───────────────────────────────────────────────────────

class TestGetValuationMetrics:
    def test_success_returns_metrics(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.GetValuationMetricsRequest(symbol="aapl")
        resp = handler.GetValuationMetrics(req, mock_grpc_context)
        assert resp.metrics.symbol == "AAPL"
        assert resp.metrics.trailing_pe == pytest.approx(28.5)
        assert resp.metrics.valuation_signal == "Fair Value"
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbol(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.GetValuationMetricsRequest(symbol="")
        handler.GetValuationMetrics(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = fundamental_pb2.GetValuationMetricsRequest(symbol="ZZZZ")
        handler.GetValuationMetrics(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_no_valuation_data(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_valuation.return_value = None
        req = fundamental_pb2.GetValuationMetricsRequest(symbol="AAPL")
        handler.GetValuationMetrics(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_internal_error(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_valuation.side_effect = RuntimeError("DB error")
        req = fundamental_pb2.GetValuationMetricsRequest(symbol="AAPL")
        handler.GetValuationMetrics(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── GetStockAnalysis ──────────────────────────────────────────────────────────

class TestGetStockAnalysis:
    def test_success_no_rationale(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.GetStockAnalysisRequest(symbol="AAPL", include_rationale=False)
        resp = handler.GetStockAnalysis(req, mock_grpc_context)
        assert resp.analysis.symbol == "AAPL"
        assert resp.analysis.current_price == pytest.approx(155.0)
        assert resp.analysis.recommendation in ("Buy", "Strong Buy", "Neutral", "Sell", "Strong Sell")
        assert resp.analysis.rationale == ""
        mock_grpc_context.set_code.assert_not_called()

    def test_success_with_rationale(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.GetStockAnalysisRequest(symbol="AAPL", include_rationale=True)
        resp = handler.GetStockAnalysis(req, mock_grpc_context)
        assert "AAPL" in resp.analysis.rationale

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = fundamental_pb2.GetStockAnalysisRequest(symbol="ZZZZ")
        handler.GetStockAnalysis(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_empty_symbol(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.GetStockAnalysisRequest(symbol="")
        handler.GetStockAnalysis(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_no_tech_data_still_returns_analysis(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_technicals.return_value = None
        handler._svc.resolve_signals.return_value = {}
        req = fundamental_pb2.GetStockAnalysisRequest(symbol="AAPL")
        resp = handler.GetStockAnalysis(req, mock_grpc_context)
        assert resp.analysis.symbol == "AAPL"


# ─── CompareStocks ─────────────────────────────────────────────────────────────

class TestCompareStocks:
    def test_success_returns_comparisons(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.CompareStocksRequest(symbols=["AAPL", "MSFT"])
        resp = handler.CompareStocks(req, mock_grpc_context)
        assert len(resp.comparisons) == 2
        assert len(resp.failed_symbols) == 0
        # Sorted alphabetically
        symbols = [c.symbol for c in resp.comparisons]
        assert symbols == sorted(symbols)

    def test_empty_symbols(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.CompareStocksRequest(symbols=[])
        handler.CompareStocks(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_partial_failure(self, make_handler, mock_stock, mock_grpc_context):
        handler = make_handler()
        def side_by_sym(sym):
            return mock_stock if sym == "AAPL" else None
        handler._stock_repo.get_stock_by_symbol.side_effect = side_by_sym
        req = fundamental_pb2.CompareStocksRequest(symbols=["AAPL", "ZZZZ"])
        resp = handler.CompareStocks(req, mock_grpc_context)
        assert len(resp.comparisons) == 1
        assert "ZZZZ" in resp.failed_symbols

    def test_comparison_fields_populated(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = fundamental_pb2.CompareStocksRequest(symbols=["AAPL"])
        resp = handler.CompareStocks(req, mock_grpc_context)
        comp = resp.comparisons[0]
        assert comp.current_price == pytest.approx(155.0)
        assert comp.valuation.trailing_pe == pytest.approx(28.5)
