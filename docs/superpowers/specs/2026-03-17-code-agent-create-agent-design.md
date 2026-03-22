# CodeAgent 改造设计文档 - 基于 LangChain create_agent

**日期**: 2026-03-17
**状态**: 设计中
**作者**: Claude Code
**评审**: 待评审

---

## 1. 概述

### 1.1 改造目标

将现有 `CodeAgent` 从直接调用 LLM 改造为使用 LangChain `create_agent` + `Tools` 模式，实现以下能力：

1. **工具调用能力**: 使 Agent 能够执行实际操作（文件读写、代码执行）
2. **利用 Memory 特性**: 为 CodeAgent 单独配置 Checkpointer，实现会话持久化
3. **架构集成评估**: 评估当前架构与 LangChain 生态的集成可能性

### 1.2 改造范围

| 模块 | 是否改造 | 说明 |
|------|----------|------|
| `CodeAgent.run()` | ✅ 改造 | 核心改造点 |
| `MasterWorkflow` | ❌ 不变 | 保持现有流程 |
| `IntentRecognizer` | ❌ 不变 | 保持现有逻辑 |
| `SessionManager` | ❌ 不变 | 保持现有存储 |
| `default_agent` | ❌ 不变 | 不涉及 |
| `plan_agent` | ❌ 不变 | 不涉及 |

---

## 2. 架构设计

### 2.1 当前架构

```
用户输入 → MasterWorkflow → IntentRecognizer → CodeAgent → llm.ainvoke() → 响应
                                              ↓
                                         直接调用 LLM
                                         无工具能力
```

### 2.2 改造后架构

```
用户输入 → MasterWorkflow → IntentRecognizer → CodeAgent → create_agent → 工具调度 → 响应
                                              ↓              ↓
                                         继承 BaseExecutor  [read_file, write_file, execute_code]
                                                              ↓
                                                         Checkpointer (可选持久化)
```

### 2.3 核心变更

```python
# 改造前
class CodeAgent(BaseExecutor):
    async def run(self) -> List[BaseMessage]:
        llm = create_llm()
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            *self.get_context_messages(),
            HumanMessage(content=self.user_message)
        ]
        response = await llm.ainvoke(messages)
        return [response]

# 改造后
class CodeAgent(BaseExecutor):
    def __init__(self, session, user_message, session_manager=None):
        super().__init__(session, user_message, session_manager)
        # 初始化工具和 agent
        self.tools = self._create_tools()
        self.agent = create_agent(
            model=create_llm(),
            tools=self.tools,
            checkpointer=self._create_checkpointer()  # 混合方案：仅 CodeAgent 使用
        )

    async def run(self) -> List[BaseMessage]:
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            *self.get_context_messages(),
            HumanMessage(content=self.user_message)
        ]
        result = await self.agent.ainvoke({"messages": messages})
        return result["messages"]
```

---

## 3. 工具设计

### 3.1 工具列表

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `read_file` | 读取文件内容 | `path: str, lines: Optional[Tuple[int, int]]` | `str` |
| `write_file` | 写入/创建文件 | `path: str, content: str, mode: str` | `str` |
| `execute_code` | 执行 Python 代码 | `code: str, timeout: int` | `ExecutionResult` |

### 3.2 工具实现

```python
from langchain.tools import tool
from pathlib import Path
import subprocess
import tempfile

# 项目根目录（安全边界 - 功能优先阶段可放宽）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

@tool
def read_file(path: str, lines: Optional[Tuple[int, int]] = None) -> str:
    """读取文件内容

    Args:
        path: 文件路径（相对于项目根目录）
        lines: 可选，指定行范围 (start, end)

    Returns:
        文件内容
    """
    # 功能优先阶段：允许绝对路径
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path

    if not file_path.exists():
        return f"Error: File not found: {path}"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if lines:
        line_list = content.split('\n')[lines[0]:lines[1]]
        return '\n'.join(line_list)

    return content


@tool
def write_file(path: str, content: str, mode: str = 'w') -> str:
    """写入/创建文件

    Args:
        path: 文件路径
        content: 文件内容
        mode: 写入模式 ('w' 覆盖，'a' 追加)

    Returns:
        操作结果
    """
    file_path = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w' if mode == 'w' else 'a', encoding='utf-8') as f:
        f.write(content)

    return f"Successfully wrote to {path}"


@tool
def execute_code(code: str, timeout: int = 30) -> str:
    """执行 Python 代码

    Args:
        code: Python 代码
        timeout: 超时时间（秒）

    Returns:
        执行结果（stdout/stderr）
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
            timeout=timeout
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
```

---

## 4. Memory 持久化设计

### 4.1 混合方案

采用"混合方案"：保持现有 `SessionManager` 不变，仅为 `CodeAgent` 配置 LangChain `Checkpointer`，实现双轨制：

- **短期记忆**: 现有 `SessionManager`（内存 SQLite）- 用于上下文获取
- **长期记忆**: LangChain `MemorySaver` - 用于 Agent 内部状态持久化

