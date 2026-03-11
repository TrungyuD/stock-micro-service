"""
scoring_handler.py — ScoringService gRPC handler.
Composite stock scoring and recommendations using weighted strategy blends.
ALL RPCs are new (no legacy equivalent).
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import grpc

from generated.analyzer.v1 import scoring_pb2, scoring_pb2_grpc
from handlers.compute_helpers import ComputeService
from handlers.recommendation_helpers import build_rationale, combine_recommendation
from utils.numeric_helpers import safe_float_or_zero

logger = logging.getLogger(__name__)

_BATCH_LIMIT = 50
_BATCH_WORKERS = 8

# Strategy → (valuation_weight, technical_weight)
_STRATEGY_WEIGHTS: dict[str, tuple[float, float]] = {
    "balanced": (0.50, 0.50),
    "growth":   (0.30, 0.70),
    "value":    (0.70, 0.30),
    "momentum": (0.20, 0.80),
}
_DEFAULT_STRATEGY = "balanced"


class ScoringHandler(scoring_pb2_grpc.ScoringServiceServicer):
    """Implements ScoringService RPCs defined in analyzer/v1/scoring.proto."""

    def __init__(self, stock_repo, svc: ComputeService) -> None:
        self._stock_repo = stock_repo
        self._svc = svc

    # ─── GetScore ─────────────────────────────────────────────────────────────

    def GetScore(self, request, context):
        """Compute composite weighted score for a single symbol."""
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return scoring_pb2.ScoreResponse()
        strategy = request.strategy or _DEFAULT_STRATEGY
        if strategy not in _STRATEGY_WEIGHTS:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Unknown strategy '{strategy}'. Valid: {sorted(_STRATEGY_WEIGHTS)}"
            )
            return scoring_pb2.ScoreResponse()
        try:
            score = self._compute_score(symbol, strategy)
            if score is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found or insufficient data: {symbol}")
                return scoring_pb2.ScoreResponse()
            return scoring_pb2.ScoreResponse(score=score)
        except Exception as exc:
            logger.exception("GetScore failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return scoring_pb2.ScoreResponse()

    # ─── GetBatchScores ───────────────────────────────────────────────────────

    def GetBatchScores(self, request, context):
        """Compute scores for up to 50 symbols concurrently."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("at least one symbol is required")
            return scoring_pb2.BatchScoreResponse()
        symbols = symbols[:_BATCH_LIMIT]
        strategy = request.strategy or _DEFAULT_STRATEGY
        if strategy not in _STRATEGY_WEIGHTS:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Unknown strategy '{strategy}'")
            return scoring_pb2.BatchScoreResponse()
        scores, failed = [], []
        with ThreadPoolExecutor(max_workers=_BATCH_WORKERS) as executor:
            future_to_sym = {
                executor.submit(self._compute_score, sym, strategy): sym
                for sym in symbols
            }
            for future in as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    score = future.result()
                    if score:
                        scores.append(score)
                    else:
                        failed.append(sym)
                except Exception as exc:
                    logger.warning("GetBatchScores: failed for %s: %s", sym, exc)
                    failed.append(sym)
        return scoring_pb2.BatchScoreResponse(scores=scores, failed_symbols=failed)

    # ─── GetRecommendation ────────────────────────────────────────────────────

    def GetRecommendation(self, request, context):
        """Return recommendation with rationale and composite score."""
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return scoring_pb2.RecommendationResponse()
        try:
            rec_proto = self._build_recommendation(symbol)
            if rec_proto is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found or insufficient data: {symbol}")
                return scoring_pb2.RecommendationResponse()
            return scoring_pb2.RecommendationResponse(recommendation=rec_proto)
        except Exception as exc:
            logger.exception("GetRecommendation failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return scoring_pb2.RecommendationResponse()

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _compute_score(self, symbol: str, strategy: str) -> scoring_pb2.StockScore | None:
        """
        Compute a StockScore for the symbol using the requested strategy weights.
        valuation_score: derived from valuation_score field (0–100, lower = better value).
        technical_score: derived from buy/sell signal ratio (0–100).
        overall_score: weighted blend per strategy.
        """
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)

        val_score = safe_float_or_zero((val_data or {}).get("valuation_score"))
        # Convert valuation_score to "quality" scale (lower raw = better value → invert)
        val_quality = round(100.0 - min(val_score, 100.0), 2)

        tech_score = 50.0  # neutral default
        if tech_data:
            signals = self._svc.resolve_signals(tech_data, current_price)
            buy = signals.get("buy_signals", 0)
            sell = signals.get("sell_signals", 0)
            total = buy + sell
            if total > 0:
                tech_score = round((buy / total) * 100.0, 2)

        val_w, tech_w = _STRATEGY_WEIGHTS[strategy]
        overall = round(val_w * val_quality + tech_w * tech_score, 2)

        return scoring_pb2.StockScore(
            symbol=symbol,
            technical_score=tech_score,
            valuation_score=val_quality,
            overall_score=overall,
            strategy=strategy,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _build_recommendation(self, symbol: str) -> scoring_pb2.Recommendation | None:
        """Build a full Recommendation proto using existing helpers."""
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)
        if tech_data:
            tech_data["_signals"] = self._svc.resolve_signals(tech_data, current_price)
        action, confidence = combine_recommendation(val_data, tech_data)
        rationale = build_rationale(symbol, val_data, tech_data, action)
        score = self._compute_score(symbol, _DEFAULT_STRATEGY)
        return scoring_pb2.Recommendation(
            symbol=symbol,
            action=action,
            confidence=confidence,
            rationale=rationale,
            score=score,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
