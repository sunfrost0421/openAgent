"""意图识别集成测试"""

import pytest

# 导入 features 模块以注册 Agent
from src.features.code import code_agent  # noqa: F401
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer

# 显式注册所有 Agent 到意图识别器
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)


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
