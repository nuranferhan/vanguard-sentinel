import time
from collections import Counter, defaultdict
from app.models.schemas import TrafficEvent
import redis.asyncio as redis
from app.config import settings
import json


class ReportGenerator:


    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._key = "vanguard:events_log"

    async def record_event(self, event: TrafficEvent):
        await self._redis.lpush(self._key, event.model_dump_json())
        await self._redis.ltrim(self._key, 0, 49999)

    async def _load_events(self, since_seconds: float) -> list[TrafficEvent]:
        raw_events = await self._redis.lrange(self._key, 0, -1)
        cutoff = time.time() - since_seconds
        events = []
        for raw in raw_events:
            data = json.loads(raw)
            if data["timestamp"] >= cutoff:
                events.append(TrafficEvent(**data))
        return events

    async def generate_summary(self, since_seconds: float = 7 * 86400) -> dict:
        events = await self._load_events(since_seconds)

        action_distribution = Counter(e.action.value for e in events)
        endpoint_targets = Counter(e.endpoint for e in events if e.action.value != "allowed")
        country_distribution = Counter(e.country_code for e in events if e.country_code)

        return {
            "period_days": since_seconds / 86400,
            "total_events": len(events),
            "action_distribution": dict(action_distribution),
            "top_targeted_endpoints": endpoint_targets.most_common(10),
            "blocked_country_distribution": dict(country_distribution),
            "block_rate_percent": (
                round(100 * (1 - action_distribution.get("allowed", 0) / len(events)), 2)
                if events else 0.0
            ),
        }

    async def close(self):
        await self._redis.aclose()


report_generator = ReportGenerator(redis_url=settings.redis_url)
