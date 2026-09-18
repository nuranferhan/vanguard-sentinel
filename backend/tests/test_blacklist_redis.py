import os
import pytest
from app.security.blacklist import RedisIPBlacklistManager

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_REDIS_TESTS") == "1",
    reason="Redis bağlantısı gerektirir, docker compose up ile çalıştırın",
)


@pytest.mark.asyncio
async def test_ban_and_check():
    manager = RedisIPBlacklistManager(redis_url="redis://localhost:6379/1")
    await manager.ban("9.9.9.9", "test_reason")
    assert await manager.is_banned("9.9.9.9") is True
    await manager.unban("9.9.9.9")
    await manager.close()


@pytest.mark.asyncio
async def test_violation_threshold_triggers_ban():
    manager = RedisIPBlacklistManager(redis_url="redis://localhost:6379/1")
    banned = False
    for _ in range(10):
        banned = await manager.record_violation("8.8.8.8", "flood")
    assert banned is True
    await manager.unban("8.8.8.8")
    await manager.close()
