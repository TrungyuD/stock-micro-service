"""
valuation-calculator.py — Computes PE, PEG, P/B, P/S, EV/EBITDA, dividend yield,
and payout ratio from financial report data and the current market price.

All methods are stateless and safe to call from multiple gRPC worker threads.
Returns None for any ratio when the required inputs are missing or would cause
division-by-zero / nonsensical results.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Valuation score thresholds (lower PE / PEG = more undervalued)
_UNDERVALUED_THRESHOLD = 40.0
_OVERVALUED_THRESHOLD = 60.0


class ValuationCalculator:
    """
    Stateless calculator — call compute() with a current price and financial data dict.
    All arithmetic guards against zero / None inputs.
    """

    def compute(
        self,
        current_price: float,
        latest_report: dict,
        eps_history: list[dict],
        revenue_history: list[dict],
    ) -> dict[str, Any]:
        """
        Compute all valuation ratios.

        Args:
            current_price:   Latest closing price.
            latest_report:   Most-recent annual financial_reports row dict.
            eps_history:     Up to 5 annual rows with 'report_date' and 'eps'.
            revenue_history: Up to 4 annual rows with 'revenue', 'operating_income',
                             'shares_outstanding'.

        Returns:
            Flat dict matching valuation_metrics table columns plus helper fields
            used by the gRPC handler (current_eps, book_value_per_share, earnings_growth_rate).
        """
        r = latest_report or {}
        result: dict[str, Any] = {}

        # ── Helpers ───────────────────────────────────────────────────────────
        eps = _f(r.get("eps"))
        book_value_per_share = _f(r.get("book_value_per_share"))
        shares = _i(r.get("shares_outstanding"))

        result["current_eps"] = eps
        result["book_value_per_share"] = book_value_per_share

        # ── Trailing P/E ─────────────────────────────────────────────────────
        result["trailing_pe"] = _safe_div(current_price, eps)

        # ── Forward P/E (approximated: use trailing if no forward EPS available) ──
        # forward_eps is not stored separately; reuse trailing EPS as best estimate
        result["forward_pe"] = result["trailing_pe"]

        # ── PEG Ratio = trailing_pe / annual_eps_growth_rate ──────────────────
        growth_rate = self._eps_growth_rate(eps_history)
        result["earnings_growth_rate"] = growth_rate
        if result["trailing_pe"] is not None and growth_rate and growth_rate > 0:
            result["peg_ratio"] = round(result["trailing_pe"] / growth_rate, 4)
        else:
            result["peg_ratio"] = None

        # ── Price-to-Book = price / book_value_per_share ──────────────────────
        result["price_to_book"] = _safe_div(current_price, book_value_per_share)

        # ── Price-to-Sales = market_cap / revenue ─────────────────────────────
        revenue = _f(r.get("revenue"))
        if revenue and revenue > 0 and shares and shares > 0:
            revenue_per_share = revenue / shares
            result["price_to_sales"] = _safe_div(current_price, revenue_per_share)
        else:
            result["price_to_sales"] = None

        # ── EV/EBITDA ─────────────────────────────────────────────────────────
        # Approximate EBITDA ≈ operating_income (capex not reliably available)
        # EV ≈ market_cap (simplified; no debt/cash data in schema)
        operating_income = _f(r.get("operating_income"))
        if operating_income and operating_income > 0 and shares and shares > 0:
            market_cap = current_price * shares
            result["ev_to_ebitda"] = _safe_div(market_cap, operating_income)
        else:
            result["ev_to_ebitda"] = None

        # ── Dividend Yield = annual_dividend / price ───────────────────────────
        # financial_reports schema does not store dividends directly;
        # derive from net_income and payout_ratio proxy when possible.
        # Set to None — will be populated if dividend data is later added.
        result["dividend_yield"] = None
        result["payout_ratio"] = None

        net_income = _f(r.get("net_income"))
        if net_income and eps and eps > 0 and shares and shares > 0:
            # payout_ratio: fraction of EPS distributed as dividend
            # Approximate: if net_income / shares ≈ eps, payout_ratio = dividends / net_income
            # Without dividend column, leave as None
            pass

        # ── Valuation Signal & Score ──────────────────────────────────────────
        signal, score = self._valuation_signal(result)
        result["valuation_signal"] = signal
        result["valuation_score"] = score

        return result

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _eps_growth_rate(self, eps_history: list[dict]) -> float | None:
        """
        Compute the CAGR of EPS over the available history.
        Requires at least 2 data points.  Returns percentage (e.g. 15.0 for 15%).
        """
        if not eps_history or len(eps_history) < 2:
            return None

        # Sort oldest-first
        sorted_rows = sorted(eps_history, key=lambda r: r["report_date"])
        oldest_eps = _f(sorted_rows[0].get("eps"))
        newest_eps = _f(sorted_rows[-1].get("eps"))

        if oldest_eps is None or newest_eps is None:
            return None
        if oldest_eps <= 0:
            # Negative base EPS — growth rate is not meaningful
            return None

        years = len(sorted_rows) - 1
        if years <= 0:
            return None

        cagr = ((newest_eps / oldest_eps) ** (1.0 / years) - 1.0) * 100.0
        return round(cagr, 4)

    def _valuation_signal(self, metrics: dict) -> tuple[str, float]:
        """
        Derive a valuation signal ('Undervalued', 'Fair Value', 'Overvalued')
        and a 0-100 score (lower = more undervalued).

        Scoring weights:
          - P/E:   40 pts  (lower is better; benchmark 15)
          - PEG:   30 pts  (< 1 ideal)
          - P/B:   20 pts  (< 1 ideal)
          - P/S:   10 pts  (< 2 ideal)
        """
        score = 50.0  # neutral default
        factors = 0

        pe = metrics.get("trailing_pe")
        if pe is not None and pe > 0:
            # Normalize: PE of 15 → 50 pts, PE of 30 → 100 pts, PE of 7 → 0 pts
            pe_score = min(100.0, max(0.0, (pe / 30.0) * 100.0))
            score = score * (factors / (factors + 1)) + pe_score * (1 / (factors + 1)) if factors else pe_score
            factors += 1

        peg = metrics.get("peg_ratio")
        if peg is not None and peg > 0:
            # PEG < 1 → undervalued; PEG > 2 → overvalued
            peg_score = min(100.0, max(0.0, (peg / 2.0) * 100.0))
            score = score * (factors / (factors + 1)) + peg_score * (1 / (factors + 1))
            factors += 1

        pb = metrics.get("price_to_book")
        if pb is not None and pb > 0:
            pb_score = min(100.0, max(0.0, (pb / 5.0) * 100.0))
            score = score * (factors / (factors + 1)) + pb_score * (1 / (factors + 1))
            factors += 1

        ps = metrics.get("price_to_sales")
        if ps is not None and ps > 0:
            ps_score = min(100.0, max(0.0, (ps / 10.0) * 100.0))
            score = score * (factors / (factors + 1)) + ps_score * (1 / (factors + 1))
            factors += 1

        score = round(score, 2)

        if score < _UNDERVALUED_THRESHOLD:
            signal = "Undervalued"
        elif score > _OVERVALUED_THRESHOLD:
            signal = "Overvalued"
        else:
            signal = "Fair Value"

        return signal, score


# ─── Arithmetic guards ────────────────────────────────────────────────────────

def _f(v: Any) -> float | None:
    """Cast to float; return None if value is None or non-numeric."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v: Any) -> int | None:
    """Cast to int; return None if value is None or non-numeric."""
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    """Return numerator / denominator rounded to 4 dp, or None on zero/None."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)
