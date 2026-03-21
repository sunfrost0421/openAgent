"""MySQLSessionStore 单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.core.session.store.mysql import MySQLSessionStore
from src.core.session.models import Session


@pytest.fixture
def mock_session_maker():
    """模拟 session_maker"""
    # 创建一个正确的异步上下文管理器 mock
    session = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    # 设置异步上下文管理器协议
    async_session = AsyncMock()
    async_session.__aenter__.return_value = session
    async_session.__aexit__.return_value = None

    # session_maker 返回异步上下文管理器
    maker = MagicMock(return_value=async_session)
    return maker


@pytest.mark.asyncio
async def test_mysql_get_session_creates_new(mock_session_maker):
    """测试获取不存在的会话时创建新会话"""
    store = MySQLSessionStore(mock_session_maker)

    # Mock 查询结果为空
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None

    async_session = mock_session_maker.return_value
    async_session.__aenter__.return_value.execute.return_value = result_mock

    # session_id = user_id_channel_id
    session = await store.get_session("user1_channel1")

    assert session.session_id == "user1_channel1"
    assert session.user_id == "user1"
    assert session.channel_id == "channel1"


@pytest.mark.asyncio
async def test_mysql_save_session(mock_session_maker):
    """测试保存会话"""
    store = MySQLSessionStore(mock_session_maker)
    session = Session(
        session_id="test_session",
        user_id="test_user",
        channel_id="test_channel",
    )

    # Mock 查询返回 None（新会话）
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None

    async_session = mock_session_maker.return_value
    async_session.__aenter__.return_value.execute.return_value = result_mock
    async_session.__aenter__.return_value.commit = AsyncMock()

    await store.save_session(session)

    async_session.__aenter__.return_value.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_cleanup_expired(mock_session_maker):
    """测试清理过期会话"""
    store = MySQLSessionStore(mock_session_maker)
    async_session = mock_session_maker.return_value
    async_session.__aenter__.return_value.commit = AsyncMock()

    await store.cleanup_expired()

    async_session.__aenter__.return_value.commit.assert_called_once()
