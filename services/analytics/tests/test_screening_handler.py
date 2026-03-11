"""
test_screening_handler.py — Tests for ScreeningHandler (ScreeningService).
Covers ScreenStocks, BatchAnalysis, GetPresetScreens, TriggerCalculation.
"""
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import grpc
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from handlers.screening_handler import ScreeningHandler, _PRESET_SCREENS
from handlers.compute_helpers import ComputeService
from generated.analyzer.v1 import screening_pb2


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_screening_row():
    """Row returned by ValuationRepository.get_screening_data()."""
    return {
        "symbol": "AAPL", "name": "Apple Inc.",
        "trailing_pe": 28.0, "peg_ratio": 1.5,
        "dividend_yield": 0.6, "valuation_score": 55.0,
        "valuation_signal": "Fair Value", "sector": "Technology",
        "latest_close": 155.0,
        "ind_rsi_14": 55.0,
        "ind_sma_20": 150.0, "ind_sma_50": 148.0, "ind_sma_200": 140.0,
        "ind_ema_20": 151.0, "ind_ema_50": 149.0,
        "ind_macd_line": 1.2, "ind_macd_signal": 0.8, "ind_macd_histogram": 0.4,
        "ind_bb_upper": 162.0, "ind_bb_middle": 152.0, "ind_bb_lower": 142.0,
    }


@pytest.fixture
def mock_stock():
    return {"id": 1, "symbol": "AAPL", "name": "Apple Inc."}


@pytest.fixture
def make_handler(sample_screening_row, mock_stock):
    def _build(screening_rows=None):
        rows = screening_rows if screening_rows is not None else [sample_screening_row]

        stock_repo = MagicMock()
        stock_repo.get_stock_by_symbol.return_value = mock_stock
        stock_repo.get_latest_close.return_value = 155.0
        stock_repo.get_all_active_stocks.return_value = [mock_stock]

        val_repo = MagicMock()
        val_repo.get_screening_data.return_value = rows

        svc = MagicMock(spec=ComputeService)
        svc.get_or_compute_valuation.return_value = {
            "trailing_pe": 28.0, "valuation_score": 55.0,
            "valuation_signal": "Fair Value",
        }
        svc.get_or_compute_technicals.return_value = {
            "rsi_14": 55.0,
            "_signals": {
                "rsi_signal": "Neutral", "trend_signal": "Bullish",
                "macd_signal": "Buy", "overall_signal": "Buy",
                "buy_signals": 2, "sell_signals": 1,
            },
        }
        svc.resolve_signals.return_value = {
            "rsi_signal": "Neutral", "trend_signal": "Bullish",
            "overall_signal": "Buy", "buy_signals": 2, "sell_signals": 1,
        }
        return ScreeningHandler(stock_repo, val_repo, svc)
    return _build


# ─── ScreenStocks ──────────────────────────────────────────────────────────────

