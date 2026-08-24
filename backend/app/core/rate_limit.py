import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """In-process sliding-window limiter. Swap the backing store for Redis later."""

    def __init__(self, *, max_keys: int = 10_000) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._max_keys = max_keys

    def hit(self, key: str, *, limit: int, window_seconds: float) -> tuple[bool, int, int]:
        """Record a hit. Returns (allowed, remaining, retry_after_seconds)."""
        now = time.monotonic()
        window_start = now - window_seconds
        bucket = self._hits[key]
        while bucket and bucket[0] <= window_start:
            bucket.popleft()
        if len(self._hits) > self._max_keys:
            self._evict_expired(window_start)
        if len(bucket) >= limit:
            retry_after = max(1, int(bucket[0] + window_seconds - now) + 1)
            return False, 0, retry_after
        bucket.append(now)
        remaining = max(0, limit - len(bucket))
        return True, remaining, 0

    def _evict_expired(self, window_start: float) -> None:
        stale = [
            key
            for key, bucket in self._hits.items()
            if not bucket or bucket[-1] <= window_start
        ]
        for key in stale:
            del self._hits[key]
        extra = len(self._hits) - self._max_keys
        if extra <= 0:
            return
        oldest = sorted(
            self._hits,
            key=lambda key: self._hits[key][0] if self._hits[key] else 0,
        )
        for key in oldest[:extra]:
            del self._hits[key]
