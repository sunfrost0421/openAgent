# Agent 系统设计文档

## 1. 概述

基于意图识别的多 Agent 路由系统，使用 LangChain 1.0+ 和 LangGraph 实现。

## 2. 系统架构

```
用户请求 → 预处理 → 意图识别 → 执行器 → 后处理
```

## 3. 核心模块设计

### 3.1 意图识别（三层策略）

1. **快捷命令匹配**：优先匹配 @ 开头的命令（如 @code、@plan）
2. **关键词匹配**：基于注册器中定义的关键词做规则匹配（至少匹配 1 个关键词）
3. **LLM 置信度评估**：LLM 对匹配结果做置信度评估，低于 0.6 时转 default_agent

### 3.2 会话管理

**会话 ID**：`user_id + channel_id` 组成会话 ID，实现会话隔离

**会话数据结构**：
```python
Session:
  - session_id: str
  - user_id: str
  - channel_id: str
  - created_at: datetime
  - updated_at: datetime
  - expires_at: datetime
  - turns: List[Turn]

Turn:
  - turn_id: str
  - agent_name: str
  - messages: List[BaseMessage]
  - final_reply: str
  - created_at: datetime
  - is_compressed: bool
```

**上下文压缩策略**：每次保存新轮次时，自动压缩最老的轮次（只保留 final_reply）

**存储接口**：
```python
class BaseSessionStore(ABC):
    async def get_session(self, session_id: str) -> Session: ...
    async def save_session(self, session: Session) -> None: ...
    async def cleanup_expired(self) -> None: ...
```

第一版实现 `MemorySessionStore`，后续可扩展 `DatabaseSessionStore`

**过期机制**：会话有过期时间，定期清理

### 3.3 Agent 设计

**执行器基类**：`base_executor.py` 定义 `async def run()` 接口

**注册器**：`orchestration/registry.py`
- 装饰器 `@register_agent()` 注册 Agent
- 元数据：name、description、keywords、command
- 查询接口：`get_all_agents()`、`get_by_command()`、`get_by_keywords()`

**Agent 列表**：
- `default_agent`：通用聊天
- `code_agent`：代码相关请求
- `plan_agent`：计划管理

**prompts.py**：统一管理所有 Agent 的系统提示词

### 3.4 配置管理

简单的 config 模块（`config/config.py`）：
```python
OPENAI_API_KEY: Optional[str] = "..."
OPENAI_BASE_URL: Optional[str] = "https://coding.dashscope.aliyuncs.com/v1"
DEFAULT_MODEL: str = "qwen3.5-plus"
INTENT_MODEL: str = "qwen3.5-plus"
INTENT_CONFIDENCE_THRESHOLD: float = 0.6
```

## 4. 技术栈

- **语言**：Python
- **框架**：FastAPI（controller）、LangChain 1.0+、LangGraph
- **数据库**：MySQL（第一版内存实现，预留接口）
- **日志**：开源日志组件
- **风格**：全程异步（async/await）

## 5. 目录结构

```
src/
├── config/
│   ├── __init__.py
│   └── config.py
├── controller/
│   ├── __init__.py
│   └── bot_controller.py
├── orchestration/
│   ├── __init__.py
│   ├── master_workflow.py
│   ├── base_executor.py
│   └── registry.py
├── agents/
│   ├── __init__.py
│   ├── prompts.py
│   ├── default_agent.py
│   ├── code_agent.py
│   └── plan_agent.py
├── core/
│   ├── __init__.py
│   ├── intent.py
│   ├── session_manager.py
│   └── session_store.py
├── infra/
│   ├── __init__.py
│   ├── database.py
│   ├── llm.py
│   └── logger.py
└── main.py
```

## 6. 测试策略

核心模块的单元测试（pytest + pytest-asyncio）：
- 意图识别
- 会话管理器
- workflow 核心逻辑