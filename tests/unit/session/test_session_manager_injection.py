"""SessionManager 依赖注入测试"""
import pytest
from unittest.mock import AsyncMock

from src.core.session.manager import SessionManager
from src.core.session.store.memory import MemorySessionStore


@pytest.mark.asyncio
async def test_session_manager_with_explicit_store():
    """测试显式注入 store"""
    store = MemorySessionStore()
    manager = SessionManager(store=store)

    session = await manager.get_or_create_session("user1", "channel1")
    assert session.session_id == "user1_channel1"


@pytest.mark.asyncio
async def test_session_manager_with_default():
    """测试默认配置（不传入 store）"""
    # 默认使用内存存储
    manager = SessionManager()

    session = await manager.get_or_create_session("user2", "channel2")
    assert session.session_id == "user2_channel2"
