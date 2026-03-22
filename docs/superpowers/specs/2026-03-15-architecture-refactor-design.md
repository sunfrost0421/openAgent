# 架构重构设计文档

**日期**: 2026-03-15
**主题**: 多 Agent 系统架构依赖关系优化

---

## 1. 现状分析

### 1.1 当前目录结构

```
src/
├── controller/        # FastAPI 入口
│   └── bot_controller.py
├── orchestration/     # 工作流编排
│   ├── master_workflow.py
│   ├── base_executor.py
│   └── registry.py
├── agents/            # 专用 Agent
│   ├── default_agent.py
│   ├── code_agent.py
│   ├── plan_agent.py
│   └── prompts.py
├── core/              # 核心业务逻辑
│   ├── intent.py
│   ├── session_manager.py
│   ├── session_store.py
│   └── memory_session_store.py
└── infra/             # 基础设施
    ├── llm.py
    ├── database.py
    └── logger.py
```

### 1.2 完整文件清单

| 文件 | 当前职责 | 问题 |
|------|----------|------|
| `config/config.py` | 配置数据类 | 被跨层依赖，无明确层级 |
| `infra/llm.py` | LLM 工厂 | 依赖 config |
| `infra/database.py` | 数据库管理器 | 依赖 config，当前为内存实现 |
| `infra/logger.py` | 日志配置 | 无依赖 |
| `core/intent.py` | 意图识别器 | 依赖 infra/llm，被 registry 直接操作 |
| `core/session_store.py` | Session/Turn 数据模型 | 无依赖 |
| `core/session_manager.py` | 会话管理器 | 依赖 core/session_store |
| `core/memory_session_store.py` | 内存会话存储 | 依赖 core/session_store |
| `orchestration/base_executor.py` | Agent 基类 | 依赖 core/session_store |
| `orchestration/registry.py` | Agent 注册表 | 直接操作 intent_recognizer，耦合高 |
| `orchestration/master_workflow.py` | 主工作流 | 依赖过多（registry, intent, session_manager） |
| `agents/*.py` | 具体 Agent 实现 | 依赖 orchestration + infra |
| `agents/prompts.py` | 提示词管理 | 无依赖，纯数据 |
| `controller/bot_controller.py` | FastAPI 路由 | 依赖 master_workflow |
| `main.py` | 应用入口 | 隐式导入 agents 触发副作用 |

### 1.2 发现的架构问题

#### 问题 1：注册机制耦合

`registry.py` 直接调用 `intent.intent_recognizer.register_agent()`，导致 Agent 注册时产生副作用依赖：

```python
# src/orchestration/registry.py
def decorator(cls: Type[BaseExecutor]) -> Type[BaseExecutor]:
    self._executors[name] = cls
    metadata = AgentMetadata(...)
    intent.intent_recognizer.register_agent(metadata)  # 直接依赖全局单例
    return cls
```

#### 问题 2：全局单例隐式依赖

多个模块依赖全局单例，难以测试和替换：
- `intent_recognizer` (src/core/intent.py)
- `agent_registry` (src/orchestration/registry.py)
- `session_manager` (src/core/session_manager.py)
- `master_workflow` (src/orchestration/master_workflow.py)

#### 问题 3：依赖方向混乱

```
agents/code_agent.py
  └── orchestration/registry.py
        └── core/intent.py  (通过副作用)

orchestration/master_workflow.py
  └── orchestration/registry.py
  └── core/session_manager.py
  └── core/intent.py
```

`orchestration` 层本应是应用编排层，但 `registry.py` 却直接操作 `core/intent.py` 的内部实现。

#### 问题 4：配置模块被跨层依赖

`src/config/config.py` 被 infra、core、orchestration 多个层次依赖，但本身没有明确的层级定位。

---

## 2. 目标架构

### 2.1 分层原则

1. **依赖单向**：上层可依赖下层，下层不可依赖上层
2. **接口隔离**：层与层之间通过接口通信，不直接依赖具体实现
3. **职责清晰**：每层有明确的职责边界

### 2.2 新目录结构

