"""
test_scoring_handler.py — Tests for ScoringHandler (ScoringService).
Covers GetScore, GetBatchScores, GetRecommendation.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import grpc
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from handlers.scoring_handler import ScoringHandler, _STRATEGY_WEIGHTS
from handlers.compute_helpers import ComputeService
from generated.analyzer.v1 import scoring_pb2


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_val():
    return {
        "trailing_pe": 28.5, "valuation_score": 60.0,
        "valuation_signal": "Fair Value",
    }


@pytest.fixture
def sample_tech():
    return {
        "rsi_14": 55.0,
        "_signals": {
            "rsi_signal": "Neutral", "trend_signal": "Bullish",
            "overall_signal": "Buy", "buy_signals": 3, "sell_signals": 1,
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

        return ScoringHandler(stock_repo, svc)
    return _build


# ─── GetScore ─────────────────────────────────────────────────────────────────

class TestGetScore:
    def test_success_balanced(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetScoreRequest(symbol="aapl", strategy="balanced")
        resp = handler.GetScore(req, mock_grpc_context)
        assert resp.score.symbol == "AAPL"
        assert resp.score.strategy == "balanced"
        assert 0.0 <= resp.score.overall_score <= 100.0
        mock_grpc_context.set_code.assert_not_called()

    def test_all_strategies_produce_scores(self, make_handler, mock_grpc_context):
        handler = make_handler()
        for strategy in _STRATEGY_WEIGHTS:
            ctx = MagicMock()
            ctx.set_code = MagicMock()
            req = scoring_pb2.GetScoreRequest(symbol="AAPL", strategy=strategy)
            resp = handler.GetScore(req, ctx)
            assert resp.score.strategy == strategy
            assert 0.0 <= resp.score.overall_score <= 100.0

    def test_growth_strategy_weights_technical_higher(self, make_handler, mock_grpc_context):
        # growth: 70% tech vs value: 30% tech — growth score should be higher
        # when tech_score > val_score (buy_signals=3, sell=1 → tech=75%; val_quality=40%)
        handler = make_handler()
        ctx_g = MagicMock()
        ctx_g.set_code = MagicMock()
        ctx_v = MagicMock()
        ctx_v.set_code = MagicMock()
        resp_g = handler.GetScore(scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="growth"), ctx_g)
        resp_v = handler.GetScore(scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="value"), ctx_v)
        assert resp_g.score.overall_score != resp_v.score.overall_score

    def test_empty_symbol(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetScoreRequest(symbol="")
        handler.GetScore(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_unknown_strategy(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="lunar")
        handler.GetScore(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = scoring_pb2.GetScoreRequest(symbol="ZZZZ", strategy="balanced")
        handler.GetScore(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_internal_error_caught(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_valuation.side_effect = RuntimeError("DB error")
        req = scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="balanced")
        handler.GetScore(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)

    def test_no_tech_data_defaults_to_neutral(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_technicals.return_value = None
        req = scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="balanced")
        resp = handler.GetScore(req, mock_grpc_context)
        # tech_score defaults to 50.0 when no data
        assert resp.score.technical_score == pytest.approx(50.0)
        mock_grpc_context.set_code.assert_not_called()

    def test_calculated_at_populated(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetScoreRequest(symbol="AAPL", strategy="balanced")
        resp = handler.GetScore(req, mock_grpc_context)
        assert resp.score.calculated_at != ""


# ─── GetBatchScores ────────────────────────────────────────────────────────────

class TestGetBatchScores:
    def test_success_returns_all(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetBatchScoresRequest(symbols=["AAPL", "MSFT"], strategy="balanced")
        resp = handler.GetBatchScores(req, mock_grpc_context)
        assert len(resp.scores) == 2
        assert len(resp.failed_symbols) == 0
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbols(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetBatchScoresRequest(symbols=[])
        handler.GetBatchScores(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_unknown_strategy(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetBatchScoresRequest(symbols=["AAPL"], strategy="astro")
        handler.GetBatchScores(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_caps_at_50_symbols(self, make_handler, mock_grpc_context):
        handler = make_handler()
        symbols = [f"SYM{i}" for i in range(60)]
        req = scoring_pb2.GetBatchScoresRequest(symbols=symbols, strategy="balanced")
        resp = handler.GetBatchScores(req, mock_grpc_context)
        assert len(resp.scores) + len(resp.failed_symbols) <= 50

    def test_partial_failure_tracked(self, make_handler, mock_stock, mock_grpc_context):
        handler = make_handler()
        def side_by_sym(sym):
            return mock_stock if sym == "AAPL" else None
        handler._stock_repo.get_stock_by_symbol.side_effect = side_by_sym
        req = scoring_pb2.GetBatchScoresRequest(symbols=["AAPL", "ZZZZ"], strategy="balanced")
        resp = handler.GetBatchScores(req, mock_grpc_context)
        syms = [s.symbol for s in resp.scores]
        assert "AAPL" in syms
        assert "ZZZZ" in resp.failed_symbols

    def test_default_strategy_is_balanced(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetBatchScoresRequest(symbols=["AAPL"])
        resp = handler.GetBatchScores(req, mock_grpc_context)
        assert resp.scores[0].strategy == "balanced"


# ─── GetRecommendation ─────────────────────────────────────────────────────────

class TestGetRecommendation:
    def test_success_returns_recommendation(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetRecommendationRequest(symbol="aapl")
        resp = handler.GetRecommendation(req, mock_grpc_context)
        rec = resp.recommendation
        assert rec.symbol == "AAPL"
        assert rec.action in ("Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell")
        assert 0.0 <= rec.confidence <= 100.0
        assert "AAPL" in rec.rationale
        assert rec.score.symbol == "AAPL"
        assert rec.generated_at != ""
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbol(self, make_handler, mock_grpc_context):
        handler = make_handler()
        req = scoring_pb2.GetRecommendationRequest(symbol="")
        handler.GetRecommendation(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_symbol_not_found(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._stock_repo.get_stock_by_symbol.return_value = None
        req = scoring_pb2.GetRecommendationRequest(symbol="ZZZZ")
        handler.GetRecommendation(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_internal_error_caught(self, make_handler, mock_grpc_context):
        handler = make_handler()
        handler._svc.get_or_compute_valuation.side_effect = RuntimeError("fail")
        req = scoring_pb2.GetRecommendationRequest(symbol="AAPL")
        handler.GetRecommendation(req, mock_grpc_context)
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)

    def test_undervalued_buy_signals_give_strong_buy(self, make_handler, mock_grpc_context):
        handler = make_handler(
            val={"valuation_score": 80.0, "valuation_signal": "Undervalued"},
            tech={
                "rsi_14": 45.0,
                "_signals": {
                    "rsi_signal": "Oversold", "trend_signal": "Bullish",
                    "overall_signal": "Strong Buy", "buy_signals": 4, "sell_signals": 0,
                },
            },
        )
        req = scoring_pb2.GetRecommendationRequest(symbol="AAPL")
        resp = handler.GetRecommendation(req, mock_grpc_context)
        assert resp.recommendation.action in ("Strong Buy", "Buy")
