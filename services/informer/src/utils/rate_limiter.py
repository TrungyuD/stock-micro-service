"""
rate_limiter.py — Simple token-bucket rate limiter for yfinance API calls.
Prevents hitting Yahoo Finance rate limits during bulk symbol fetches.
Full implementation in Phase 4.
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token-bucket rate limiter.
    Allows `max_calls` per `period` seconds across all threads.

    Thread-safety note: the lock is released before sleeping so other threads
    are not blocked during the wait period, then re-acquired to append the
    new call timestamp.
    """

    def __init__(self, max_calls: int = 10, period: float = 1.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available without holding the lock while sleeping."""
        while True:
            with self._lock:
                now = time.monotonic()
                # Drop timestamps outside the rolling window
                self._calls = [t for t in self._calls if now - t < self._period]
                if len(self._calls) < self._max_calls:
                    # Token available — record call and return immediately
                    self._calls.append(time.monotonic())
                    return
                # Calculate wait time before releasing the lock
                wait = self._period - (now - self._calls[0])

            # Sleep outside the lock so other threads can inspect/update state
            if wait > 0:
                logger.debug("Rate limit reached — sleeping %.2fs", wait)
                time.sleep(wait)
            # Loop back to re-check under lock (another thread may have consumed a slot)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        pass
