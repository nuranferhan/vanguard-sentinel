import time
import redis.asyncio as redis
from app.config import settings
from app.models.schemas import ReplayGuardResult


class ReplayAttackGuard:


    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def _nonce_key(self, client_id: str, nonce: str) -> str:
        return f"vanguard:nonce:{client_id}:{nonce}"

    async def validate(self, client_id: str, nonce: str, request_timestamp: float) -> ReplayGuardResult:
        now = time.time()
        drift = abs(now - request_timestamp)

        if drift > settings.replay_window_seconds:
            return ReplayGuardResult(is_valid=False, reason="timestamp_out_of_window")

        key = self._nonce_key(client_id, nonce)
        was_set = await self._redis.set(key, "1", nx=True, ex=settings.replay_nonce_ttl_seconds)

        if not was_set:
            return ReplayGuardResult(is_valid=False, reason="nonce_reused")

        return ReplayGuardResult(is_valid=True)

    async def close(self):
        await self._redis.aclose()


replay_guard = ReplayAttackGuard(redis_url=settings.redis_url)
