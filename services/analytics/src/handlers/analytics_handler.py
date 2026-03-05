"""
analytics_handler.py — gRPC servicer implementing all 7 AnalyticsService RPCs.
Delegates to: ComputeService (compute/persist), proto_mappers (proto building),
screening_helpers (ScreenStocks filters), recommendation_helpers (StockAnalysis).
"""
import logging
import threading
from datetime import datetime, timezone

import grpc

from calculators.technical_calculator import TechnicalCalculator
from calculators.valuation_calculator import ValuationCalculator
from generated import analytics_pb2, analytics_pb2_grpc
from handlers.compute_helpers import ComputeService
from handlers.proto_mappers import dict_to_technicals_proto, dict_to_valuation_proto
from handlers.recommendation_helpers import build_rationale, combine_recommendation
from handlers.screening_helpers import (
    compute_match_score,
    passes_technical_criteria,
    passes_valuation_criteria,
    sort_screened,
)
from repositories.indicator_repository import IndicatorRepository
from repositories.stock_data_repository import StockDataRepository
from repositories.valuation_repository import ValuationRepository

logger = logging.getLogger(__name__)

_VERSION = "1.0.0"
_START_TIME = datetime.now(timezone.utc)
_BATCH_LIMIT = 50


class AnalyticsHandler(analytics_pb2_grpc.AnalyticsServiceServicer):
    """Implements all RPCs defined in analytics.proto."""

    def __init__(
        self,
        stock_data_repo: StockDataRepository,
        indicator_repo: IndicatorRepository,
        valuation_repo: ValuationRepository,
    ) -> None:
        self._stock_repo = stock_data_repo
        self._ind_repo = indicator_repo
        self._val_repo = valuation_repo
        tech_calc = TechnicalCalculator()
        val_calc = ValuationCalculator()
        self._svc = ComputeService(
            stock_data_repo, indicator_repo, valuation_repo, tech_calc, val_calc
        )

    # ─── GetValuationMetrics ──────────────────────────────────────────────────

    def GetValuationMetrics(self, request, context):
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return analytics_pb2.GetValuationMetricsResponse()
        try:
            stock = self._stock_repo.get_stock_by_symbol(symbol)
            if not stock:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return analytics_pb2.GetValuationMetricsResponse()
            metrics = self._svc.get_or_compute_valuation(stock)
            if metrics is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Insufficient data for {symbol}")
                return analytics_pb2.GetValuationMetricsResponse()
            return analytics_pb2.GetValuationMetricsResponse(
                metrics=dict_to_valuation_proto(symbol, metrics)
            )
        except Exception as exc:
            logger.exception("GetValuationMetrics failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return analytics_pb2.GetValuationMetricsResponse()

    # ─── GetTechnicalIndicators ───────────────────────────────────────────────

    def GetTechnicalIndicators(self, request, context):
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return analytics_pb2.GetTechnicalIndicatorsResponse()
        try:
            stock = self._stock_repo.get_stock_by_symbol(symbol)
            if not stock:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return analytics_pb2.GetTechnicalIndicatorsResponse()
            ind = self._svc.get_or_compute_technicals(stock)
            if ind is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Insufficient OHLCV data for {symbol}")
                return analytics_pb2.GetTechnicalIndicatorsResponse()
            current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
            signals = self._svc.resolve_signals(ind, current_price)
            return analytics_pb2.GetTechnicalIndicatorsResponse(
                indicators=dict_to_technicals_proto(symbol, ind, current_price, signals)
            )
        except Exception as exc:
            logger.exception("GetTechnicalIndicators failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return analytics_pb2.GetTechnicalIndicatorsResponse()

    # ─── GetStockAnalysis ─────────────────────────────────────────────────────

    def GetStockAnalysis(self, request, context):
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return analytics_pb2.GetStockAnalysisResponse()
        try:
            analysis = self._build_stock_analysis(symbol, request.include_rationale)
            if analysis is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found or insufficient data: {symbol}")
                return analytics_pb2.GetStockAnalysisResponse()
            return analytics_pb2.GetStockAnalysisResponse(analysis=analysis)
        except Exception as exc:
            logger.exception("GetStockAnalysis failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return analytics_pb2.GetStockAnalysisResponse()

    # ─── BatchAnalysis ────────────────────────────────────────────────────────

    def BatchAnalysis(self, request, context):
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            return analytics_pb2.BatchAnalysisResponse()
        symbols = symbols[:_BATCH_LIMIT]
        analyses, failed = [], []
        for sym in symbols:
            try:
                analysis = self._build_stock_analysis(sym, include_rationale=False)
                if analysis:
                    analyses.append(analysis)
                else:
                    failed.append(sym)
            except Exception as exc:
                logger.warning("BatchAnalysis: failed for %s: %s", sym, exc)
                failed.append(sym)
        return analytics_pb2.BatchAnalysisResponse(
            analyses=analyses, failed_symbols=failed
        )

    # ─── ScreenStocks ─────────────────────────────────────────────────────────

    def ScreenStocks(self, request, context):
        criteria = request.criteria
        limit = request.limit or 20
        sort_by = request.sort_by or "valuation_score"
        try:
            matched = []
            for row in self._val_repo.get_all_latest():
                stock_id = row["stock_id"]
                symbol = row.get("symbol", "")
                if not passes_valuation_criteria(row, criteria):
                    continue
                current_price = self._stock_repo.get_latest_close(stock_id) or 0.0
                ind_row = self._ind_repo.get_latest(stock_id)
                if ind_row:
                    ind_row["_signals"] = self._svc.resolve_signals(ind_row, current_price)
                if not passes_technical_criteria(ind_row, criteria):
                    continue
                if criteria.sector and row.get("sector", "") != criteria.sector:
                    continue
                matched.append(analytics_pb2.ScreenedStock(
                    symbol=symbol,
                    company_name=row.get("name", ""),
                    current_price=current_price,
                    match_score=compute_match_score(row, ind_row, criteria),
                    valuation=dict_to_valuation_proto(symbol, row),
                    technicals=dict_to_technicals_proto(symbol, ind_row or {}, current_price),
                ))
            matched = sort_screened(matched, sort_by)
            total = len(matched)
            return analytics_pb2.ScreenStocksResponse(
                stocks=matched[:limit], total_matched=total
            )
        except Exception as exc:
            logger.exception("ScreenStocks failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return analytics_pb2.ScreenStocksResponse()

    # ─── TriggerCalculation ───────────────────────────────────────────────────

    def TriggerCalculation(self, request, context):
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        calc_type = request.calculation_type or "all"
        if not symbols:
            try:
                symbols = [r["symbol"] for r in self._stock_repo.get_all_active_stocks()]
            except Exception as exc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(exc))
                return analytics_pb2.TriggerCalculationResponse(accepted=False)
        logger.info("TriggerCalculation: type=%s symbols=%d", calc_type, len(symbols))
        threading.Thread(
            target=self._svc.run_calculation_job,
            args=(symbols, calc_type),
            daemon=True,
            name="calc-trigger",
        ).start()
        return analytics_pb2.TriggerCalculationResponse(
            accepted=True,
            message=f"Calculating {calc_type} for {len(symbols)} symbol(s)",
        )

    # ─── HealthCheck ──────────────────────────────────────────────────────────

    def HealthCheck(self, request, context):
        db_ok = False
        try:
            self._stock_repo._db.execute("SELECT 1", fetch="one")
            db_ok = True
        except Exception as exc:
            logger.warning("HealthCheck DB probe failed: %s", exc)
        status = "SERVING" if db_ok else "NOT_SERVING"
        uptime = f"{int((datetime.now(timezone.utc) - _START_TIME).total_seconds())}s"
        return analytics_pb2.HealthCheckResponse(
            status=status, version=_VERSION, uptime=uptime
        )

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _build_stock_analysis(
        self, symbol: str, include_rationale: bool
    ) -> analytics_pb2.StockAnalysis | None:
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)
        if tech_data:
            tech_data["_signals"] = self._svc.resolve_signals(tech_data, current_price)
        recommendation, confidence = combine_recommendation(val_data, tech_data)
        return analytics_pb2.StockAnalysis(
            symbol=symbol,
            company_name=stock.get("name", ""),
            current_price=current_price,
            valuation=dict_to_valuation_proto(symbol, val_data or {}),
            technicals=dict_to_technicals_proto(symbol, tech_data or {}, current_price),
            recommendation=recommendation,
            confidence_score=confidence,
            rationale=(
                build_rationale(symbol, val_data, tech_data, recommendation)
                if include_rationale else ""
            ),
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )
