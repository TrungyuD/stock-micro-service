"""
screening_handler.py — ScreeningService gRPC handler.
Implements ScreenStocks, BatchAnalysis, GetPresetScreens, TriggerCalculation
using generated.analyzer.v1 proto types.
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import grpc

from generated.analyzer.v1 import fundamental_pb2, screening_pb2, screening_pb2_grpc
from handlers.compute_helpers import ComputeService
from handlers.recommendation_helpers import build_rationale, combine_recommendation
from handlers.screening_helpers import (
    compute_match_score,
    passes_technical_criteria,
    passes_valuation_criteria,
)
from handlers.v1_proto_mappers import dict_to_technicals_proto_v1, dict_to_valuation_proto_v1
from repositories.valuation_repository import ValuationRepository
from utils.numeric_helpers import safe_float_or_zero

logger = logging.getLogger(__name__)

_BATCH_LIMIT = 50
_BATCH_WORKERS = 8

# Hardcoded preset screen definitions
_PRESET_SCREENS = [
    {
        "id": "value",
        "name": "Value Stocks",
        "description": "Undervalued stocks: low PE, low PEG, any dividend yield",
        "criteria": {"max_pe": 15.0, "max_peg": 1.0},
    },
    {
        "id": "growth",
        "name": "Growth Stocks",
        "description": "High-momentum stocks: bullish trend, RSI not overbought",
        "criteria": {"trend_direction": "Bullish"},
    },
    {
        "id": "momentum",
        "name": "Momentum Stocks",
        "description": "Technically strong: buy RSI oversold bounce candidates",
        "criteria": {"rsi_oversold": True},
    },
    {
        "id": "dividend",
        "name": "Dividend Stocks",
        "description": "Income-focused: minimum 2% dividend yield",
        "criteria": {"min_dividend_yield": 2.0},
    },
]


class ScreeningHandler(screening_pb2_grpc.ScreeningServiceServicer):
    """Implements ScreeningService RPCs defined in analyzer/v1/screening.proto."""

    def __init__(self, stock_repo, val_repo: ValuationRepository, svc: ComputeService) -> None:
        self._stock_repo = stock_repo
        self._val_repo = val_repo
        self._svc = svc
        # Prevent concurrent TriggerCalculation runs
        self._trigger_lock = threading.Lock()
        self._trigger_running = False

    # ─── ScreenStocks ─────────────────────────────────────────────────────────

    def ScreenStocks(self, request, context):
        """Filter all stocks against screening criteria and return matches."""
        criteria = request.criteria
        limit = min(request.limit or 20, 200)
        sort_by = request.sort_by or "valuation_score"
        try:
            matched = []
            for row in self._val_repo.get_screening_data():
                symbol = row.get("symbol", "")
                if not passes_valuation_criteria(row, criteria):
                    continue
                current_price = float(row["latest_close"]) if row.get("latest_close") else 0.0
                ind_row = self._extract_indicator_row(row, current_price)
                if not passes_technical_criteria(ind_row, criteria):
                    continue
                if criteria.sector and row.get("sector", "") != criteria.sector:
                    continue
                matched.append(screening_pb2.ScreenedStock(
                    symbol=symbol,
                    company_name=row.get("name", ""),
                    current_price=current_price,
                    match_score=compute_match_score(row, ind_row, criteria),
                    valuation=dict_to_valuation_proto_v1(symbol, row),
                    technicals=dict_to_technicals_proto_v1(
                        symbol, ind_row or {}, current_price
                    ),
                ))
            matched = self._sort_screened(matched, sort_by)
            return screening_pb2.ScreenStocksResponse(
                stocks=matched[:limit], total_matched=len(matched)
            )
        except Exception as exc:
            logger.exception("ScreenStocks failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return screening_pb2.ScreenStocksResponse()

    # ─── BatchAnalysis ────────────────────────────────────────────────────────

    def BatchAnalysis(self, request, context):
        """Run full stock analysis for multiple symbols concurrently."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        if not symbols:
            return screening_pb2.BatchAnalysisResponse()
        symbols = symbols[:_BATCH_LIMIT]
        analyses, failed = [], []
        with ThreadPoolExecutor(max_workers=_BATCH_WORKERS) as executor:
            future_to_sym = {
                executor.submit(self._build_stock_analysis, sym): sym for sym in symbols
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
        return screening_pb2.BatchAnalysisResponse(
            analyses=analyses, failed_symbols=failed
        )

    # ─── GetPresetScreens ─────────────────────────────────────────────────────

    def GetPresetScreens(self, request, context):
        """Return hardcoded preset screening configurations."""
        presets = []
        for p in _PRESET_SCREENS:
            c = p["criteria"]
            criteria = screening_pb2.ScreeningCriteria(
                max_pe=c.get("max_pe", 0.0),
                max_peg=c.get("max_peg", 0.0),
                min_dividend_yield=c.get("min_dividend_yield", 0.0),
                trend_direction=c.get("trend_direction", ""),
                rsi_oversold=c.get("rsi_oversold", False),
            )
            presets.append(screening_pb2.PresetScreen(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                criteria=criteria,
            ))
        return screening_pb2.PresetScreensResponse(presets=presets)

    # ─── TriggerCalculation ───────────────────────────────────────────────────

    def TriggerCalculation(self, request, context):
        """Trigger async recalculation of technicals/valuation for symbols."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        calc_type = request.calculation_type or "all"
        if not symbols:
            try:
                symbols = [r["symbol"] for r in self._stock_repo.get_all_active_stocks()]
            except Exception as exc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(exc))
                return screening_pb2.TriggerCalculationResponse(accepted=False)
        with self._trigger_lock:
            if self._trigger_running:
                return screening_pb2.TriggerCalculationResponse(
                    accepted=False,
                    message="Calculation already in progress — try again later",
                )
            self._trigger_running = True
        logger.info("TriggerCalculation: type=%s symbols=%d", calc_type, len(symbols))
        threading.Thread(
            target=self._guarded_calculation_job,
            args=(symbols, calc_type),
            daemon=True,
            name="calc-trigger-v1",
        ).start()
        return screening_pb2.TriggerCalculationResponse(
            accepted=True,
            message=f"Calculating {calc_type} for {len(symbols)} symbol(s)",
        )

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _build_stock_analysis(self, symbol: str) -> fundamental_pb2.StockAnalysis | None:
        """Build StockAnalysis proto (used in BatchAnalysis)."""
        stock = self._stock_repo.get_stock_by_symbol(symbol)
        if not stock:
            return None
        current_price = self._stock_repo.get_latest_close(stock["id"]) or 0.0
        val_data = self._svc.get_or_compute_valuation(stock)
        tech_data = self._svc.get_or_compute_technicals(stock)
        if tech_data:
            tech_data["_signals"] = self._svc.resolve_signals(tech_data, current_price)
        recommendation, confidence = combine_recommendation(val_data, tech_data)
        return fundamental_pb2.StockAnalysis(
            symbol=symbol,
            company_name=stock.get("name", ""),
            current_price=current_price,
            valuation=dict_to_valuation_proto_v1(symbol, val_data or {}),
            technicals=dict_to_technicals_proto_v1(symbol, tech_data or {}, current_price),
            recommendation=recommendation,
            confidence_score=confidence,
            rationale="",
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _extract_indicator_row(self, row: dict, current_price: float) -> dict | None:
        """Extract indicator sub-dict from a screening data row."""
        if row.get("ind_rsi_14") is None:
            return None
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
        return ind_row

    def _sort_screened(
        self, stocks: list, sort_by: str
    ) -> list:
        """Sort ScreenedStock list by requested field."""
        if sort_by == "pe_ratio":
            return sorted(stocks, key=lambda s: s.valuation.trailing_pe or 999)
        if sort_by == "dividend_yield":
            return sorted(stocks, key=lambda s: s.valuation.dividend_yield, reverse=True)
        return sorted(stocks, key=lambda s: s.match_score, reverse=True)

    def _guarded_calculation_job(self, symbols: list[str], calc_type: str) -> None:
        """Run calculation job and release trigger lock on completion."""
        try:
            self._svc.run_calculation_job(symbols, calc_type)
        finally:
            with self._trigger_lock:
                self._trigger_running = False