```
src/
├── config/            # 配置层（最底层，无内部依赖）
│   └── config.py      # Config 数据类 + 全局实例
│
├── infra/             # 基础设施层（仅依赖 config）
│   ├── __init__.py
│   ├── llm.py         # LLM 工厂函数 (create_llm, create_intent_llm)
│   ├── database.py    # 数据库连接 (DatabaseManager)
│   └── logger.py      # 日志配置 (setup_logger)
│
├── core/              # 领域层（依赖 infra，核心业务模型）
│   ├── __init__.py
│   ├── types.py       # 共享类型定义 (AgentMetadata, IntentResult, IntentMatch)
│   ├── session.py     # Session, Turn, BaseSessionStore 数据模型
│   ├── intent.py      # IntentRecognizer 意图识别器
│   ├── session_manager.py  # SessionManager 会话管理器
│   ├── memory_store.py     # MemorySessionStore 内存实现
│   └── executor.py    # BaseExecutor 抽象基类
│
├── services/          # 服务层（依赖 core，业务服务与 Agent 实现）
│   ├── __init__.py
│   ├── registry.py    # AgentRegistry（只管理元数据，不操作 intent_recognizer）
│   ├── workflow.py    # MasterWorkflow 主工作流
│   ├── prompts.py     # 系统提示词管理 (Prompts 类)
│   └── agents/        # 具体 Agent 实现
│       ├── __init__.py
│       ├── default_agent.py  # DefaultAgent
│       ├── code_agent.py     # CodeAgent
│       └── plan_agent.py     # PlanAgent
│
└── controller/        # 接口层（依赖 services，API 入口）
    ├── __init__.py
    ├── bot_controller.py  # FastAPI Router
    └── schemas.py         # Pydantic 请求/响应模型
```

### 2.3 依赖关系图

```
controller/
    └── services/
          ├── core/
          │     └── infra/
          │           └── config/
          └── services/agents/
```

### 2.4 各层职责详解

#### config 层
- **职责**：定义系统配置数据类，提供全局配置实例
- **依赖**：无
- **导出**：`Config` 数据类，`get_config()` 函数

#### infra 层
- **职责**：基础设施实现（LLM、数据库、日志）
- **依赖**：config
- **导出**：
  - `llm.py`: `create_llm(model, **kwargs)`, `create_intent_llm()`
  - `database.py`: `DatabaseManager`, `db_manager`
  - `logger.py`: `setup_logger(name)`

#### core 层
- **职责**：核心领域模型和业务逻辑
- **依赖**：infra, config
- **导出**：
  - `types.py`: `AgentMetadata`, `IntentResult`, `IntentMatch`
  - `session.py`: `Session`, `Turn`, `BaseSessionStore`(ABC)
  - `intent.py`: `IntentRecognizer`, `intent_recognizer`(全局实例)
  - `session_manager.py`: `SessionManager`, `session_manager`(全局实例)
  - `memory_store.py`: `MemorySessionStore`
  - `executor.py`: `BaseExecutor`(ABC)

#### services 层
- **职责**：业务服务编排，Agent 具体实现
- **依赖**：core, infra, config
- **导出**：
  - `registry.py`: `AgentRegistry`, `agent_registry`(全局实例)
  - `workflow.py`: `MasterWorkflow`, `master_workflow`(全局实例)
  - `prompts.py`: `Prompts` 类
  - `agents/`: `DefaultAgent`, `CodeAgent`, `PlanAgent`

#### controller 层
- **职责**：API 接口定义，HTTP 请求处理
- **依赖**：services, core
- **导出**：
  - `schemas.py`: `ChatRequest`, `ChatResponse`
  - `bot_controller.py`: `router` (FastAPI APIRouter)

---

## 3. 关键改动

### 3.1 Registry 职责简化

**当前**：
```python
# src/orchestration/registry.py
def decorator(cls):
    self._executors[name] = cls
    intent.intent_recognizer.register_agent(metadata)  # 直接操作全局单例
    return cls
```

**重构后**：
```python
# src/features/registry.py
class AgentRegistry:
    def __init__(self):
        self._executors: Dict[str, Type[BaseExecutor]] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, name: str, description: str, keywords: List[str],
                 command: Optional[str] = None) -> Callable:
        def decorator(cls: Type[BaseExecutor]) -> Type[BaseExecutor]:
            self._executors[name] = cls
            self._metadata[name] = AgentMetadata(name, description, keywords, command)
            # 不再直接操作 intent_recognizer
            return cls
        return decorator

    def get_executor(self, name: str) -> Type[BaseExecutor]:
        return self._executors.get(name)

    def get_all_metadata(self) -> Dict[str, AgentMetadata]:
        return self._metadata.copy()
```

### 3.2 启动时显式注册

