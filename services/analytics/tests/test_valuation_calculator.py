"""Tests for calculators/valuation_calculator.py — PE, PEG, P/B, P/S, signals."""
from calculators.valuation_calculator import ValuationCalculator


class TestValuationCalculatorCompute:
    """ValuationCalculator.compute() returns valuation ratios."""

    def test_trailing_pe(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(150.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        # PE = 150 / 6.42 ≈ 23.36
        assert result["trailing_pe"] is not None
        assert 23.0 < result["trailing_pe"] < 24.0

    def test_peg_ratio(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(150.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        assert result["peg_ratio"] is not None
        assert result["peg_ratio"] > 0

    def test_price_to_book(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(150.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        # P/B = 150 / 4.38 ≈ 34.25
        assert result["price_to_book"] is not None
        assert result["price_to_book"] > 30

    def test_price_to_sales(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(150.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        assert result["price_to_sales"] is not None

    def test_ev_to_ebitda(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(150.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        assert result["ev_to_ebitda"] is not None

    def test_empty_report(self):
        calc = ValuationCalculator()
        result = calc.compute(150.0, {}, [], [])
        assert result["trailing_pe"] is None
        assert result["peg_ratio"] is None
        assert result["price_to_book"] is None

    def test_zero_price(self, sample_latest_report, sample_eps_history, sample_revenue_history):
        calc = ValuationCalculator()
        result = calc.compute(0.0, sample_latest_report, sample_eps_history, sample_revenue_history)
        # P/E with 0 price = 0/6.42 = 0
        assert result["trailing_pe"] == 0.0


class TestEpsGrowthRate:
    """_eps_growth_rate computes CAGR from EPS history."""

    def test_positive_growth(self):
        calc = ValuationCalculator()
        history = [
            {"report_date": "2022-12-31", "eps": 4.0},
            {"report_date": "2025-12-31", "eps": 6.0},
        ]
        rate = calc._eps_growth_rate(history)
        # CAGR = (6/4)^(1/1) - 1 = 0.5 = 50%
        assert rate is not None
        assert rate > 0

    def test_insufficient_history(self):
        calc = ValuationCalculator()
        assert calc._eps_growth_rate([]) is None
        assert calc._eps_growth_rate([{"report_date": "2025-12-31", "eps": 6.0}]) is None

    def test_negative_base_eps(self):
        calc = ValuationCalculator()
        history = [
            {"report_date": "2022-12-31", "eps": -2.0},
            {"report_date": "2025-12-31", "eps": 6.0},
        ]
        assert calc._eps_growth_rate(history) is None


class TestValuationSignal:
    """_valuation_signal returns signal string and score."""

    def test_undervalued(self):
        calc = ValuationCalculator()
        metrics = {"trailing_pe": 10, "peg_ratio": 0.5, "price_to_book": 1.0, "price_to_sales": 1.0}
        signal, score = calc._valuation_signal(metrics)
        assert signal == "Undervalued"
        assert score < 40

    def test_overvalued(self):
        calc = ValuationCalculator()
        metrics = {"trailing_pe": 50, "peg_ratio": 3.0, "price_to_book": 10.0, "price_to_sales": 15.0}
        signal, score = calc._valuation_signal(metrics)
        assert signal == "Overvalued"
        assert score > 60

    def test_no_data_defaults_neutral(self):
        calc = ValuationCalculator()
        signal, score = calc._valuation_signal({})
        assert signal == "Fair Value"
        assert score == 50.0
