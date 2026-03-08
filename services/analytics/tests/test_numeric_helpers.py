"""Tests for utils/numeric_helpers.py — safe casting and division."""
from utils.numeric_helpers import safe_div, safe_float, safe_float_or_zero, safe_int


class TestSafeFloat:
    def test_valid_int(self):
        assert safe_float(42) == 42.0

    def test_valid_string(self):
        assert safe_float("3.14") == 3.14

    def test_none(self):
        assert safe_float(None) is None

    def test_invalid_string(self):
        assert safe_float("abc") is None


class TestSafeInt:
    def test_valid(self):
        assert safe_int(42) == 42

    def test_from_float(self):
        assert safe_int(3.9) == 3

    def test_none(self):
        assert safe_int(None) is None

    def test_invalid(self):
        assert safe_int("abc") is None


class TestSafeDiv:
    def test_normal(self):
        assert safe_div(10.0, 3.0) == 3.3333

    def test_zero_denominator(self):
        assert safe_div(10.0, 0.0) is None

    def test_none_numerator(self):
        assert safe_div(None, 5.0) is None

    def test_none_denominator(self):
        assert safe_div(10.0, None) is None


class TestSafeFloatOrZero:
    def test_valid(self):
        assert safe_float_or_zero(3.14) == 3.14

    def test_none(self):
        assert safe_float_or_zero(None) == 0.0

    def test_invalid(self):
        assert safe_float_or_zero("abc") == 0.0
