"""
fundamental_handler.py — FundamentalAnalysisService gRPC handler.
Implements GetValuationMetrics, GetStockAnalysis, CompareStocks
using generated.analyzer.v1 proto types.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import grpc

from generated.analyzer.v1 import fundamental_pb2, fundamental_pb2_grpc
from handlers.compute_helpers import ComputeService
from handlers.recommendation_helpers import build_rationale, combine_recommendation
from handlers.v1_proto_mappers import dict_to_technicals_proto_v1, dict_to_valuation_proto_v1

logger = logging.getLogger(__name__)

_COMPARE_LIMIT = 10
_COMPARE_WORKERS = 4


class FundamentalHandler(fundamental_pb2_grpc.FundamentalAnalysisServiceServicer):
    """Implements FundamentalAnalysisService RPCs defined in analyzer/v1/fundamental.proto."""

    def __init__(self, stock_repo, svc: ComputeService) -> None:
        self._stock_repo = stock_repo
        self._svc = svc

    # ─── GetValuationMetrics ──────────────────────────────────────────────────

    def GetValuationMetrics(self, request, context):
        """Return valuation metrics for a single symbol."""
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return fundamental_pb2.ValuationMetricsResponse()
        try:
            stock = self._stock_repo.get_stock_by_symbol(symbol)
            if not stock:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return fundamental_pb2.ValuationMetricsResponse()
            metrics = self._svc.get_or_compute_valuation(stock)
            if metrics is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Insufficient data for {symbol}")
                return fundamental_pb2.ValuationMetricsResponse()
            return fundamental_pb2.ValuationMetricsResponse(
                metrics=dict_to_valuation_proto_v1(symbol, metrics)
            )
        except Exception as exc:
            logger.exception("GetValuationMetrics failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return fundamental_pb2.ValuationMetricsResponse()

    # ─── GetStockAnalysis ─────────────────────────────────────────────────────

    def GetStockAnalysis(self, request, context):
        """Return full stock analysis including valuation, technicals, recommendation."""
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return fundamental_pb2.StockAnalysisResponse()
        try:
            analysis = self._build_stock_analysis(symbol, request.include_rationale)
            if analysis is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found or insufficient data: {symbol}")
                return fundamental_pb2.StockAnalysisResponse()
            return fundamental_pb2.StockAnalysisResponse(analysis=analysis)
        except Exception as exc:
            logger.exception("GetStockAnalysis failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return fundamental_pb2.StockAnalysisResponse()

    # ─── CompareStocks ────────────────────────────────────────────────────────

    def CompareStocks(self, request, context):
        """Compare multiple symbols side-by-side. Returns StockComparison entries."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("at least one symbol is required")
            return fundamental_pb2.CompareStocksResponse()
        symbols = symbols[:_COMPARE_LIMIT]
        comparisons, failed = [], []
        with ThreadPoolExecutor(max_workers=_COMPARE_WORKERS) as executor:
            future_to_sym = {
                executor.submit(self._build_comparison, sym): sym for sym in symbols
            }
            for future in as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    comp = future.result()
                    if comp:
                        comparisons.append(comp)
                    else:
                        failed.append(sym)
                except Exception as exc:
                    logger.warning("CompareStocks: failed for %s: %s", sym, exc)
                    failed.append(sym)
        # Sort by symbol for deterministic ordering
        comparisons.sort(key=lambda c: c.symbol)
        return fundamental_pb2.CompareStocksResponse(
            comparisons=comparisons, failed_symbols=failed
        )

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _build_stock_analysis(
        self, symbol: str, include_rationale: bool
    ) -> fundamental_pb2.StockAnalysis | None:
        """Build StockAnalysis proto from computed valuation + technical data."""
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)
        if tech_data:
            tech_data["_signals"] = self._svc.resolve_signals(tech_data, current_price)
        recommendation, confidence = combine_recommendation(val_data, tech_data)
        # StockAnalysis.technicals references technical_pb2.TechnicalIndicators (cross-import)
        return fundamental_pb2.StockAnalysis(
            symbol=symbol,
            company_name=stock.get("name", ""),
            current_price=current_price,
            valuation=dict_to_valuation_proto_v1(symbol, val_data or {}),
            technicals=dict_to_technicals_proto_v1(symbol, tech_data or {}, current_price),
            recommendation=recommendation,
            confidence_score=confidence,
            rationale=(
                build_rationale(symbol, val_data, tech_data, recommendation)
                if include_rationale else ""
            ),
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _build_comparison(self, symbol: str) -> fundamental_pb2.StockComparison | None:
        """Build a StockComparison proto for one symbol."""
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)
        signals = self._svc.resolve_signals(tech_data, current_price) if tech_data else {}
        return fundamental_pb2.StockComparison(
            symbol=symbol,
            company_name=stock.get("name", ""),
            current_price=current_price,
            valuation=dict_to_valuation_proto_v1(symbol, val_data or {}),
            technicals=dict_to_technicals_proto_v1(
                symbol, tech_data or {}, current_price, signals
            ),
        )
