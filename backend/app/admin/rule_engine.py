import time
import json
import uuid
import fnmatch
import redis.asyncio as redis
from app.config import settings
from app.models.schemas import FilterRule


class RuleEngine:


    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._key = "vanguard:rules"

    async def create_rule(self, name: str, endpoint_pattern: str, created_by: str,
                           max_requests_per_sec: int | None = None,
                           blocked_countries: list[str] | None = None) -> FilterRule:
        rule = FilterRule(
            rule_id=str(uuid.uuid4()),
            name=name,
            endpoint_pattern=endpoint_pattern,
            max_requests_per_sec=max_requests_per_sec,
            blocked_countries=blocked_countries or [],
            enabled=True,
            created_by=created_by,
            created_at=time.time(),
        )
        await self._redis.hset(self._key, rule.rule_id, rule.model_dump_json())
        return rule

    async def list_rules(self) -> list[FilterRule]:
        raw_rules = await self._redis.hgetall(self._key)
        return [FilterRule(**json.loads(v)) for v in raw_rules.values()]

    async def delete_rule(self, rule_id: str):
        await self._redis.hdel(self._key, rule_id)

    async def toggle_rule(self, rule_id: str, enabled: bool):
        raw = await self._redis.hget(self._key, rule_id)
        if raw is None:
            return
        rule = FilterRule(**json.loads(raw))
        rule.enabled = enabled
        await self._redis.hset(self._key, rule_id, rule.model_dump_json())

    async def match_rules(self, endpoint: str, country_code: str | None) -> list[FilterRule]:
        rules = await self.list_rules()
        matched = []
        for rule in rules:
            if not rule.enabled:
                continue
            if not fnmatch.fnmatch(endpoint, rule.endpoint_pattern):
                continue
            if country_code and country_code in rule.blocked_countries:
                matched.append(rule)
                continue
            if rule.max_requests_per_sec is not None:
                matched.append(rule)
        return matched

    async def close(self):
        await self._redis.aclose()


rule_engine = RuleEngine(redis_url=settings.redis_url)
