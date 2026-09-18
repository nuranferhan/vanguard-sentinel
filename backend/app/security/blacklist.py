import time
import json
import redis.asyncio as redis
from app.config import settings
from app.models.schemas import BlacklistEntry


class RedisIPBlacklistManager:
    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def _ban_key(self, ip: str) -> str:
        return f"vanguard:blacklist:{ip}"

    def _violation_key(self, ip: str) -> str:
        return f"vanguard:violations:{ip}"

    async def record_violation(self, ip: str, reason: str) -> bool:
        key = self._violation_key(ip)
        count = await self._redis.incr(key)
        await self._redis.expire(key, settings.blacklist_ttl_seconds)

        if count >= settings.max_violations_before_ban:
            await self.ban(ip, reason, count)
            return True
        return False

    async def ban(self, ip: str, reason: str, violation_count: int = 1):
        now = time.time()
        entry = BlacklistEntry(
            ip=ip,
            reason=reason,
            banned_at=now,
            expires_at=now + settings.blacklist_ttl_seconds,
            violation_count=violation_count,
        )
        await self._redis.set(
            self._ban_key(ip),
            entry.model_dump_json(),
            ex=settings.blacklist_ttl_seconds,
        )

    async def is_banned(self, ip: str) -> bool:
        exists = await self._redis.exists(self._ban_key(ip))
        return bool(exists)

    async def unban(self, ip: str):
        await self._redis.delete(self._ban_key(ip))
        await self._redis.delete(self._violation_key(ip))

    async def list_active(self) -> list[BlacklistEntry]:
        keys = await self._redis.keys("vanguard:blacklist:*")
        entries = []
        for key in keys:
            raw = await self._redis.get(key)
            if raw:
                entries.append(BlacklistEntry(**json.loads(raw)))
        return entries

    async def close(self):
        await self._redis.aclose()


blacklist_manager = RedisIPBlacklistManager(redis_url=settings.redis_url)
