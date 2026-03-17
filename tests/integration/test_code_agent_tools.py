"""CodeAgent 工具集成测试"""

import pytest
import tempfile
from pathlib import Path

# 导入 features 模块以注册 Agent
from src.features.code import code_agent  # noqa: F401
from src.features.code.tools import read_file, write_file
from src.core.orchestration import master_workflow
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer

# 显式注册所有 Agent 到意图识别器
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)


@pytest.fixture
def temp_test_file():
    """创建临时测试文件"""
    fd, path = tempfile.mkstemp(suffix='.py')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("def hello():\n    return 'Hello from file'\n")
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_code_agent_file_operations(temp_test_file):
    """测试 CodeAgent 文件操作能力"""
    # 读取测试文件内容
    result = await read_file.ainvoke({"path": temp_test_file})
    assert "def hello" in result
    assert "Hello from file" in result


@pytest.mark.asyncio
async def test_code_agent_workflow():
    """测试 CodeAgent 工作流（验证能正确路由和执行）"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="@code 写一个 Python 函数，返回两个数的和"
    )

    assert result.agent_name == "code_agent"
    assert result.final_reply
    assert "def" in result.final_reply or "lambda" in result.final_reply or "return" in result.final_reply


@pytest.mark.asyncio
async def test_code_agent_execute_request():
    """测试 CodeAgent 执行请求响应"""
    # 这个测试验证 agent 能正确响应执行代码的请求
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="@code 执行代码：print(2 + 2)"
    )

    assert result.agent_name == "code_agent"
    # Agent 应该返回执行结果
    assert result.final_reply