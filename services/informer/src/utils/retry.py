"""
retry.py — Exponential-backoff decorator for transient failures.
Retries on configurable exception types with jitter-free delays.
"""
import logging
import time
from functools import wraps
from typing import Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator that retries the wrapped function on specified exceptions.

    Delay schedule (backoff_factor=2): 2s → 4s → 8s (then re-raises).

    Args:
        max_retries:    Total attempts before giving up.
        backoff_factor: Base for exponential delay: factor^(attempt+1).
        exceptions:     Tuple of exception classes that trigger a retry.

    Example::

        @retry_with_backoff(max_retries=3, exceptions=(IOError,))
        def fetch_data(): ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_retries - 1:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__qualname__, max_retries, exc,
                        )
                        raise
                    wait = backoff_factor ** (attempt + 1)
                    logger.warning(
                        "%s attempt %d/%d failed: %s — retrying in %.1fs",
                        func.__qualname__, attempt + 1, max_retries, exc, wait,
                    )
                    time.sleep(wait)
        return wrapper
    return decorator
