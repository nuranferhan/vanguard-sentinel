import time
import redis.asyncio as redis
from app.config import settings


class RedisTokenBucketRateLimiter:
    _LUA_SCRIPT = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_per_sec = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])

    local bucket = redis.call("HMGET", key, "tokens", "last_refill")
    local tokens = tonumber(bucket[1])
    local last_refill = tonumber(bucket[2])

    if tokens == nil then
        tokens = capacity
        last_refill = now
    end

    local elapsed = now - last_refill
    tokens = math.min(capacity, tokens + elapsed * refill_per_sec)

    local allowed = 0
    if tokens >= 1 then
        tokens = tokens - 1
        allowed = 1
    end

    redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
    redis.call("EXPIRE", key, 3600)

    return {allowed, tokens}
    """

    def __init__(self, capacity: int, refill_per_sec: float, redis_url: str):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._script = None

    async def _get_script(self):
        if self._script is None:
            self._script = self._redis.register_script(self._LUA_SCRIPT)
        return self._script

    async def allow(self, client_ip: str, capacity_override: int | None = None) -> tuple[bool, int]:
        script = await self._get_script()
        key = f"vanguard:ratelimit:{client_ip}"
        now = time.time()
        capacity = capacity_override or self.capacity
        result = await script(keys=[key], args=[capacity, self.refill_per_sec, now])
        allowed, remaining_tokens = int(result[0]), float(result[1])
        return bool(allowed), int(remaining_tokens)

    async def current_rate(self, client_ip: str) -> float:
        key = f"vanguard:ratelimit:{client_ip}"
        tokens = await self._redis.hget(key, "tokens")
        if tokens is None:
            return 0.0
        return self.capacity - float(tokens)

    async def close(self):
        await self._redis.aclose()


rate_limiter = RedisTokenBucketRateLimiter(
    capacity=settings.rate_limit_capacity,
    refill_per_sec=settings.rate_limit_refill_per_sec,
    redis_url=settings.redis_url,
)
