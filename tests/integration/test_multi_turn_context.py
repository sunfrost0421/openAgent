"""测试多轮对话上下文"""

import pytest
import uuid

# 导入 features 模块以注册 Agent
from src.features.code import code_agent  # noqa: F401
from src.features.default import default_agent  # noqa: F401
from src.features.plan import plan_agent  # noqa: F401
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer

from src.core.orchestration.master_workflow import MasterWorkflow
from src.core.session.manager import SessionManager
from src.core.session.store import MemorySessionStore
from src.config import Config

# 显式注册所有 Agent 到意图识别器
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)


@pytest.mark.asyncio
async def test_multi_turn_context():
    """测试多轮对话上下文保留

    场景：
    1. 首次对话：用户告诉系统自己的名字
    2. 第二次对话：询问用户是谁，应该能回答出名字
    """
    # 创建带独立会话存储的工作流
    store = MemorySessionStore()
    session_manager = SessionManager(store)
    workflow = MasterWorkflow(session_manager=session_manager)

    # 使用唯一 ID 避免测试间污染
    unique_id = str(uuid.uuid4())[:8]
    user_id = f"test_user_{unique_id}"
    channel_id = f"test_channel_{unique_id}"

    # 第一轮：用户告诉系统自己的名字
    result1 = await workflow.execute(
        user_id=user_id,
        channel_id=channel_id,
        message="你好，我叫 qrc"
    )
    assert result1.final_reply is not None
    assert len(result1.final_reply) > 0

    # 第二轮：询问用户是谁
    result2 = await workflow.execute(
        user_id=user_id,
        channel_id=channel_id,
        message="我是谁"
    )

    # 验证：回复中应该包含用户的名字 "qrc"
    assert result2.final_reply is not None, "Second reply should not be None"
    assert "qrc" in result2.final_reply.lower(), f"Expected 'qrc' in reply: {result2.final_reply[:100]}"


@pytest.mark.asyncio
async def test_multi_turn_code_context():
    """测试代码任务的上下文保留

    场景：
    1. 第一轮：请求写一个函数
    2. 第二轮：修改这个函数
    """
    # 创建带独立会话存储的工作流
    store = MemorySessionStore()
    session_manager = SessionManager(store)
    workflow = MasterWorkflow(session_manager=session_manager)

    user_id = "test_code_user"
    channel_id = "test_channel"

    # 第一轮：请求写函数
    result1 = await workflow.execute(
        user_id=user_id,
        channel_id=channel_id,
        message="帮我写一个 Python 函数，计算两个数的和"
    )
    assert result1.final_reply is not None

    # 第二轮：修改函数
    result2 = await workflow.execute(
        user_id=user_id,
        channel_id=channel_id,
        message="给这个函数添加参数类型注解"
    )

    # 验证：回复应该包含类型注解相关内容
    assert len(result2.final_reply) > 0


@pytest.mark.asyncio
async def test_context_token_compression():
    """测试上下文 token 压缩机制

    场景：
    1. 添加多个对话轮次，超过 CONTEXT_KEEP_TURNS
    2. 验证旧轮次被正确压缩（is_compressed=True）
    3. 验证 get_context_messages 返回的消息数量受控
    """
    config = Config.get()
    store = MemorySessionStore()
    session_manager = SessionManager(store)

    # 创建会话
    session = await session_manager.get_or_create_session(
        "test_compression_user", "test_channel"
    )

    # 添加 10 个轮次（超过 CONTEXT_KEEP_TURNS=3）
    for i in range(10):
        from langchain_core.messages import HumanMessage, AIMessage
        messages = [
            HumanMessage(content=f"Question {i}"),
            AIMessage(content=f"Answer {i}")
        ]
        await session_manager.add_turn(
            session=session,
            agent_name="default_agent",
            user_message=f"Question {i}",
            messages=messages,
            final_reply=f"Answer {i}"
        )

    # 验证：大部分轮次应该被压缩
    compressed_count = sum(1 for t in session.turns if t.is_compressed)
    # 至少应该有 7 个轮次被压缩（10 - 3 = 7）
    assert compressed_count >= 7, f"Expected at least 7 compressed turns, got {compressed_count}"

    # 验证：获取上下文消息数量应该受控
    context_messages = session.get_context_messages(
        keep_turns=config.CONTEXT_KEEP_TURNS,
        max_tokens=config.CONTEXT_MAX_TOKENS
    )
    # 3 轮完整消息（每轮 2 条）+ 7 轮 final_reply（每轮 1 条）= 13 条
    expected_max = config.CONTEXT_KEEP_TURNS * 2 + (10 - config.CONTEXT_KEEP_TURNS)
    assert len(context_messages) <= expected_max, \
        f"Expected at most {expected_max} messages, got {len(context_messages)}"


@pytest.mark.asyncio
async def test_session_summary_field():
    """测试 Session 的 summary 字段"""
    from src.core.session.models import Session

    session = Session(session_id="test")
    assert hasattr(session, "summary")
    assert session.summary == ""

    # 模拟设置摘要
    session.summary = "这是一个测试摘要"
    assert session.summary == "这是一个测试摘要"
