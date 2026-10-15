"""In-memory sliding-window rate limiter for single-process deployments."""

from __future__ import annotations

import threading
import time


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            stamps = [stamp for stamp in self._hits.get(key, ()) if stamp > cutoff]
            if len(stamps) >= self.limit:
                self._hits[key] = stamps
                return False
            stamps.append(now)
            self._hits[key] = stamps
            return True

    def retry_after_seconds(self, key: str) -> int:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            stamps = [stamp for stamp in self._hits.get(key, ()) if stamp > cutoff]
            if len(stamps) < self.limit or not stamps:
                return 0
            return max(1, int(stamps[0] + self.window_seconds - now) + 1)