**当前**：
```python
# main.py - 隐式依赖导入触发副作用
from src.agents import default_agent, code_agent, plan_agent  # noqa: F401
```

**重构后**：

```python
# main.py - 显式注册
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer

# 导入 code 模块（触发装饰器注册到 registry）
from src.features.code import code_agent
from src.features.plan import plan_agent
from src.features.default import default_agent

# 显式将 registry 中的元数据同步到 intent_recognizer
for name, metadata in agent_registry.get_all_metadata().items():
    intent_recognizer.register_agent(metadata)
```

### 3.3 新增 types.py 集中类型定义

**新增** `src/core/types.py`：

```python
# 共享类型定义，避免循环导入
from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel, Field

@dataclass
class AgentMetadata:
    name: str
    description: str
    keywords: List[str]
    command: Optional[str] = None

class IntentMatch(BaseModel):
    agent_name: str = Field(description="匹配的 Agent 名称")
    confidence: float = Field(description="置信度，0-1 之间")
    reason: str = Field(description="匹配原因")

class IntentResult(BaseModel):
    agent_name: str
    confidence: float
    reason: str
    match_type: str  # "command", "keyword", "llm", "default"
```

### 3.4 文件移动对照表

| 原路径 | 新路径 | 改动说明 |
|--------|--------|----------|
| `src/config/config.py` | `src/config/config.py` | 不变 |
| `src/infra/llm.py` | `src/infra/llm.py` | 不变 |
| `src/infra/database.py` | `src/infra/database.py` | 不变 |
| `src/infra/logger.py` | `src/infra/logger.py` | 不变 |
| `src/core/session_store.py` | `src/core/session.py` | 重命名，只保留数据模型 |
| `src/core/session_manager.py` | `src/core/session_manager.py` | 不变，导入路径更新 |
| `src/core/memory_session_store.py` | `src/core/memory_store.py` | 重命名 |
| `src/core/intent.py` | `src/core/intent.py` | 移除类型定义，从 types.py 导入 |
| `src/orchestration/base_executor.py` | `src/core/executor.py` | 移动到 core 层 |
| `src/orchestration/registry.py` | `src/services/registry.py` | 移除对 intent_recognizer 的直接操作 |
| `src/orchestration/master_workflow.py` | `src/services/workflow.py` | 重命名，导入路径更新 |
| `src/agents/prompts.py` | `src/services/prompts.py` | 移动到 services 层 |
| `src/agents/default_agent.py` | `src/services/agents/default_agent.py` | 移动到 services/agents/ |
| `src/agents/code_agent.py` | `src/services/agents/code_agent.py` | 移动到 services/agents/ |
| `src/agents/plan_agent.py` | `src/services/agents/plan_agent.py` | 移动到 services/agents/ |
| `src/controller/bot_controller.py` | `src/controller/bot_controller.py` | 不变，导入路径更新 |
| `src/controller/__init__.py` | `src/controller/schemas.py` | 新增，定义 ChatRequest/ChatResponse |

---

## 4. 测试策略

### 4.1 单元测试隔离

分层后各层可独立测试：

```python
# tests/unit/domain/test_intent.py
def test_intent_recognizer_keyword_match():
    recognizer = IntentRecognizer()  # 可直接实例化，不依赖全局单例
    recognizer.register_agent(AgentMetadata(...))
    result = await recognizer.recognize("帮我写个函数")
    assert result.agent_name == "code_agent"
```

### 4.2 集成测试

```python
# tests/integration/test_workflow.py
async def test_full_workflow():
    # 使用依赖注入组装各组件
    store = MemorySessionStore()
    session_manager = SessionManager(store)
    recognizer = IntentRecognizer()
    workflow = MasterWorkflow(session_manager, recognizer)

    # 注册测试用 Agent
    ...
```

---

## 5. 迁移步骤

1. **Phase 1**: 创建新目录结构，移动文件（不改代码）
2. **Phase 2**: 修改 `registry.py` 移除对 `intent_recognizer` 的直接调用
3. **Phase 3**: 修改 `main.py` 显式注册 Agent
4. **Phase 4**: 更新所有导入路径
5. **Phase 5**: 运行测试验证

---

## 6. 验收标准

- [ ] 所有现有测试通过
- [ ] 依赖关系单向（可通过脚本或工具验证）
- [ ] 单元测试可独立 mock 各层组件
- [ ] `main.py` 显式组合所有依赖，无隐式副作用