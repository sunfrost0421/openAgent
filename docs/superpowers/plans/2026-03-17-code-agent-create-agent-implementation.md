# CodeAgent 改造实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 CodeAgent 从直接调用 LLM 改造为使用 LangChain `create_agent` + `Tools` 模式，实现工具调用能力

**Architecture:** 保留 BaseExecutor 继承结构，在 CodeAgent 内部使用 create_agent 创建带工具的 Agent，采用混合方案为 CodeAgent 单独配置 Checkpointer

**Tech Stack:** LangChain (create_agent, @tool), LangGraph (MemorySaver), FastAPI, pytest-asyncio

---

## Chunk 1: 工具定义与测试

### Task 1: 创建工具定义文件

**Files:**
- Create: `src/features/code/tools.py`

- [ ] **Step 1: 创建工具定义文件**

```python
"""CodeAgent 工具定义"""

from langchain.tools import tool
from pathlib import Path
import subprocess
import tempfile
from typing import Optional, Tuple

# 项目根目录（功能优先阶段：允许任意路径）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


@tool
def read_file(path: str, lines: Optional[Tuple[int, int]] = None) -> str:
    """读取文件内容

    Args:
        path: 文件路径（绝对路径或相对于项目根目录）
        lines: 可选，指定行范围 (start, end)，从 0 开始计数

    Returns:
        文件内容字符串

    Example:
        >>> read_file.invoke({"path": "README.md"})
        >>> read_file.invoke({"path": "src/main.py", "lines": [0, 10]})
    """
    # 功能优先阶段：允许绝对路径
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path

    if not file_path.exists():
        return f"Error: File not found: {path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if lines:
            line_list = content.split('\n')[lines[0]:lines[1]]
            return '\n'.join(line_list)

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(path: str, content: str, mode: str = 'w') -> str:
    """写入/创建文件

    Args:
        path: 文件路径（绝对路径或相对于项目根目录）
        content: 文件内容
        mode: 写入模式 ('w' 覆盖，'a' 追加)

    Returns:
        操作结果字符串

    Example:
        >>> write_file.invoke({"path": "output.txt", "content": "Hello World"})
        >>> write_file.invoke({"path": "log.txt", "content": "New line", "mode": "a"})
    """
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w' if mode == 'w' else 'a', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def execute_code(code: str, timeout: int = 30) -> str:
    """执行 Python 代码

    Args:
        code: Python 代码字符串
        timeout: 超时时间（秒），默认 30 秒

    Returns:
        执行结果（stdout/stderr 和退出码）

    Example:
        >>> execute_code.invoke({"code": "print('hello')"})
        >>> execute_code.invoke({"code": "1+1", "timeout": 10})
    """
    try:
        # 创建临时文件执行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT  # 在项目根目录执行
        )

        # 清理临时文件
        Path(temp_path).unlink()

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        if result.returncode == 0:
            output.append("Execution completed successfully")
        else:
            output.append(f"Exit code: {result.returncode}")

        return '\n'.join(output)

    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"


def get_all_tools():
    """获取所有工具列表

    Returns:
        工具列表 [read_file, write_file, execute_code]
    """
    return [read_file, write_file, execute_code]
```

- [ ] **Step 2: 运行静态检查**

```bash
python -m py_compile src/features/code/tools.py
```
Expected: 无错误

---

### Task 2: 编写工具单元测试

**Files:**
- Create: `tests/unit/features/code/test_tools.py`

- [ ] **Step 1: 创建测试目录**

```bash
mkdir -p tests/unit/features/code
```

- [ ] **Step 2: 创建测试文件**

