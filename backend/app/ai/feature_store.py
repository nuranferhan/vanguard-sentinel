import time
import json
import numpy as np
import redis.asyncio as redis
from app.config import settings


class FeatureStore:


    def __init__(self, redis_url: str, window_size: int):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._window_size = window_size

    def _key(self, client_id: str) -> str:
        return f"vanguard:features:{client_id}"

    async def append(self, client_id: str, requests_per_sec: float, avg_packet_size: float,
                      unique_endpoints: int, interval_variance: float):
        key = self._key(client_id)
        record = json.dumps({
            "t": time.time(),
            "rps": requests_per_sec,
            "size": avg_packet_size,
            "endpoints": unique_endpoints,
            "variance": interval_variance,
        })
        await self._redis.lpush(key, record)
        await self._redis.ltrim(key, 0, self._window_size - 1)
        await self._redis.expire(key, 86400)

    async def get_recent(self, client_id: str, limit: int = 50) -> list[dict]:
        key = self._key(client_id)
        raw_records = await self._redis.lrange(key, 0, limit - 1)
        return [json.loads(r) for r in raw_records]

    async def get_feature_matrix(self, client_id: str, limit: int = 50) -> np.ndarray:
        records = await self.get_recent(client_id, limit)
        if not records:
            return np.empty((0, 4))
        return np.array([[r["rps"], r["size"], r["endpoints"], r["variance"]] for r in records])

    async def close(self):
        await self._redis.aclose()


feature_store = FeatureStore(redis_url=settings.redis_url, window_size=settings.feature_store_window_size)
