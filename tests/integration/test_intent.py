"""意图识别集成测试"""

import pytest

# 导入 agents 模块以注册 Agent
from src.agents import default_agent, code_agent, plan_agent  # noqa: F401
from src.core.intent import intent_recognizer, IntentResult


@pytest.mark.asyncio
async def test_command_match():
    """测试命令匹配"""
    result = await intent_recognizer.recognize("@code 帮我写代码")

    assert result.agent_name == "code_agent"
    assert result.confidence == 1.0
    assert result.match_type == "command"


@pytest.mark.asyncio
async def test_keyword_match():
    """测试关键词匹配"""
    # 使用中文关键词测试
    result = await intent_recognizer.recognize("帮我写一段代码")

    # 应该匹配 code_agent
    assert result.agent_name == "code_agent"
    assert result.match_type in ["keyword", "llm"]


@pytest.mark.asyncio
async def test_greeting():
    """测试问候语匹配默认 Agent"""
    result = await intent_recognizer.recognize("你好")

    assert result.agent_name == "default_agent"
