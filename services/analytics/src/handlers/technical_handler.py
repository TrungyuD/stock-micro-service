"""
technical-handler.py — TechnicalAnalysisService gRPC handler.
Implements GetTechnicalIndicators, GetMultipleIndicators, GetIndicatorBatch
using generated.analyzer.v1 proto types.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import grpc

from generated.analyzer.v1 import technical_pb2, technical_pb2_grpc
from handlers.compute_helpers import ComputeService
from handlers.v1_proto_mappers import dict_to_technicals_proto_v1

logger = logging.getLogger(__name__)

_BATCH_LIMIT = 20
_BATCH_WORKERS = 8

# Supported indicator filter names for GetMultipleIndicators
_INDICATOR_NAMES = {"rsi", "moving_averages", "macd", "bollinger_bands"}


class TechnicalHandler(technical_pb2_grpc.TechnicalAnalysisServiceServicer):
    """Implements TechnicalAnalysisService RPCs defined in analyzer/v1/technical.proto."""

    def __init__(self, stock_repo, svc: ComputeService) -> None:
        self._stock_repo = stock_repo
        self._svc = svc

    # ─── GetTechnicalIndicators ───────────────────────────────────────────────

    def GetTechnicalIndicators(self, request, context):
        """Return all technical indicators for a single symbol."""
        symbol = request.symbol.strip().upper()
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return technical_pb2.TechnicalIndicatorsResponse()
        try:
            stock = self._stock_repo.get_stock_by_symbol(symbol)
            if not stock:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return technical_pb2.TechnicalIndicatorsResponse()
            ind = self._svc.get_or_compute_technicals(stock)
            if ind is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Insufficient OHLCV data for {symbol}")
                return technical_pb2.TechnicalIndicatorsResponse()
            current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
            signals = self._svc.resolve_signals(ind, current_price)
            return technical_pb2.TechnicalIndicatorsResponse(
                indicators=dict_to_technicals_proto_v1(symbol, ind, current_price, signals)
            )
        except Exception as exc:
            logger.exception("GetTechnicalIndicators failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return technical_pb2.TechnicalIndicatorsResponse()

    # ─── GetMultipleIndicators ────────────────────────────────────────────────

    def GetMultipleIndicators(self, request, context):
        """Return only the requested indicator groups for a symbol."""
        symbol = request.symbol.strip().upper()
        requested = {n.lower() for n in request.indicator_names if n}
        if not symbol:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbol is required")
            return technical_pb2.MultipleIndicatorsResponse()
        # Default to all indicators if none specified
        if not requested:
            requested = _INDICATOR_NAMES
        try:
            stock = self._stock_repo.get_stock_by_symbol(symbol)
            if not stock:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return technical_pb2.MultipleIndicatorsResponse()
            ind = self._svc.get_or_compute_technicals(stock)
            if ind is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Insufficient OHLCV data for {symbol}")
                return technical_pb2.MultipleIndicatorsResponse()
            current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
            signals = self._svc.resolve_signals(ind, current_price)
            indicators = self._build_filtered_indicators(
                symbol, ind, current_price, signals, requested
            )
            return technical_pb2.MultipleIndicatorsResponse(
                symbol=symbol, indicators=indicators
            )
        except Exception as exc:
            logger.exception("GetMultipleIndicators failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return technical_pb2.MultipleIndicatorsResponse()

    # ─── GetIndicatorBatch ────────────────────────────────────────────────────

    def GetIndicatorBatch(self, request, context):
        """Batch process up to 20 symbols and return their indicators."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            return technical_pb2.IndicatorBatchResponse()
        symbols = symbols[:_BATCH_LIMIT]
        results, failed = [], []
        with ThreadPoolExecutor(max_workers=_BATCH_WORKERS) as executor:
            future_to_sym = {
                executor.submit(self._fetch_indicators_for_symbol, sym): sym
                for sym in symbols
            }
            for future in as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    proto = future.result()
                    if proto:
                        results.append(proto)
                    else:
                        failed.append(sym)
                except Exception as exc:
                    logger.warning("GetIndicatorBatch: failed for %s: %s", sym, exc)
                    failed.append(sym)
        return technical_pb2.IndicatorBatchResponse(
            results=results, failed_symbols=failed
        )

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _fetch_indicators_for_symbol(self, symbol: str):
        """Fetch and compute indicators for one symbol; returns proto or None."""
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        ind = self._svc.get_or_compute_technicals(stock)
        if ind is None:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        signals = self._svc.resolve_signals(ind, current_price)
        return dict_to_technicals_proto_v1(symbol, ind, current_price, signals)

    def _build_filtered_indicators(
        self, symbol: str, ind: dict, current_price: float,
        signals: dict, requested: set
    ) -> technical_pb2.TechnicalIndicators:
        """Build TechnicalIndicators proto with only requested groups populated."""
        from utils.numeric_helpers import safe_float_or_zero

        bb_upper = safe_float_or_zero(ind.get("bb_upper"))
        bb_lower = safe_float_or_zero(ind.get("bb_lower"))
        band_width = bb_upper - bb_lower if bb_upper and bb_lower else 0.0
        percent_b = (
            (current_price - bb_lower) / (bb_upper - bb_lower)
            if bb_upper and bb_lower and (bb_upper - bb_lower) > 0
            else 0.0
        )
        return technical_pb2.TechnicalIndicators(
            symbol=symbol,
            rsi=(
                technical_pb2.RSI(
                    period=14,
                    value=safe_float_or_zero(ind.get("rsi_14")),
                    signal=signals.get("rsi_signal", "Neutral"),
                )
                if "rsi" in requested else None
            ),
            moving_averages=(
                technical_pb2.MovingAverages(
                    sma_20=safe_float_or_zero(ind.get("sma_20")),
                    sma_50=safe_float_or_zero(ind.get("sma_50")),
                    sma_200=safe_float_or_zero(ind.get("sma_200")),
                    ema_20=safe_float_or_zero(ind.get("ema_20")),
                    ema_50=safe_float_or_zero(ind.get("ema_50")),
                    trend_signal=signals.get("trend_signal", "Neutral"),
                )
                if "moving_averages" in requested else None
            ),
            macd=(
                technical_pb2.MACDIndicator(
                    macd_line=safe_float_or_zero(ind.get("macd_line")),
                    signal_line=safe_float_or_zero(ind.get("macd_signal")),
                    histogram=safe_float_or_zero(ind.get("macd_histogram")),
                    signal=signals.get("macd_signal", "Neutral"),
                )
                if "macd" in requested else None
            ),
            bollinger_bands=(
                technical_pb2.BollingerBands(
                    upper_band=bb_upper,
                    middle_band=safe_float_or_zero(ind.get("bb_middle")),
                    lower_band=bb_lower,
                    band_width=band_width,
                    percent_b=percent_b,
                )
                if "bollinger_bands" in requested else None
            ),
            overall_signal=signals.get("overall_signal", "Neutral"),
            buy_signals=signals.get("buy_signals", 0),
            sell_signals=signals.get("sell_signals", 0),
        )
