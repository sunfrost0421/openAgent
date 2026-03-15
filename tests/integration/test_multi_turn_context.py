"""测试多轮对话上下文"""

import pytest
import uuid

# 导入 agents 模块以注册 Agent
from src.agents import default_agent, code_agent, plan_agent  # noqa: F401

from src.orchestration.master_workflow import MasterWorkflow
from src.core.session_manager import SessionManager
from src.core.memory_session_store import MemorySessionStore


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
