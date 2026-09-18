import os
import pytest
from app.security.rate_limiter import RedisTokenBucketRateLimiter

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_REDIS_TESTS") == "1",
    reason="Redis bağlantısı gerektirir, docker compose up ile çalıştırın",
)


@pytest.mark.asyncio
async def test_allows_requests_within_capacity():
    limiter = RedisTokenBucketRateLimiter(capacity=5, refill_per_sec=1.0, redis_url="redis://localhost:6379/1")
    for _ in range(5):
        allowed, _ = await limiter.allow("test_ip_1")
        assert allowed is True
    await limiter.close()


@pytest.mark.asyncio
async def test_blocks_requests_beyond_capacity():
    limiter = RedisTokenBucketRateLimiter(capacity=3, refill_per_sec=0.01, redis_url="redis://localhost:6379/1")
    for _ in range(3):
        await limiter.allow("test_ip_2")
    allowed, _ = await limiter.allow("test_ip_2")
    assert allowed is False
    await limiter.close()
