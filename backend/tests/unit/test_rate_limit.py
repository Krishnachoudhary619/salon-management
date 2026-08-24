from app.core.rate_limit import SlidingWindowLimiter


def test_limiter_allows_until_limit() -> None:
    limiter = SlidingWindowLimiter()
    allowed, remaining, retry_after = limiter.hit("ip:1", limit=2, window_seconds=60)
    assert allowed is True
    assert remaining == 1
    assert retry_after == 0
    allowed, remaining, _ = limiter.hit("ip:1", limit=2, window_seconds=60)
    assert allowed is True
    assert remaining == 0
    allowed, remaining, retry_after = limiter.hit("ip:1", limit=2, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after >= 1


def test_limiter_isolates_keys() -> None:
    limiter = SlidingWindowLimiter()
    limiter.hit("ip:a", limit=1, window_seconds=60)
    allowed, _, _ = limiter.hit("ip:b", limit=1, window_seconds=60)
    assert allowed is True