### 4.2 Checkpointer 配置

```python
from langgraph.checkpoint.memory import MemorySaver
# 或使用 SQLiteSaver 实现持久化

def _create_checkpointer(self):
    """为 CodeAgent 创建 Checkpointer"""
    # 方案 A: 内存 Checkpointer（开发阶段）
    return MemorySaver()

    # 方案 B: SQLite Checkpointer（生产阶段）
    # from langgraph.checkpoint.sqlite import SqliteSaver
    # return SqliteSaver.from_conn_string("code_agent_memory.db")
```

### 4.3 与现有 SessionManager 的集成

```python
# MasterWorkflow 保持不变
async def _execute_agent(self, user_id, channel_id, message, intent_result):
    session = await self._session_manager.get_or_create_session(user_id, channel_id)

    executor_class = agent_registry.get_executor(intent_result.agent_name)
    executor = executor_class(
        session=session,
        user_message=message,
        session_manager=self._session_manager  # 传入现有管理器
    )

    messages = await executor.run()
    # ... 保存会话逻辑不变
```

---

## 5. 架构集成评估

### 5.1 LangChain 特性支持评估

| LangChain 特性 | 当前支持 | 集成难度 | 优先级 | 备注 |
|---------------|----------|----------|--------|------|
| `create_agent` | ❌ → ✅ | 中 | 高 | 本次改造核心 |
| `@tool` 装饰器 | ❌ → ✅ | 低 | 高 | 工具定义 |
| `MemorySaver` | ❌ → ✅ | 中 | 中 | 混合方案 |
| `SqliteSaver` | ❌ → ✅ | 中 | 低 | 后续可选 |
| `PostgresSaver` | ❌ | 高 | 低 | 与 MySQL 计划冲突 |
| `LangGraph` | ❌ | 高 | 低 | 需重构主流程 |
| `Middleware` | ❌ | 中 | 低 | 需 Runnable 接口 |
| `stream()` | ❌ → ⚠️ | 中 | 中 | 需改造响应处理 |

### 5.2 当前架构优势

1. **意图识别三层策略**: 命令匹配 → 关键词匹配 → LLM 评估，这是自研优势
2. **会话隔离**: `user_id_channel_id` 设计清晰
3. **分层架构**: controller → services → core → infra，依赖清晰

### 5.3 集成建议

1. **短期**: 完成本次改造，获得 Tools 能力
2. **中期**: 评估是否将 `SessionManager` 迁移到 LangChain `MemorySaver`
3. **长期**: 如需复杂工作流，考虑引入 `LangGraph`

---

## 6. 实现清单

### 6.1 任务列表

- [ ] 创建工具定义文件 `src/features/code/tools.py`
- [ ] 修改 `CodeAgent` 实现，使用 `create_agent`
- [ ] 添加 `langgraph` 依赖（提供 Checkpointer）
- [ ] 编写工具测试用例
- [ ] 更新 `Prompts.CODE_AGENT` 提示词，说明工具能力
- [ ] 运行现有测试确保兼容性

### 6.2 文件结构

```
src/features/code/
├── __init__.py
├── code_agent.py      # 修改：使用 create_agent
└── tools.py           # 新增：工具定义
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# tests/unit/features/code/test_tools.py
import pytest
from src.features.code.tools import read_file, write_file, execute_code

async def test_read_file():
    result = await read_file.ainvoke({"path": "test.txt"})
    assert "Error" not in result

async def test_execute_code():
    result = await execute_code.ainvoke({"code": "print('hello')"})
    assert "hello" in result
```

### 7.2 集成测试

```python
# tests/integration/test_code_agent.py
async def test_code_agent_with_tools():
    workflow = MasterWorkflow()
    result = await workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="创建一个文件并写入 hello world"
    )
    assert result.agent_name == "code_agent"
```

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `create_agent` 与现有架构不兼容 | 高 | 选项 1 方案风险低，保持继承关系 |
| 工具执行安全问题 | 中 | 功能优先，后续添加沙箱 |
| Checkpointer 增加复杂性 | 低 | 可选配置，默认使用内存 |
| 依赖增加 (`langgraph`) | 低 | 官方依赖，维护良好 |

---

## 9. 后续演进

### 9.1 阶段 2：安全增强

- [ ] 添加文件访问白名单
- [ ] 代码执行沙箱（Docker 或 subprocess 限制）
- [ ] 敏感操作确认机制

### 9.2 阶段 3：能力扩展

- [ ] 添加 `list_directory` 工具
- [ ] 添加 `explain_code` 工具（LLM 调用）
- [ ] 添加 `search_code` 工具（代码搜索）

### 9.3 阶段 4：架构演进（可选）

- [ ] 评估迁移到 `LangGraph` 的价值
- [ ] 统一 Memory 管理（迁移到 Checkpointer）
- [ ] 支持流式输出

---

## 10. 参考文档

- [LangChain create_agent 文档](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Tools 文档](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph Checkpointer](https://docs.langchain.com/oss/python/langgraph/checkpointer)