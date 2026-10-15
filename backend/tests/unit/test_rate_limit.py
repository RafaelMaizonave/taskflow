from app.infrastructure.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_blocks_after_limit():
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("ip:/login") is True
    assert limiter.allow("ip:/login") is True
    assert limiter.allow("ip:/login") is False
    assert limiter.allow("other:/login") is True
    assert limiter.retry_after_seconds("ip:/login") >= 1
