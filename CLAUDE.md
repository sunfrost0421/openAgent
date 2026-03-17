# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作提供指导，请全程使用中文与用户对话。

## 构建和开发命令

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/integration/test_intent.py
pytest tests/integration/test_workflow.py

# 详细输出模式
pytest -v

# 启动应用
python main.py

# 或直接用 uvicorn 启动
uvicorn main:app --host=0.0.0.0 --port=8000
```

## 架构概述

这是一个基于意图识别的**多 Agent 系统**，请求会被路由到不同的子 Agent 处理。

### 技术栈
- **语言**: Python
- **框架**: FastAPI (控制器层)
- **LLM 框架**: LangChain (1.0 以后版本)
- **LLM 提供商**: 阿里云通义千问 (qwen3.5-plus 模型)
- **数据库**: MySQL (计划中), 当前使用 SQLAlchemy + 内存 SQLite

### 目录结构

```
src/
├── config/            # 配置层（最底层，无内部依赖）
│   └── config.py
│
├── infra/             # 基础设施层（仅依赖 config）
│   ├── llm.py               # LLM 客户端工厂
│   ├── database.py          # 数据库连接 (SQLAlchemy)
│   └── logger.py            # 日志配置
│
├── core/              # 领域层（依赖 infra）
│   ├── __init__.py          # 统一导出
│   ├── types.py             # 共享类型定义 (IntentMatch, IntentResult)
│   ├── workflow/            # 【工作流相关】
│   │   ├── __init__.py
│   │   ├── master.py        # MasterWorkflow (主工作流)
│   │   ├── registry.py      # AgentRegistry (Agent 注册)
│   │   ├── intent.py        # IntentRecognizer (意图识别)
│   │   ├── executor.py      # BaseExecutor (执行器基类)
│   │   └── types.py         # 共享类型 (AgentMetadata, IntentMatch, IntentResult)
│   └── session/             # 【会话管理相关】
│       ├── __init__.py
│       ├── models.py        # Session/Turn 数据模型
│       ├── store.py         # MemorySessionStore 存储实现
│       └── manager.py       # SessionManager 生命周期管理
│
├── services/          # 服务层（依赖 core）
│   ├── prompts.py             # 系统提示词
│   └── agents/
│       ├── __init__.py
│       ├── default_agent.py   # 意图不清晰时的默认 Agent
│       ├── code_agent.py      # 代码相关任务
│       └── plan_agent.py      # 计划与任务管理
│
├── controller/        # 接口层（依赖 services）
│   ├── bot_controller.py      # FastAPI 入口
│   └── schemas.py             # Pydantic 请求/响应模型
│
└── main.py            # 应用入口，显式注册 Agent
```

### 依赖关系

```
controller → services → core → infra → config
```

### 核心设计模式

**意图识别（三层策略）**:
1. **命令匹配**: `@command` 前缀命令 (100% 置信度)
2. **关键词匹配**: 语义关键词 + 置信度评分 (0.3-0.8)
3. **LLM 评估**: 验证关键词匹配的语义相关性

**会话管理**:
- 会话 ID = `user_id_channel_id` 实现隔离
- 基于轮次 (Turn) 的存储，支持上下文压缩
- 保留最近 N 轮的完整消息历史，更早的轮次仅保留最终回复
- 可配置的超时时间 (默认 30 分钟)

**Agent 注册**:

新的架构中，Agent 通过装饰器注册到 `agent_registry`，然后在 `main.py` 的 `lifespan` 函数中显式同步到 `intent_recognizer`：

```python
# src/features/code/code_agent.py
@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求",
    keywords=["代码", "编程", "function", "class"],
    command="@code"
)
class CodeAgent(BaseExecutor):
    async def run(self) -> List[BaseMessage]:
        ...

# main.py - lifespan 函数中显式注册
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)
```

**请求流程**:
```
用户输入 → BotController → MasterWorkflow (core/workflow/master.py)
       → IntentRecognizer (core/workflow/intent.py)
       → Agent Executor (services/agents/*) → SessionManager (保存轮次)
       → 响应
```

### 配置

`src/config/config.py` 中的关键配置:
- `OPENAI_API_KEY` / `OPENAI_BASE_URL`: LLM 凭证 (阿里云 DashScope)
- `DEFAULT_MODEL` / `INTENT_MODEL`: 模型选择
- `SESSION_TIMEOUT_MINUTES`: 会话过期时间
- `CONTEXT_KEEP_TURNS`: 保留完整上下文的轮次数

### 测试注意事项

- 测试使用 `pytest-asyncio`,配置为 `asyncio_mode = "auto"`
- Agent 注册是副作用操作：需要导入 `src.services.agents` 模块来填充注册表
- 测试文件必须在导入后显式注册 Agent 到 `intent_recognizer`:

```python
from src.features.code import code_agent  # noqa: F401
from src.features.plan import plan_agent
from src.features.default import default_agent
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer

# 显式注册所有 Agent 到意图识别器
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)
```

### 向后兼容

旧的导入路径已废弃，请使用新的模块结构：
- `src.core.orchestration.*` → 已删除，使用 `src.core.workflow.*`
- `src.core.session.session_store` → 已删除，使用 `src.core.session.models`
- `src.core.session.memory_store` → 已删除，使用 `src.core.session.store`
- `src.core.session.session_manager` → 已删除，使用 `src.core.session.manager`