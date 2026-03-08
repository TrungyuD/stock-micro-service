"""Tests for utils/retry.py — exponential-backoff decorator."""
from unittest.mock import patch

import pytest

from utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    """retry_with_backoff retries on configured exceptions with backoff delays."""

    def test_success_no_retry(self):
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def fn():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert fn() == "ok"
        assert call_count == 1

    @patch("utils.retry.time.sleep")
    def test_retries_on_exception(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(IOError,))
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise IOError("fail")
            return "ok"

        assert fn() == "ok"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("utils.retry.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=2, backoff_factor=2.0, exceptions=(IOError,))
        def fn():
            nonlocal call_count
            call_count += 1
            raise IOError("persistent")

        with pytest.raises(IOError):
            fn()
        assert call_count == 2

    def test_no_retry_on_unmatched_exception(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, exceptions=(IOError,))
        def fn():
            nonlocal call_count
            call_count += 1
            raise ValueError("wrong type")

        with pytest.raises(ValueError):
            fn()
        assert call_count == 1

    @patch("utils.retry.time.sleep")
    def test_backoff_delays(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(IOError,))
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise IOError()
            return "ok"

        fn()
        # Delays: 2^1=2, 2^2=4
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)
