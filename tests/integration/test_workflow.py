"""工作流集成测试"""

import pytest

# 导入 agents 模块以注册 Agent
from src.agents import default_agent, code_agent, plan_agent  # noqa: F401
from src.orchestration.master_workflow import master_workflow


@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="你好"
    )

    assert result.agent_name in ["default_agent", "code_agent", "plan_agent"]
    assert result.final_reply
    assert result.messages


@pytest.mark.asyncio
async def test_command_routing():
    """测试命令路由"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="@code 帮我写个函数"
    )

    assert result.agent_name == "code_agent"
    assert result.final_reply


@pytest.mark.asyncio
async def test_plan_command():
    """测试计划命令"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="@plan 帮我制定一个学习计划"
    )

    assert result.agent_name == "plan_agent"
    assert result.final_reply
