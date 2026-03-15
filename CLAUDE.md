# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作提供指导。

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
├── controller/        # FastAPI 入口
│   └── bot_controller.py
├── orchestration/     # 工作流编排
│   ├── master_workflow.py   # 主流程：预处理 → 意图识别 → 执行 → 后处理
│   ├── base_executor.py     # 所有 Agent 的基类
│   └── registry.py          # 使用装饰器注册 Agent
├── agents/            # 专用 Agent
│   ├── default_agent.py     # 意图不清晰时的默认 Agent
│   ├── code_agent.py        # 代码相关任务
│   ├── plan_agent.py        # 计划与任务管理
│   └── prompts.py           # 系统提示词
├── core/              # 核心业务逻辑
│   ├── intent.py              # 三层意图识别
│   ├── session_manager.py     # 会话生命周期管理
│   ├── session_store.py       # Session/Turn 数据模型
│   └── memory_session_store.py # 内存会话存储
└── infra/             # 基础设施
    ├── llm.py               # LLM 客户端工厂
    ├── database.py          # 数据库连接 (SQLAlchemy)
    └── logger.py            # 日志配置
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
```python
@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求",
    keywords=["代码", "编程", "function", "class"],
    command="@code"
)
class CodeAgent(BaseExecutor):
    async def run(self) -> List[BaseMessage]:
        ...
```

**请求流程**:
```
用户输入 → BotController → MasterWorkflow
       → IntentRecognizer (命令 → 关键词 → LLM)
       → Agent Executor → SessionManager (保存轮次)
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
- Agent 注册是副作用操作：需要导入 agents 模块来填充注册表
- 测试文件必须导入 `src.agents` 以确保测试前 Agent 已注册