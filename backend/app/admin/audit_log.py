import time
import json
import redis.asyncio as redis
from app.config import settings
from app.models.schemas import AuditLogEntry


class AuditLogger:


    def __init__(self, redis_url: str, retention_days: int):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._key = "vanguard:audit_log"
        self._retention_seconds = retention_days * 86400

    async def record(self, actor: str, action: str, target: str, detail: str | None = None):
        entry = AuditLogEntry(actor=actor, action=action, target=target, timestamp=time.time(), detail=detail)
        await self._redis.lpush(self._key, entry.model_dump_json())
        await self._redis.ltrim(self._key, 0, 9999)

    async def list_entries(self, limit: int = 100) -> list[AuditLogEntry]:
        raw_entries = await self._redis.lrange(self._key, 0, limit - 1)
        return [AuditLogEntry(**json.loads(e)) for e in raw_entries]

    async def close(self):
        await self._redis.aclose()


audit_logger = AuditLogger(redis_url=settings.redis_url, retention_days=settings.audit_log_retention_days)