class TestScreenStocks:
    def test_returns_matched_stock(self, make_handler, mock_grpc_context):
        handler = make_handler()
        criteria = screening_pb2.ScreeningCriteria()
        req = screening_pb2.ScreenStocksRequest(criteria=criteria, limit=10)
        resp = handler.ScreenStocks(req, mock_grpc_context)
        assert resp.total_matched == 1
        assert resp.stocks[0].symbol == "AAPL"
        mock_grpc_context.set_code.assert_not_called()

    def test_pe_filter_excludes_stock(self, make_handler, mock_grpc_context):
        handler = make_handler()
        # max_pe=10 should exclude AAPL with PE=28
        criteria = screening_pb2.ScreeningCriteria(max_pe=10.0)
        req = screening_pb2.ScreenStocksRequest(criteria=criteria, limit=10)
        resp = handler.ScreenStocks(req, mock_grpc_context)
        assert resp.total_matched == 0

    def test_sector_filter(self, make_handler, mock_grpc_context):
        handler = make_handler()
        criteria = screening_pb2.ScreeningCriteria(sector="Healthcare")
        req = screening_pb2.ScreenStocksRequest(criteria=criteria, limit=10)
        resp = handler.ScreenStocks(req, mock_grpc_context)
        assert resp.total_matched == 0

    def test_limit_respected(self, make_handler, mock_grpc_context, sample_screening_row):
        # 5 identical rows, limit=2
        rows = [dict(sample_screening_row, symbol=f"S{i}") for i in range(5)]
        handler = make_handler(screening_rows=rows)
        criteria = screening_pb2.ScreeningCriteria()
        req = screening_pb2.ScreenStocksRequest(criteria=criteria, limit=2)
        resp = handler.ScreenStocks(req, mock_grpc_context)
        assert len(resp.stocks) == 2
        assert resp.total_matched == 5

    def test_internal_error_caught(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._val_repo.get_screening_data.side_effect = RuntimeError("DB down")
        req = screening_pb2.ScreenStocksRequest(criteria=screening_pb2.ScreeningCriteria())
        handler.ScreenStocks(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── BatchAnalysis ─────────────────────────────────────────────────────────────

class TestBatchAnalysis:
    def test_success(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.BatchAnalysisRequest(symbols=["AAPL", "MSFT"])
        resp = handler.BatchAnalysis(req, mock_grpc_context)
        assert len(resp.analyses) == 2
        assert len(resp.failed_symbols) == 0

    def test_empty_symbols_returns_empty(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.BatchAnalysisRequest(symbols=[])
        resp = handler.BatchAnalysis(req, mock_grpc_context)
        assert len(resp.analyses) == 0

    def test_partial_failure(self, make_handler, mock_stock, mock_grpc_context):
        handler = make_handler()
        def side_by_sym(sym):
            return mock_stock if sym == "AAPL" else None
        handler._stock_repo.get_stock_by_symbol.side_effect = side_by_sym
        req = screening_pb2.BatchAnalysisRequest(symbols=["AAPL", "ZZZZ"])
        resp = handler.BatchAnalysis(req, mock_grpc_context)
        symbols = [a.symbol for a in resp.analyses]
        assert "AAPL" in symbols
        assert "ZZZZ" in resp.failed_symbols


# ─── GetPresetScreens ──────────────────────────────────────────────────────────

class TestGetPresetScreens:
    def test_returns_four_presets(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.GetPresetScreensRequest()
        resp = handler.GetPresetScreens(req, mock_grpc_context)
        assert len(resp.presets) == len(_PRESET_SCREENS)
        mock_grpc_context.set_code.assert_not_called()

    def test_preset_ids_match(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.GetPresetScreensRequest()
        resp = handler.GetPresetScreens(req, mock_grpc_context)
        ids = {p.id for p in resp.presets}
        assert ids == {"value", "growth", "momentum", "dividend"}

    def test_value_preset_has_max_pe(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.GetPresetScreensRequest()
        resp = handler.GetPresetScreens(req, mock_grpc_context)
        value_preset = next(p for p in resp.presets if p.id == "value")
        assert value_preset.criteria.max_pe > 0

    def test_dividend_preset_has_min_yield(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.GetPresetScreensRequest()
        resp = handler.GetPresetScreens(req, mock_grpc_context)
        div_preset = next(p for p in resp.presets if p.id == "dividend")
        assert div_preset.criteria.min_dividend_yield > 0


# ─── TriggerCalculation ────────────────────────────────────────────────────────

class TestTriggerCalculation:
    def test_accepted_with_symbols(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.TriggerCalculationRequest(
            symbols=["AAPL"], calculation_type="all"
        )
        resp = handler.TriggerCalculation(req, mock_grpc_context)
        assert resp.accepted is True
        assert "1 symbol" in resp.message

    def test_accepted_with_no_symbols_uses_active_stocks(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = screening_pb2.TriggerCalculationRequest(symbols=[])
        resp = handler.TriggerCalculation(req, mock_grpc_context)
        assert resp.accepted is True

    def test_concurrent_trigger_rejected(self, make_handler, mock_grpc_context):
        handler = make_handler()
        # Mark as already running
        handler._trigger_running = True
        req = screening_pb2.TriggerCalculationRequest(symbols=["AAPL"])
        resp = handler.TriggerCalculation(req, mock_grpc_context)
        assert resp.accepted is False
        assert "in progress" in resp.message