```python
"""CodeAgent 工具单元测试"""

import pytest
import tempfile
from pathlib import Path

from src.features.code.tools import read_file, write_file, execute_code


@pytest.fixture
def temp_file():
    """创建临时文件用于测试"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
    yield path
    Path(path).unlink()


@pytest.mark.asyncio
async def test_read_file_exists(temp_file):
    """测试读取已存在的文件"""
    result = await read_file.ainvoke({"path": temp_file})
    assert "Line 1" in result
    assert "Line 5" in result


@pytest.mark.asyncio
async def test_read_file_not_found():
    """测试读取不存在的文件"""
    result = await read_file.ainvoke({"path": "/nonexistent/file.txt"})
    assert "Error" in result
    assert "not found" in result


@pytest.mark.asyncio
async def test_read_file_with_lines(temp_file):
    """测试读取指定行范围"""
    result = await read_file.ainvoke({"path": temp_file, "lines": [1, 3]})
    assert "Line 2" in result
    assert "Line 3" in result
    assert "Line 1" not in result
    assert "Line 4" not in result


@pytest.mark.asyncio
async def test_write_file_new(temp_file):
    """测试写入新文件"""
    test_path = temp_file + "_new.txt"
    try:
        result = await write_file.ainvoke({
            "path": test_path,
            "content": "Test content"
        })
        assert "Successfully wrote" in result

        # 验证内容
        with open(test_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "Test content"
    finally:
        Path(test_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_write_file_append(temp_file):
    """测试追加模式写入"""
    result = await write_file.ainvoke({
        "path": temp_file,
        "content": "\nLine 6",
        "mode": "a"
    })
    assert "Successfully wrote" in result

    # 验证内容
    with open(temp_file, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "Line 5" in content
    assert "Line 6" in content


@pytest.mark.asyncio
async def test_execute_code_simple():
    """测试执行简单代码"""
    result = await execute_code.ainvoke({"code": "print('hello world')"})
    assert "hello world" in result
    assert "completed successfully" in result


@pytest.mark.asyncio
async def test_execute_code_with_error():
    """测试执行出错代码"""
    result = await execute_code.ainvoke({"code": "1/0"})
    assert "Error" in result or "STDERR" in result or "ZeroDivisionError" in result


@pytest.mark.asyncio
async def test_execute_code_timeout():
    """测试超时处理"""
    code = "import time\ntime.sleep(10)"
    result = await execute_code.ainvoke({"code": code, "timeout": 2})
    assert "timed out" in result
```

- [ ] **Step 3: 创建 unit 测试 __init__.py**

```python
# tests/unit/__init__.py
"""单元测试模块"""
```

```python
# tests/unit/features/__init__.py
"""Features 单元测试"""
```

```python
# tests/unit/features/code/__init__.py
"""Code 模块测试"""
```

- [ ] **Step 4: 运行工具测试**

```bash
pytest tests/unit/features/code/test_tools.py -v
```
Expected: 8 个测试全部通过

---

## Chunk 2: CodeAgent 改造

### Task 3: 修改 CodeAgent 使用 create_agent

**Files:**
- Modify: `src/features/code/code_agent.py`

- [ ] **Step 1: 更新 imports**

```python
"""Code Agent - 代码助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from src.core.orchestration.executor import BaseExecutor
from src.core.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.features.prompts import Prompts
from src.features.code.tools import get_all_tools
```

- [ ] **Step 2: 重写 CodeAgent 类**

```python
@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求，包括编写、解释、调试代码，支持文件读写和代码执行",
    keywords=[
        "代码", "编程", "function", "class", "def", "import",
        "write code", "code", "function", "class", "bug", "debug",
        "file", "read", "write", "execute", "run"
    ],
    command="@code"
)
class CodeAgent(BaseExecutor):
    """Code Agent - 代码助手（支持工具调用）"""

    def __init__(self, session, user_message, session_manager=None):
        """初始化 CodeAgent

        Args:
            session: 当前会话
            user_message: 用户输入消息
            session_manager: 会话管理器
        """
        super().__init__(session, user_message, session_manager)

        # 初始化工具和 agent
        self.tools = get_all_tools()
        self.llm = create_llm()

        # 创建 agent（使用内存 Checkpointer）
        # 注：checkpointer 用于 Agent 内部状态持久化，与 SessionManager 独立
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=MemorySaver()  # 开发阶段使用内存
        )

    async def run(self) -> List[BaseMessage]:
        """执行代码相关任务

        Returns:
            消息列表（LangChain 格式）
        """
        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            *self.get_context_messages(),
            HumanMessage(content=self.user_message)
        ]

        # 调用 agent（自动工具选择和执行）
        result = await self.agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": f"{self.session.user_id}_{self.session.channel_id}"}}
        )

        return result["messages"]
```

