"""MySQLSessionStore 单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.core.session.store.mysql import MySQLSessionStore
from src.core.session.models import Session, Turn


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


def test_serialize_deserialize_basic_messages():
    """测试基本消息的序列化和反序列化"""
    store = MySQLSessionStore.__new__(MySQLSessionStore)

    # 创建测试消息
    messages = [
        HumanMessage(content="你好，我的名字是什么？"),
        AIMessage(content="你的名字是张三。"),
        SystemMessage(content="你是一个有用的助手。"),
    ]

    # 序列化
    json_str = store._serialize_messages(messages)
    assert isinstance(json_str, str)
    assert '"type": "human"' in json_str or '"type":"human"' in json_str

    # 反序列化
    deserialized = store._deserialize_messages(json_str)
    assert len(deserialized) == 3
    assert isinstance(deserialized[0], HumanMessage)
    assert isinstance(deserialized[1], AIMessage)
    assert isinstance(deserialized[2], SystemMessage)
    assert deserialized[0].content == "你好，我的名字是什么？"
    assert deserialized[1].content == "你的名字是张三。"
    assert deserialized[2].content == "你是一个有用的助手。"


def test_serialize_deserialize_with_tool_calls():
    """测试带 tool_calls 的 AIMessage 序列化和反序列化"""
    store = MySQLSessionStore.__new__(MySQLSessionStore)

    # 创建带 tool_calls 的 AIMessage
    ai_message = AIMessage(
        content="让我查询一下天气",
        tool_calls=[
            {"name": "get_weather", "args": {"city": "北京"}, "id": "call_1", "type": "tool_call"}
        ]
    )

    # 序列化
    json_str = store._serialize_messages([ai_message])

    # 反序列化
    deserialized = store._deserialize_messages(json_str)
    assert len(deserialized) == 1
    assert isinstance(deserialized[0], AIMessage)
    assert len(deserialized[0].tool_calls) == 1
    assert deserialized[0].tool_calls[0]["name"] == "get_weather"
    assert deserialized[0].tool_calls[0]["args"]["city"] == "北京"


def test_deserialize_empty_data():
    """测试空数据反序列化"""
    store = MySQLSessionStore.__new__(MySQLSessionStore)
    store._logger = AsyncMock()  # Mock logger

    assert store._deserialize_messages("") == []
    assert store._deserialize_messages(None) == []


def test_deserialize_invalid_json():
    """测试无效 JSON 反序列化"""
    store = MySQLSessionStore.__new__(MySQLSessionStore)
    store._logger = AsyncMock()  # Mock logger

    result = store._deserialize_messages("invalid json {")
    assert result == []
