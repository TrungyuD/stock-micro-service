"""Tests for utils/rate_limiter.py — token-bucket rate limiter."""
import time

from utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """RateLimiter allows max_calls per period; blocks excess calls."""

    def test_allows_within_limit(self):
        rl = RateLimiter(max_calls=5, period=1.0)
        for _ in range(5):
            rl.acquire()  # should not block

    def test_blocks_over_limit(self):
        rl = RateLimiter(max_calls=2, period=0.5)
        rl.acquire()
        rl.acquire()
        start = time.monotonic()
        rl.acquire()  # should block ~0.5s
        elapsed = time.monotonic() - start
        assert elapsed >= 0.3  # allow margin

    def test_context_manager(self):
        rl = RateLimiter(max_calls=5, period=1.0)
        with rl:
            pass  # should not raise

    def test_tokens_replenish(self):
        rl = RateLimiter(max_calls=1, period=0.2)
        rl.acquire()
        time.sleep(0.3)  # wait for replenish
        start = time.monotonic()
        rl.acquire()  # should be immediate
        elapsed = time.monotonic() - start
        assert elapsed < 0.15
