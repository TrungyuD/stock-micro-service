"""
analytics_handler.py — gRPC servicer implementing all 7 AnalyticsService RPCs.
Delegates to: ComputeService (compute/persist), proto_mappers (proto building),
screening_helpers (ScreenStocks filters), recommendation_helpers (StockAnalysis).
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import grpc

from calculators.technical_calculator import TechnicalCalculator
from calculators.valuation_calculator import ValuationCalculator
from generated import analytics_pb2, analytics_pb2_grpc
from generated.common import health_pb2
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
from utils.numeric_helpers import safe_float_or_zero

logger = logging.getLogger(__name__)

_VERSION = "1.0.0"
_START_TIME = datetime.now(timezone.utc)
_BATCH_LIMIT = 50
_BATCH_WORKERS = 8


class AnalyticsHandler(analytics_pb2_grpc.AnalyticsServiceServicer):
    """Implements all RPCs defined in analytics.proto."""

    def __init__(
        self,
        stock_data_repo: StockDataRepository,
        indicator_repo: IndicatorRepository,
        valuation_repo: ValuationRepository,
        tech_calc: TechnicalCalculator,
        val_calc: ValuationCalculator,
        db_pool=None,
    ) -> None:
        self._stock_repo = stock_data_repo
        self._ind_repo = indicator_repo
        self._val_repo = valuation_repo
        self._db_pool = db_pool
        self._svc = ComputeService(
            stock_data_repo, indicator_repo, valuation_repo, tech_calc, val_calc
        )
        # C3: Lock to prevent concurrent TriggerCalculation runs
        self._trigger_lock = threading.Lock()
        self._trigger_running = False

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
        # C2: Use ThreadPoolExecutor for concurrent batch processing
        with ThreadPoolExecutor(max_workers=_BATCH_WORKERS) as executor:
            future_to_sym = {
                executor.submit(self._build_stock_analysis, sym, False): sym
                for sym in symbols
            }
            for future in as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    analysis = future.result()
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
        limit = min(request.limit or 20, 200)  # cap at 200 to prevent abuse
        sort_by = request.sort_by or "valuation_score"
        try:
            matched = []
            # Single batch query returns valuation + close + indicators for all stocks
            for row in self._val_repo.get_screening_data():
                symbol = row.get("symbol", "")

                if not passes_valuation_criteria(row, criteria):
                    continue

                current_price = float(row["latest_close"]) if row.get("latest_close") else 0.0

                # Reconstruct indicator dict from prefixed columns.
                # Cast to float to handle Decimal values from LATERAL JOIN.
                ind_row = None
                if row.get("ind_rsi_14") is not None:
                    _f = safe_float_or_zero
                    ind_row = {
                        "rsi_14": _f(row["ind_rsi_14"]),
                        "sma_20": _f(row["ind_sma_20"]),
                        "sma_50": _f(row["ind_sma_50"]),
                        "sma_200": _f(row["ind_sma_200"]),
                        "ema_20": _f(row["ind_ema_20"]),
                        "ema_50": _f(row["ind_ema_50"]),
                        "macd_line": _f(row["ind_macd_line"]),
                        "macd_signal": _f(row["ind_macd_signal"]),
                        "macd_histogram": _f(row["ind_macd_histogram"]),
                        "bb_upper": _f(row["ind_bb_upper"]),
                        "bb_middle": _f(row["ind_bb_middle"]),
                        "bb_lower": _f(row["ind_bb_lower"]),
                    }
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
        # C3: Prevent concurrent trigger runs with a lock
        with self._trigger_lock:
            if self._trigger_running:
                return analytics_pb2.TriggerCalculationResponse(
                    accepted=False,
                    message="Calculation already in progress — try again later",
                )
            self._trigger_running = True
        logger.info("TriggerCalculation: type=%s symbols=%d", calc_type, len(symbols))
        threading.Thread(
            target=self._guarded_calculation_job,
            args=(symbols, calc_type),
            daemon=True,
            name="calc-trigger",
        ).start()
        return analytics_pb2.TriggerCalculationResponse(
            accepted=True,
            message=f"Calculating {calc_type} for {len(symbols)} symbol(s)",
        )

    def _guarded_calculation_job(self, symbols: list[str], calc_type: str) -> None:
        """Run calculation job and release the trigger lock when done."""
        try:
            self._svc.run_calculation_job(symbols, calc_type)
        finally:
            with self._trigger_lock:
                self._trigger_running = False

    # ─── HealthCheck ──────────────────────────────────────────────────────────

    def HealthCheck(self, request, context):
        db_ok = False
        try:
            if self._db_pool:
                db_ok = self._db_pool.health_check()
        except Exception as exc:
            logger.warning("HealthCheck DB probe failed: %s", exc)
        status = "SERVING" if db_ok else "NOT_SERVING"
        uptime = f"{int((datetime.now(timezone.utc) - _START_TIME).total_seconds())}s"
        return health_pb2.HealthCheckResponse(
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
