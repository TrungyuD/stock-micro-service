"""Tests for utils/validators.py — symbol, OHLCV, and date-range validation."""
from datetime import date, datetime

from utils.validators import validate_date_range, validate_ohlcv, validate_symbol


class TestValidateSymbol:
    """validate_symbol() accepts 1-10 uppercase letters/dots."""

    def test_valid_simple(self):
        assert validate_symbol("AAPL") is True

    def test_valid_with_dot(self):
        assert validate_symbol("BRK.B") is True

    def test_invalid_lowercase(self):
        assert validate_symbol("aapl") is False

    def test_invalid_empty(self):
        assert validate_symbol("") is False

    def test_invalid_too_long(self):
        assert validate_symbol("A" * 11) is False

    def test_invalid_numbers(self):
        assert validate_symbol("AAPL1") is False

    def test_invalid_type(self):
        assert validate_symbol(123) is False

    def test_invalid_none(self):
        assert validate_symbol(None) is False


class TestValidateOhlcv:
    """validate_ohlcv() checks candle dict structure and sanity."""

    def test_valid_candle(self):
        candle = {"open": 150, "high": 155, "low": 148, "close": 153, "volume": 1000}
        assert validate_ohlcv(candle) is True

    def test_missing_key(self):
        candle = {"open": 150, "high": 155, "low": 148, "close": 153}
        assert validate_ohlcv(candle) is False

    def test_negative_price(self):
        candle = {"open": -1, "high": 155, "low": 148, "close": 153, "volume": 1000}
        assert validate_ohlcv(candle) is False

    def test_negative_volume(self):
        candle = {"open": 150, "high": 155, "low": 148, "close": 153, "volume": -1}
        assert validate_ohlcv(candle) is False

    def test_open_above_high(self):
        candle = {"open": 160, "high": 155, "low": 148, "close": 153, "volume": 1000}
        assert validate_ohlcv(candle) is False

    def test_close_below_low(self):
        candle = {"open": 150, "high": 155, "low": 148, "close": 140, "volume": 1000}
        assert validate_ohlcv(candle) is False

    def test_zero_price(self):
        candle = {"open": 0, "high": 155, "low": 148, "close": 153, "volume": 1000}
        assert validate_ohlcv(candle) is False

    def test_string_values_coerced(self):
        candle = {"open": "150", "high": "155", "low": "148", "close": "153", "volume": "1000"}
        assert validate_ohlcv(candle) is True


class TestValidateDateRange:
    """validate_date_range() accepts str, date, datetime; start must be before end."""

    def test_valid_strings(self):
        assert validate_date_range("2025-01-01", "2025-12-31") is True

    def test_valid_date_objects(self):
        assert validate_date_range(date(2025, 1, 1), date(2025, 12, 31)) is True

    def test_valid_datetime_objects(self):
        assert validate_date_range(datetime(2025, 1, 1), datetime(2025, 12, 31)) is True

    def test_equal_dates(self):
        assert validate_date_range("2025-06-15", "2025-06-15") is False

    def test_reversed_dates(self):
        assert validate_date_range("2025-12-31", "2025-01-01") is False

    def test_invalid_format(self):
        assert validate_date_range("not-a-date", "2025-12-31") is False

    def test_mixed_types(self):
        assert validate_date_range("2025-01-01", date(2025, 12, 31)) is True