- [ ] **Step 3: 运行静态检查**

```bash
python -m py_compile src/features/code/code_agent.py
```
Expected: 无错误

---

### Task 4: 更新 Prompts

**Files:**
- Modify: `src/features/prompts.py:17-31`

- [ ] **Step 1: 更新 CODE_AGENT 提示词**

```python
CODE_AGENT = """You are an expert coding assistant with powerful tools.

Capabilities:
- Write clean, well-documented code
- Explain code concepts clearly
- Debug and fix code issues
- Suggest best practices and improvements
- Support multiple programming languages

Available Tools:
- **read_file**: Read file contents (optionally specify line ranges)
- **write_file**: Create or modify files
- **execute_code**: Run Python code and see results

Guidelines:
- Always write production-ready code
- Include comments for complex logic
- Explain your code choices
- Ask for clarification if requirements are unclear
- **Use tools when you need to**:
  - Read existing code before modifying
  - Write code to files instead of just showing snippets
  - Execute code to verify it works
- Think step by step when solving complex problems
"""
```

- [ ] **Step 2: 运行测试验证提示词**

```bash
python -c "from src.features.prompts import Prompts; print(Prompts.get('code_agent'))"
```
Expected: 输出新提示词内容

---

## Chunk 3: 集成测试与验证

### Task 5: 添加 CodeAgent 集成测试

**Files:**
- Create: `tests/integration/test_code_agent_tools.py`

- [ ] **Step 1: 创建集成测试文件**

```python
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
    assert "def" in result.final_reply or "lambda" in result.final_reply


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
```

- [ ] **Step 2: 运行集成测试**

```bash
pytest tests/integration/test_code_agent_tools.py -v
```
Expected: 测试通过

---

### Task 6: 运行现有测试确保兼容性

**Files:**
- 修改：无（验证现有测试）

- [ ] **Step 1: 运行所有现有测试**

```bash
pytest tests/integration/ -v
```
Expected: 所有测试通过（包括 test_workflow.py, test_intent.py, test_multi_turn_context.py）

- [ ] **Step 2: 运行所有测试**

```bash
pytest -v
```
Expected: 所有测试通过

---

## Chunk 4: 清理与文档

### Task 7: 清理与提交

- [ ] **Step 1: 检查代码风格**

```bash
python -m py_compile src/features/code/*.py
```
Expected: 无错误

- [ ] **Step 2: 查看 git 状态**

```bash
git status
```
Expected: 显示修改的文件

- [ ] **Step 3: 查看变更**

```bash
git diff src/features/code/code_agent.py
```

- [ ] **Step 4: 提交变更**

```bash
git add src/features/code/tools.py src/features/code/code_agent.py src/features/prompts.py tests/unit/features/code/test_tools.py tests/integration/test_code_agent_tools.py
git commit -m "feat(code_agent): 使用 create_agent 实现工具调用能力

- 新增 tools.py: read_file, write_file, execute_code
- 改造 code_agent.py: 使用 create_agent + MemorySaver
- 更新 prompts: 说明工具使用指南
- 添加单元测试和集成测试
- 保持与现有架构兼容"
```

---

## 验证清单

完成以上任务后，验证以下功能：

- [ ] 工具可以独立调用
- [ ] CodeAgent 可以正确响应代码请求
- [ ] CodeAgent 可以使用工具读写文件
- [ ] CodeAgent 可以执行代码
- [ ] 现有测试全部通过
- [ ] 意图识别正常工作

---

## 参考文档

- 设计文档：`docs/superpowers/specs/2026-03-17-code-agent-create-agent-design.md`
- [LangChain create_agent 文档](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Tools 文档](https://docs.langchain.com/oss/python/langchain/tools)