"""Per-user rate limiting with pluggable backends.

Two implementations are provided:

- :class:`MemoryRateLimiter`: an in-process fixed-window counter. Zero
  dependencies, but each worker process keeps its own counts, so under
  multiple workers the effective limit is ``limit * num_workers``. It also
  prunes expired buckets lazily on each call to avoid unbounded growth.
- :class:`RedisRateLimiter`: a Redis-backed fixed-window counter (INCR +
  EXPIRE). Accurate across workers/instances when a ``REDIS_URL`` is
  configured. Requires the ``redis`` package.

The active limiter is chosen in :func:`get_limiter` based on whether
``REDIS_URL`` is set. Callers should use the FastAPI dependency
:func:`rate_limiter` (and the action-specific wrappers in routers) so the
backend can be swapped in tests via ``app.dependency_overrides``.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Protocol

from fastapi import HTTPException

from .config import REDIS_URL

logger = logging.getLogger("xuexibao.ratelimit")


class RateLimiter(Protocol):
    def check(self, *, key: str, limit: int, window_s: int = 3600) -> None:
        """Raise HTTPException(429) if ``key`` has hit ``limit`` in the window.

        Otherwise record this call against the key.
        """
        ...


class MemoryRateLimiter:
    """In-process fixed-window rate limiter.

    Stores ``{key: [(timestamp, ...)]}`` in memory. Lazily prunes expired
    entries on each ``check`` to prevent unbounded memory growth from users
    who never return. Thread-safe via a single coarse lock.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        # Prune at most this many stale keys per check() to bound overhead.
        self._prune_every = 64
        self._calls_since_prune = 0

    def check(self, *, key: str, limit: int, window_s: int = 3600) -> None:
        now = time.time()
        cutoff = now - window_s
        with self._lock:
            self._maybe_prune(now, window_s)
            calls = [t for t in self._store.get(key, []) if t > cutoff]
            if len(calls) >= limit:
                self._store[key] = calls
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，每小时最多 {limit} 次，请稍后再试。",
                )
            calls.append(now)
            self._store[key] = calls

    def _maybe_prune(self, now: float, window_s: int) -> None:
        """Drop keys whose entries are all expired. Bounded amortized cost."""
        self._calls_since_prune += 1
        if self._calls_since_prune < self._prune_every:
            return
        self._calls_since_prune = 0
        cutoff = now - window_s
        # Keep keys that have at least one still-valid timestamp.
        self._store = {k: [t for t in v if t > cutoff] for k, v in self._store.items() if any(t > cutoff for t in v)}


class RedisRateLimiter:
    """Redis fixed-window rate limiter (INCR + EXPIRE).

    Accurate across multiple workers/processes. Requires the ``redis``
    package; if it is unavailable we fall back to memory and log a warning.
    """

    _KEY_PREFIX = "ratelimit:"

    def __init__(self, redis_url: str) -> None:
        import redis  # imported lazily so the app still runs without redis

        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        # Ping early so a bad URL surfaces immediately rather than per-request.
        try:
            self._redis.ping()
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Redis connection failed (%s); rate limiting will be inaccurate.", exc)

    def check(self, *, key: str, limit: int, window_s: int = 3600) -> None:
        redis_key = f"{self._KEY_PREFIX}{key}"
        try:
            count = self._redis.incr(redis_key)
            if count == 1:
                self._redis.expire(redis_key, window_s)
            if count > limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，每小时最多 {limit} 次，请稍后再试。",
                )
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - environment dependent
            # If Redis is down, fail open (allow the request) rather than
            # blocking all users. Log so operators notice.
            logger.warning("Redis rate-limit check failed (%s); allowing request.", exc)


_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    """Return the process-wide limiter, building it on first call."""
    global _limiter
    if _limiter is not None:
        return _limiter

    if REDIS_URL:
        try:
            _limiter = RedisRateLimiter(REDIS_URL)
            logger.info("Rate limiting backed by Redis: %s", REDIS_URL)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Could not initialize Redis limiter (%s); falling back to memory.", exc)
            _limiter = MemoryRateLimiter()
    else:
        _limiter = MemoryRateLimiter()
    return _limiter


def reset_limiter_for_tests() -> None:
    """Force the next ``get_limiter()`` to rebuild (test-only)."""
    global _limiter
    _limiter = None
