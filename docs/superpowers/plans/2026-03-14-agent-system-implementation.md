# Agent 系统实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个基于意图识别的多 Agent 路由系统，支持快捷命令、关键词匹配和 LLM 置信度评估三层意图识别策略。

**Architecture:** 系统采用分层架构：Controller 层接收请求 → 预处理 → 意图识别 → 执行器 → 后处理。会话管理负责保存和压缩上下文，注册器负责 Agent 的发现和路由。

**Tech Stack:** Python, FastAPI, LangChain 1.0+, LangGraph, MySQL(预留), pytest+pytest-asyncio

---

## Chunk 1: 基础设施层 (Infra)

本 Chunk 实现基础设施层，包括配置模块、LLM 封装、日志配置和数据库连接（预留）。

### Task 1.1: 配置模块 (`config/config.py`)

**Files:**
- Create: `src/config/__init__.py`
- Create: `src/config/config.py`

- [ ] **Step 1: 创建配置模块**

```python
# src/config/config.py
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """系统配置"""

    # LLM 配置
    OPENAI_API_KEY: Optional[str] = "sk-sp-b6c188b0bd9d478ca5fba8b8b34cc5f1"
    OPENAI_BASE_URL: Optional[str] = "https://coding.dashscope.aliyuncs.com/v1"
    DEFAULT_MODEL: str = "qwen3.5-plus"
    INTENT_MODEL: str = "qwen3.5-plus"

    # 意图识别配置
    INTENT_CONFIDENCE_THRESHOLD: float = 0.6

    # 会话管理配置
    SESSION_TIMEOUT_MINUTES: int = 30
    CONTEXT_KEEP_TURNS: int = 3  # 保留多少轮的完整上下文

    @classmethod
    def get(cls) -> "Config":
        """获取全局配置实例"""
        return _global_config


_global_config = Config()
```

```python
# src/config/__init__.py
from .config import Config

__all__ = ["Config"]
```

- [ ] **Step 2: 验证配置可导入**

Run: `cd D:\workplace\qrc\new3 && python -c "from src.config import Config; print(Config.get())"`
Expected: 输出 Config 实例

- [ ] **Step 3: 提交**

```bash
git add src/config/
git commit -m "feat: add config module"
```

---

### Task 1.2: LLM 封装 (`infra/llm.py`)

**Files:**
- Create: `src/infra/__init__.py`
- Create: `src/infra/llm.py`

- [ ] **Step 1: 创建 LLM 封装**

```python
# src/infra/llm.py
"""LLM 封装模块"""

from langchain_openai import ChatOpenAI
from src.config import Config


def create_llm(model: str | None = None, **kwargs) -> ChatOpenAI:
    """创建 LLM 实例

    Args:
        model: 模型名称，默认使用 DEFAULT_MODEL
        **kwargs: 传递给 ChatOpenAI 的其他参数

    Returns:
        ChatOpenAI 实例
    """
    config = Config.get()

    return ChatOpenAI(
        model=model or config.DEFAULT_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
        **kwargs
    )


def create_intent_llm() -> ChatOpenAI:
    """创建意图识别专用 LLM 实例

    Returns:
        ChatOpenAI 实例，使用 INTENT_MODEL
    """
    return create_llm(model=Config.get().INTENT_MODEL, temperature=0)
```

- [ ] **Step 2: 验证 LLM 可创建**

Run: `cd D:\workplace\qrc\new3 && python -c "from src.infra.llm import create_llm; llm = create_llm(); print(type(llm))"`
Expected: 输出 `<class 'langchain_openai.chat_models.base.ChatOpenAI'>`

- [ ] **Step 3: 提交**

```bash
git add src/infra/
git commit -m "feat: add LLM wrapper"
```

---

### Task 1.3: 日志配置 (`infra/logger.py`)

**Files:**
- Modify: `src/infra/__init__.py`
- Create: `src/infra/logger.py`

- [ ] **Step 1: 创建日志配置**

```python
# src/infra/logger.py
"""日志配置模块"""

import logging
import sys


def setup_logger(name: str = "agent_system") -> logging.Logger:
    """设置并返回 logger

    Args:
        name: logger 名称

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# 全局 logger
logger = setup_logger()
```

- [ ] **Step 2: 更新 infra __init__.py**

```python
# src/infra/__init__.py
from .logger import logger, setup_logger

__all__ = ["logger", "setup_logger"]
```

- [ ] **Step 3: 验证日志可工作**

Run: `cd D:\workplace\qrc\new3 && python -c "from src.infra import logger; logger.info('test')"`
Expected: 输出日志信息

- [ ] **Step 4: 提交**

```bash
git add src/infra/__init__.py src/infra/logger.py
git commit -m "feat: add logger configuration"
```

---

### Task 1.4: 数据库连接（预留）(`infra/database.py`)

**Files:**
- Modify: `src/infra/__init__.py`
- Create: `src/infra/database.py`

- [ ] **Step 1: 创建数据库连接占位**

```python
# src/infra/database.py
"""数据库连接模块 - 第一版为内存实现，后续扩展到 MySQL"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import Config


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str | None = None):
        """初始化数据库管理器

        Args:
            database_url: 数据库连接 URL，为 None 时使用内存 SQLite
        """
        self.database_url = database_url or "sqlite+aiosqlite:///:memory:"
        self.engine = None
        self.async_session_maker = None

    async def init(self) -> None:
        """初始化数据库连接"""
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()

    def get_session_maker(self) -> async_sessionmaker:
        """获取 session maker"""
        if self.async_session_maker is None:
            raise RuntimeError("Database not initialized")
        return self.async_session_maker


# 全局数据库管理器实例
db_manager = DatabaseManager()
```

- [ ] **Step 2: 更新 infra __init__.py**

```python
# src/infra/__init__.py
from .logger import logger, setup_logger
from .database import DatabaseManager, db_manager

__all__ = ["logger", "setup_logger", "DatabaseManager", "db_manager"]
```

- [ ] **Step 3: 提交**

```bash
git add src/infra/__init__.py src/infra/database.py
git commit -m "feat: add database manager placeholder"
```

---

## Chunk 2: 核心层 (Core)

本 Chunk 实现核心业务逻辑，包括会话存储接口、会话管理器、意图识别。

### Task 2.1: 会话存储接口 (`core/session_store.py`)

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/core/session_store.py`

- [ ] **Step 1: 创建会话存储抽象基类**

```python
# src/core/session_store.py
"""会话存储抽象接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from langchain_core.messages import BaseMessage


@dataclass
class Turn:
    """对话轮次"""
    turn_id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    messages: List[BaseMessage] = field(default_factory=list)
    final_reply: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_compressed: bool = False

    def compress(self) -> None:
        """压缩轮次，只保留最终回复"""
        self.is_compressed = True


@dataclass
class Session:
    """会话"""
    session_id: str = ""
    user_id: str = ""
    channel_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=30))
    turns: List[Turn] = field(default_factory=list)

    def add_turn(self, agent_name: str, messages: List[BaseMessage], final_reply: str) -> Turn:
        """添加新轮次，并压缩最老的轮次"""
        # 压缩最老的未压缩轮次
        for turn in self.turns:
            if not turn.is_compressed:
                turn.compress()
                break

        turn = Turn(
            agent_name=agent_name,
            messages=messages,
            final_reply=final_reply
        )
        self.turns.append(turn)
        self.updated_at = datetime.now()
        return turn

    def get_context_messages(self, keep_turns: int = 3) -> List[BaseMessage]:
        """获取上下文消息

        Args:
            keep_turns: 保留完整上下文的轮次数

        Returns:
            用于 LLM 上下文的消息列表
        """
        messages = []
        # 最近的 keep_turns 轮使用完整消息，之前的只使用 final_reply
        for i, turn in enumerate(self.turns):
            if i >= len(self.turns) - keep_turns:
                # 最近的轮次，使用完整消息
                messages.extend(turn.messages)
            else:
                # 较远的轮次，只使用最终回复
                if turn.final_reply:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=turn.final_reply))
        return messages


class BaseSessionStore(ABC):
    """会话存储抽象基类"""

    @abstractmethod
    async def get_session(self, session_id: str) -> Session:
        """获取会话"""
        pass

    @abstractmethod
    async def save_session(self, session: Session) -> None:
        """保存会话"""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        pass
```

- [ ] **Step 2: 更新 core __init__.py**

```python
# src/core/__init__.py
from .session_store import BaseSessionStore, Session, Turn

__all__ = ["BaseSessionStore", "Session", "Turn"]
```

- [ ] **Step 3: 提交**

```bash
git add src/core/
git commit -m "feat: add session store interfaces and models"
```

---

### Task 2.2: 内存会话存储实现 (`core/memory_session_store.py`)

**Files:**
- Modify: `src/core/__init__.py`
- Create: `src/core/memory_session_store.py`

- [ ] **Step 1: 创建内存会话存储实现**

```python
# src/core/memory_session_store.py
"""内存会话存储实现"""

import asyncio
from datetime import datetime
from typing import Dict

from src.core.session_store import BaseSessionStore, Session
from src.infra import logger


class MemorySessionStore(BaseSessionStore):
    """内存会话存储"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._logger = logger.getLogger("MemorySessionStore")

    async def get_session(self, session_id: str) -> Session:
        """获取会话，不存在则创建"""
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session(session_id=session_id)
                self._logger.debug(f"Created new session: {session_id}")
            return self._sessions[session_id]

    async def save_session(self, session: Session) -> None:
        """保存会话"""
        async with self._lock:
            self._sessions[session.session_id] = session
            self._logger.debug(f"Saved session: {session.session_id}")

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        async with self._lock:
            now = datetime.now()
            expired = [
                sid for sid, s in self._sessions.items()
                if s.expires_at < now
            ]
            for sid in expired:
                del self._sessions[sid]
                self._logger.debug(f"Cleaned up expired session: {sid}")
            if expired:
                self._logger.info(f"Cleaned up {len(expired)} expired sessions")


# 全局内存会话存储实例
memory_session_store = MemorySessionStore()
```

- [ ] **Step 2: 更新 core __init__.py**

```python
# src/core/__init__.py
from .session_store import BaseSessionStore, Session, Turn
from .memory_session_store import MemorySessionStore, memory_session_store

__all__ = [
    "BaseSessionStore",
    "Session",
    "Turn",
    "MemorySessionStore",
    "memory_session_store",
]
```

- [ ] **Step 3: 编写单元测试**

Create: `tests/core/test_memory_session_store.py`

```python
# tests/core/test_memory_session_store.py
"""内存会话存储测试"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.core.memory_session_store import MemorySessionStore
from src.core.session_store import Session


@pytest.fixture
def store():
    return MemorySessionStore()


@pytest.mark.asyncio
async def test_get_session_creates_new(store):
    """测试获取不存在的会话会创建新会话"""
    session = await store.get_session("user1_channel1")
    assert session.session_id == "user1_channel1"
    assert session.turns == []


@pytest.mark.asyncio
async def test_get_session_returns_same_instance(store):
    """测试多次获取同一会话返回相同实例"""
    session1 = await store.get_session("user1_channel1")
    session2 = await store.get_session("user1_channel1")
    assert session1 is session2


@pytest.mark.asyncio
async def test_save_session(store):
    """测试保存会话"""
    session = Session(session_id="user1_channel1")
    await store.save_session(session)
    retrieved = await store.get_session("user1_channel1")
    assert retrieved is session


@pytest.mark.asyncio
async def test_cleanup_expired(store):
    """测试清理过期会话"""
    # 创建正常会话
    await store.get_session("user1_channel1")
    # 创建过期会话
    expired_session = Session(session_id="user2_channel2")
    expired_session.expires_at = datetime.now() - timedelta(minutes=1)
    await store.save_session(expired_session)

    await store.cleanup_expired()

    # 正常会话应存在
    assert await store.get_session("user1_channel1") is not None
    # 过期会话应被清理
    sessions = store._sessions
    assert "user2_channel2" not in sessions
```

- [ ] **Step 4: 运行测试**

Run: `cd D:\workplace\qrc\new3 && pytest tests/core/test_memory_session_store.py -v`
Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/core/memory_session_store.py tests/core/
git commit -m "feat: add memory session store implementation"
```

---

### Task 2.3: 会话管理器 (`core/session_manager.py`)

**Files:**
- Modify: `src/core/__init__.py`
- Create: `src/core/session_manager.py`

- [ ] **Step 1: 创建会话管理器**

```python
# src/core/session_manager.py
"""会话管理器"""

from typing import List

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from src.core.session_store import Session, Turn
from src.core.memory_session_store import MemorySessionStore
from src.config import Config


class SessionManager:
    """会话管理器

    负责：
    - 会话的获取和保存
    - 轮次的添加和压缩
    - 上下文消息的提取
    """

    def __init__(self, store: MemorySessionStore | None = None):
        """初始化会话管理器

        Args:
            store: 会话存储实例，默认使用全局 memory_session_store
        """
        self._store = store or MemorySessionStore()
        self._config = Config.get()

    def create_session_id(self, user_id: str, channel_id: str) -> str:
        """创建会话 ID"""
        return f"{user_id}_{channel_id}"

    async def get_or_create_session(
        self, user_id: str, channel_id: str
    ) -> Session:
        """获取或创建会话"""
        session_id = self.create_session_id(user_id, channel_id)
        return await self._store.get_session(session_id)

    async def add_turn(
        self,
        session: Session,
        agent_name: str,
        user_message: str,
        messages: List[BaseMessage],
        final_reply: str,
    ) -> Turn:
        """添加对话轮次

        Args:
            session: 会话实例
            agent_name: 执行 Agent 名称
            user_message: 用户输入消息
            messages: 完整消息列表（包含中间交互）
            final_reply: 最终回复

        Returns:
            添加的 Turn 实例
        """
        # 确保消息列表包含用户输入
        if not messages or not isinstance(messages[0], HumanMessage):
            messages = [HumanMessage(content=user_message), *messages]

        turn = session.add_turn(
            agent_name=agent_name,
            messages=messages,
            final_reply=final_reply
        )

        # 自动压缩最老的未压缩轮次
        self._compress_old_turns(session)

        await self._store.save_session(session)
        return turn

    def _compress_old_turns(self, session: Session) -> None:
        """压缩旧的轮次，只保留最近的 keep_turns 轮完整上下文"""
        keep_turns = self._config.CONTEXT_KEEP_TURNS
        turns_to_compress = max(0, len(session.turns) - keep_turns)

        for i in range(turns_to_compress):
            if not session.turns[i].is_compressed:
                session.turns[i].compress()

    def get_context_messages(self, session: Session) -> List[BaseMessage]:
        """获取会话上下文消息"""
        return session.get_context_messages(
            keep_turns=self._config.CONTEXT_KEEP_TURNS
        )

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        await self._store.cleanup_expired()


# 全局会话管理器实例
session_manager = SessionManager()
```

- [ ] **Step 2: 更新 core __init__.py**

```python
# src/core/__init__.py
from .session_store import BaseSessionStore, Session, Turn
from .memory_session_store import MemorySessionStore, memory_session_store
from .session_manager import SessionManager, session_manager

__all__ = [
    "BaseSessionStore",
    "Session",
    "Turn",
    "MemorySessionStore",
    "memory_session_store",
    "SessionManager",
    "session_manager",
]
```

- [ ] **Step 3: 编写单元测试**

Create: `tests/core/test_session_manager.py`

```python
# tests/core/test_session_manager.py
"""会话管理器测试"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from src.core.session_manager import SessionManager
from src.core.memory_session_store import MemorySessionStore


@pytest.fixture
def manager():
    return SessionManager()


@pytest.mark.asyncio
async def test_create_session_id(manager):
    """测试创建会话 ID"""
    session_id = manager.create_session_id("user1", "channel1")
    assert session_id == "user1_channel1"


@pytest.mark.asyncio
async def test_get_or_create_session(manager):
    """测试获取或创建会话"""
    session = await manager.get_or_create_session("user1", "channel1")
    assert session.session_id == "user1_channel1"


@pytest.mark.asyncio
async def test_add_turn(manager):
    """测试添加轮次"""
    session = await manager.get_or_create_session("user1", "channel1")

    messages = [AIMessage(content="Hello")]
    turn = await manager.add_turn(
        session=session,
        agent_name="default_agent",
        user_message="Hi",
        messages=messages,
        final_reply="Hello! How can I help?",
    )

    assert turn.agent_name == "default_agent"
    assert turn.final_reply == "Hello! How can I help?"
    assert len(session.turns) == 1


@pytest.mark.asyncio
async def test_context_messages(manager):
    """测试上下文消息提取"""
    session = await manager.get_or_create_session("user1", "channel1")

    # 添加多个轮次
    for i in range(5):
        await manager.add_turn(
            session=session,
            agent_name="default_agent",
            user_message=f"Message {i}",
            messages=[AIMessage(content=f"Reply {i}")],
            final_reply=f"Final reply {i}",
        )

    context = manager.get_context_messages(session)
    # 应该包含最近 3 轮的完整消息和之前轮的 final_reply
    assert len(context) > 0
```

- [ ] **Step 4: 运行测试**

Run: `cd D:\workplace\qrc\new3 && pytest tests/core/test_session_manager.py -v`
Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/core/session_manager.py tests/core/test_session_manager.py
git commit -m "feat: add session manager"
```

---

### Task 2.4: 意图识别 (`core/intent.py`)

**Files:**
- Modify: `src/core/__init__.py`
- Create: `src/core/intent.py`

- [ ] **Step 1: 创建意图识别类**

```python
# src/core/intent.py
"""意图识别模块"""

import re
from dataclasses import dataclass
from typing import List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.infra.llm import create_intent_llm
from src.infra import logger
from src.config import Config


@dataclass
class AgentMetadata:
    """Agent 元数据"""
    name: str
    description: str
    keywords: List[str]
    command: Optional[str] = None


class IntentMatch(BaseModel):
    """意图匹配结果"""
    agent_name: str = Field(description="匹配的 Agent 名称")
    confidence: float = Field(description="置信度，0-1 之间")
    reason: str = Field(description="匹配原因")


class IntentResult(BaseModel):
    """意图识别结果"""
    agent_name: str
    confidence: float
    reason: str
    match_type: str  # "command", "keyword", "llm"


class IntentRecognizer:
    """意图识别器

    三层识别策略：
    1. 快捷命令匹配：优先匹配 @ 开头的命令
    2. 关键词匹配：基于注册器中定义的关键词
    3. LLM 置信度评估：LLM 对匹配结果做置信度评估
    """

    def __init__(self):
        self._agents: dict[str, AgentMetadata] = {}
        self._llm = create_intent_llm()
        self._parser = PydanticOutputParser(pydantic_object=IntentMatch)
        self._config = Config.get()
        self._logger = logger.getLogger("IntentRecognizer")

    def register_agent(self, metadata: AgentMetadata) -> None:
        """注册 Agent"""
        self._agents[metadata.name] = metadata
        self._logger.debug(f"Registered agent: {metadata.name}")

    async def recognize(self, message: str) -> IntentResult:
        """识别用户意图

        Args:
            message: 用户输入消息

        Returns:
            意图识别结果
        """
        # 1. 快捷命令匹配
        command_result = self._match_command(message)
        if command_result:
            return command_result

        # 2. 关键词匹配
        keyword_result = self._match_keywords(message)
        if keyword_result:
            # 3. LLM 置信度评估
            llm_result = await self._llm_evaluate(keyword_result, message)
            return llm_result

        # 默认进入 default_agent
        return IntentResult(
            agent_name="default_agent",
            confidence=0.0,
            reason="No matching agent found, using default",
            match_type="default"
        )

    def _match_command(self, message: str) -> Optional[IntentResult]:
        """快捷命令匹配

        匹配 @command 格式的命令
        """
        match = re.match(r"^@(\w+)\s*", message)
        if not match:
            return None

        command = match.group(1)

        for agent in self._agents.values():
            if agent.command and agent.command.strip("@") == command:
                self._logger.info(f"Command match: {command} -> {agent.name}")
                return IntentResult(
                    agent_name=agent.name,
                    confidence=1.0,  # 命令匹配 100% 准确
                    reason=f"Matched command: {agent.command}",
                    match_type="command"
                )

        return None

    def _match_keywords(self, message: str) -> Optional[IntentResult]:
        """关键词匹配

        匹配至少 1 个关键词
        """
        message_lower = message.lower()
        best_match = None
        best_count = 0

        for agent in self._agents.values():
            match_count = sum(
                1 for kw in agent.keywords if kw.lower() in message_lower
            )
            if match_count > best_count:
                best_count = match_count
                best_match = agent

        if best_count > 0:
            confidence = min(0.8, 0.3 + best_count * 0.1)  # 1 个词 0.4, 2 个 0.5, 最多 0.8
            self._logger.info(
                f"Keyword match: {best_match.name} with {best_count} keywords"
            )
            return IntentResult(
                agent_name=best_match.name,
                confidence=confidence,
                reason=f"Matched {best_count} keywords: {best_match.keywords}",
                match_type="keyword"
            )

        return None

    async def _llm_evaluate(
        self, intent_result: IntentResult, message: str
    ) -> IntentResult:
        """LLM 置信度评估

        使用 LLM 评估关键词匹配的结果是否准确
        """
        agent = self._agents.get(intent_result.agent_name)
        if not agent:
            return intent_result

        prompt = f"""
You are an intent classifier. Evaluate whether the user's message should be handled by the specified agent.

User message: "{message}"

Agent info:
- Name: {agent.name}
- Description: {agent.description}
- Keywords: {agent.keywords}

Current match reason: {intent_result.reason}

Evaluate if this is the correct agent for this message. Consider:
1. Does the message semantically match the agent's purpose?
2. Are the matched keywords actually relevant to the message's intent?

Respond with a confidence score (0.0-1.0) and brief reason.
"""

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            # 简单解析，假设 LLM 返回一个 0-1 的数字
            content = response.content.strip()
            # 尝试提取置信度
            confidence = intent_result.confidence  # 默认保持原置信度

            # 如果 LLM 明确表达了低置信度，调整
            if any(word in content.lower() for word in ["not relevant", "wrong", "incorrect"]):
                confidence = 0.3
            elif any(word in content.lower() for word in ["correct", "appropriate", "suitable"]):
                confidence = max(confidence, 0.7)

            self._logger.debug(f"LLM evaluation confidence: {confidence}")

            return IntentResult(
                agent_name=intent_result.agent_name,
                confidence=confidence,
                reason=f"{intent_result.reason}. LLM: {content[:100]}",
                match_type="llm"
            )
        except Exception as e:
            self._logger.error(f"LLM evaluation failed: {e}")
            return intent_result

    def get_all_agents(self) -> List[AgentMetadata]:
        """获取所有注册的 Agent"""
        return list(self._agents.values())


# 全局意图识别器实例
intent_recognizer = IntentRecognizer()
```

- [ ] **Step 2: 更新 core __init__.py**

```python
# src/core/__init__.py
from .session_store import BaseSessionStore, Session, Turn
from .memory_session_store import MemorySessionStore, memory_session_store
from .session_manager import SessionManager, session_manager
from .intent import (
    IntentRecognizer,
    IntentResult,
    AgentMetadata,
    intent_recognizer,
)

__all__ = [
    "BaseSessionStore",
    "Session",
    "Turn",
    "MemorySessionStore",
    "memory_session_store",
    "SessionManager",
    "session_manager",
    "IntentRecognizer",
    "IntentResult",
    "AgentMetadata",
    "intent_recognizer",
]
```

- [ ] **Step 3: 编写单元测试**

Create: `tests/core/test_intent.py`

```python
# tests/core/test_intent.py
"""意图识别测试"""

import pytest
import asyncio

from src.core.intent import (
    IntentRecognizer,
    AgentMetadata,
    IntentResult,
)


@pytest.fixture
def recognizer():
    r = IntentRecognizer()
    # 注册测试 Agent
    r.register_agent(
        AgentMetadata(
            name="code_agent",
            description="处理代码相关请求",
            keywords=["代码", "编程", "function", "class"],
            command="@code",
        )
    )
    r.register_agent(
        AgentMetadata(
            name="plan_agent",
            description="帮助用户制定和管理计划",
            keywords=["计划", "任务", "todo", "schedule"],
            command="@plan",
        )
    )
    r.register_agent(
        AgentMetadata(
            name="default_agent",
            description="通用聊天助手",
            keywords=["你好", "hello"],
            command=None,
        )
    )
    return r


@pytest.mark.asyncio
async def test_command_match(recognizer):
    """测试快捷命令匹配"""
    result = await recognizer.recognize("@code 帮我写个函数")
    assert result.agent_name == "code_agent"
    assert result.confidence == 1.0
    assert result.match_type == "command"


@pytest.mark.asyncio
async def test_plan_command(recognizer):
    """测试计划命令"""
    result = await recognizer.recognize("@plan 明天开会")
    assert result.agent_name == "plan_agent"
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_keyword_match(recognizer):
    """测试关键词匹配"""
    result = await recognizer.recognize("帮我写一个 python 函数")
    assert result.agent_name == "code_agent"
    assert result.match_type in ["keyword", "llm"]


@pytest.mark.asyncio
async def test_default_agent(recognizer):
    """测试默认 Agent"""
    result = await recognizer.recognize("今天天气怎么样")
    assert result.agent_name == "default_agent"
```

- [ ] **Step 4: 运行测试**

Run: `cd D:\workplace\qrc\new3 && pytest tests/core/test_intent.py -v`
Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/core/intent.py tests/core/test_intent.py
git commit -m "feat: add intent recognizer"
```

---

## Chunk 3: 编排层 (Orchestration)

本 Chunk 实现 Agent 编排层，包括执行器基类、Agent 注册器、主工作流。

### Task 3.1: 执行器基类 (`orchestration/base_executor.py`)

**Files:**
- Create: `src/orchestration/__init__.py`
- Create: `src/orchestration/base_executor.py`

- [ ] **Step 1: 创建执行器基类**

```python
# src/orchestration/base_executor.py
"""执行器基类"""

from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import BaseMessage

from src.core.session_store import Session


class BaseExecutor(ABC):
    """执行器基类

    所有 Agent 必须继承该类并实现 run 方法
    """

    def __init__(self, session: Session, user_message: str):
        """初始化执行器

        Args:
            session: 当前会话
            user_message: 用户输入消息
        """
        self.session = session
        self.user_message = user_message

    @property
    def agent_name(self) -> str:
        """获取 Agent 名称（子类名）"""
        return self.__class__.__name__

    @abstractmethod
    async def run(self) -> List[BaseMessage]:
        """执行 Agent 逻辑

        Returns:
            消息列表（LangChain 格式）
        """
        pass
```

- [ ] **Step 2: 更新 orchestration __init__.py**

```python
# src/orchestration/__init__.py
from .base_executor import BaseExecutor

__all__ = ["BaseExecutor"]
```

- [ ] **Step 3: 提交**

```bash
git add src/orchestration/
git commit -m "feat: add base executor class"
```

---

### Task 3.2: Agent 注册器 (`orchestration/registry.py`)

**Files:**
- Modify: `src/orchestration/__init__.py`
- Create: `src/orchestration/registry.py`

- [ ] **Step 1: 创建 Agent 注册器**

```python
# src/orchestration/registry.py
"""Agent 注册器"""

from typing import Callable, Dict, List, Optional, Type

from src.core.intent import AgentMetadata
from src.core import intent
from src.orchestration.base_executor import BaseExecutor
from src.infra import logger


class AgentRegistry:
    """Agent 注册器

    使用装饰器注册 Agent，管理元数据和执行器类
    """

    def __init__(self):
        self._executors: Dict[str, Type[BaseExecutor]] = {}
        self._logger = logger.getLogger("AgentRegistry")

    def register(
        self,
        name: str,
        description: str,
        keywords: List[str],
        command: Optional[str] = None,
    ) -> Callable[[Type[BaseExecutor]], Type[BaseExecutor]]:
        """注册 Agent 装饰器

        Args:
            name: Agent 名称
            description: Agent 描述
            keywords: 关键词列表
            command: 快捷命令（如 @code）

        Returns:
            装饰器函数

        Example:
            @agent_registry.register(
                name="code_agent",
                description="处理代码相关请求",
                keywords=["代码", "编程", "function"],
                command="@code"
            )
            class CodeAgent(BaseExecutor):
                async def run(self):
                    ...
        """
        def decorator(cls: Type[BaseExecutor]) -> Type[BaseExecutor]:
            # 注册执行器类
            self._executors[name] = cls

            # 注册到意图识别器
            metadata = AgentMetadata(
                name=name,
                description=description,
                keywords=keywords,
                command=command
            )
            intent.intent_recognizer.register_agent(metadata)

            self._logger.info(f"Registered agent: {name}")
            return cls

        return decorator

    def get_executor(self, agent_name: str) -> Type[BaseExecutor]:
        """获取 Agent 执行器类"""
        if agent_name not in self._executors:
            raise ValueError(f"Agent not found: {agent_name}")
        return self._executors[agent_name]

    def get_all_executors(self) -> Dict[str, Type[BaseExecutor]]:
        """获取所有执行器类"""
        return self._executors.copy()


# 全局 Agent 注册器实例
agent_registry = AgentRegistry()
```

- [ ] **Step 2: 更新 orchestration __init__.py**

```python
# src/orchestration/__init__.py
from .base_executor import BaseExecutor
from .registry import agent_registry, AgentRegistry

__all__ = ["BaseExecutor", "agent_registry", "AgentRegistry"]
```

- [ ] **Step 3: 提交**

```bash
git add src/orchestration/registry.py src/orchestration/__init__.py
git commit -m "feat: add agent registry"
```

---

### Task 3.3: 主工作流 (`orchestration/master_workflow.py`)

**Files:**
- Modify: `src/orchestration/__init__.py`
- Create: `src/orchestration/master_workflow.py`

- [ ] **Step 1: 创建主工作流**

```python
# src/orchestration/master_workflow.py
"""主工作流：预处理 → 意图识别 → 执行器 → 后处理"""

from typing import NamedTuple

from langchain_core.messages import BaseMessage, AIMessage

from src.core.session_manager import SessionManager, session_manager
from src.core.intent import IntentRecognizer, intent_recognizer, IntentResult
from src.core.session_store import Session
from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra import logger
from src.config import Config


class WorkflowResult(NamedTuple):
    """工作流执行结果"""
    agent_name: str
    final_reply: str
    messages: list[BaseMessage]


class MasterWorkflow:
    """主工作流

    流程：
    1. 预处理：输入验证
    2. 意图识别：三层识别策略
    3. 执行器：执行对应 Agent
    4. 后处理：保存会话，格式化输出
    """

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        intent_recognizer: IntentRecognizer | None = None,
    ):
        self._session_manager = session_manager or session_manager
        self._intent_recognizer = intent_recognizer or intent_recognizer
        self._config = Config.get()
        self._logger = logger.getLogger("MasterWorkflow")

    async def execute(
        self, user_id: str, channel_id: str, message: str
    ) -> WorkflowResult:
        """执行工作流

        Args:
            user_id: 用户 ID
            channel_id: 渠道 ID
            message: 用户输入消息

        Returns:
            工作流执行结果
        """
        # 1. 预处理
        self._preprocess(message)

        # 2. 意图识别
        intent_result = await self._recognize_intent(message)

        # 3. 执行器
        messages = await self._execute_agent(
            user_id, channel_id, message, intent_result
        )

        # 4. 后处理
        final_reply = self._postprocess(messages)

        return WorkflowResult(
            agent_name=intent_result.agent_name,
            final_reply=final_reply,
            messages=messages
        )

    def _preprocess(self, message: str) -> None:
        """预处理：输入验证"""
        if not message or not message.strip():
            raise ValueError("Empty message")
        self._logger.debug(f"Preprocess: message length={len(message)}")

    async def _recognize_intent(self, message: str) -> IntentResult:
        """意图识别"""
        self._logger.info(f"Recognizing intent for: {message[:50]}...")
        result = await self._intent_recognizer.recognize(message)
        self._logger.info(
            f"Intent recognized: {result.agent_name} "
            f"(confidence={result.confidence}, type={result.match_type})"
        )
        return result

    async def _execute_agent(
        self,
        user_id: str,
        channel_id: str,
        message: str,
        intent_result: IntentResult,
    ) -> list[BaseMessage]:
        """执行 Agent"""
        # 获取会话
        session = await self._session_manager.get_or_create_session(
            user_id, channel_id
        )

        # 获取执行器类并实例化
        executor_class = agent_registry.get_executor(intent_result.agent_name)
        executor: BaseExecutor = executor_class(session=session, user_message=message)

        # 执行
        self._logger.info(f"Executing agent: {intent_result.agent_name}")
        messages = await executor.run()

        # 保存会话
        final_reply = messages[-1].content if messages else ""
        await self._session_manager.add_turn(
            session=session,
            agent_name=intent_result.agent_name,
            user_message=message,
            messages=messages,
            final_reply=final_reply
        )

        return messages

    def _postprocess(self, messages: list[BaseMessage]) -> str:
        """后处理：获取最终回复"""
        if not messages:
            return ""

        # 取最后一条 AI 消息
        final_message = messages[-1]
        if isinstance(final_message, AIMessage):
            return final_message.content
        return str(final_message.content)


# 全局工作流实例
master_workflow = MasterWorkflow()
```

- [ ] **Step 2: 更新 orchestration __init__.py**

```python
# src/orchestration/__init__.py
from .base_executor import BaseExecutor
from .registry import agent_registry, AgentRegistry
from .master_workflow import MasterWorkflow, master_workflow, WorkflowResult

__all__ = [
    "BaseExecutor",
    "agent_registry",
    "AgentRegistry",
    "MasterWorkflow",
    "master_workflow",
    "WorkflowResult",
]
```

- [ ] **Step 3: 提交**

```bash
git add src/orchestration/master_workflow.py src/orchestration/__init__.py
git commit -m "feat: add master workflow"
```

---

## Chunk 4: Agents 层

本 Chunk 实现具体的 Agent：default_agent、code_agent、plan_agent。

### Task 4.1: Agent 提示词管理 (`agents/prompts.py`)

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/prompts.py`

- [ ] **Step 1: 创建提示词管理**

```python
# src/agents/prompts.py
"""Agent 系统提示词管理"""


class Prompts:
    """系统提示词集合"""

    DEFAULT_AGENT = """You are a friendly and helpful assistant. Engage in natural conversation with the user.

Guidelines:
- Be warm and conversational
- Provide helpful and accurate information
- If you don't know something, admit it honestly
- Keep responses concise but informative
- Ask follow-up questions when appropriate to better understand user needs
"""

    CODE_AGENT = """You are an expert coding assistant. Help users with programming tasks.

Capabilities:
- Write clean, well-documented code
- Explain code concepts clearly
- Debug and fix code issues
- Suggest best practices and improvements
- Support multiple programming languages

Guidelines:
- Always write production-ready code
- Include comments for complex logic
- Explain your code choices
- Ask for clarification if requirements are unclear
"""

    PLAN_AGENT = """You are a productivity assistant specializing in planning and task management.

Capabilities:
- Help users create and manage tasks
- Assist with scheduling and time management
- Break down complex projects into actionable steps
- Provide productivity tips and techniques

Guidelines:
- Be practical and realistic in suggestions
- Help prioritize tasks effectively
- Consider user's constraints and deadlines
- Encourage good work-life balance
"""

    @classmethod
    def get(cls, agent_name: str) -> str:
        """获取指定 Agent 的系统提示词"""
        mapping = {
            "default_agent": cls.DEFAULT_AGENT,
            "code_agent": cls.CODE_AGENT,
            "plan_agent": cls.PLAN_AGENT,
        }
        return mapping.get(agent_name, cls.DEFAULT_AGENT)
```

- [ ] **Step 2: 更新 agents __init__.py**

```python
# src/agents/__init__.py
from .prompts import Prompts

__all__ = ["Prompts"]
```

- [ ] **Step 3: 提交**

```bash
git add src/agents/
git commit -m "feat: add agent prompts"
```

---

### Task 4.2: Default Agent (`agents/default_agent.py`)

**Files:**
- Modify: `src/agents/__init__.py`
- Create: `src/agents/default_agent.py`

- [ ] **Step 1: 创建 Default Agent**

```python
# src/agents/default_agent.py
"""Default Agent - 通用聊天助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="default_agent",
    description="通用聊天助手，处理意图不清晰的请求",
    keywords=["你好", "hello", "hi", "早上好", "下午好", "晚上好"],
    command=None
)
class DefaultAgent(BaseExecutor):
    """Default Agent - 通用聊天助手"""

    async def run(self) -> List[BaseMessage]:
        """执行通用聊天逻辑"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("default_agent")),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
```

- [ ] **Step 2: 更新 agents __init__.py**

```python
# src/agents/__init__.py
from .prompts import Prompts
from . import default_agent  # noqa: F401 - 注册 Agent
from . import code_agent  # noqa: F401
from . import plan_agent  # noqa: F401

__all__ = ["Prompts"]
```

- [ ] **Step 3: 提交**

```bash
git add src/agents/default_agent.py src/agents/__init__.py
git commit -m "feat: add default agent"
```

---

### Task 4.3: Code Agent (`agents/code_agent.py`)

**Files:**
- Create: `src/agents/code_agent.py`

- [ ] **Step 1: 创建 Code Agent**

```python
# src/agents/code_agent.py
"""Code Agent - 代码助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求，包括编写、解释、调试代码",
    keywords=[
        "代码", "编程", "function", "class", "def", "import",
        "write code", "code", "function", "class", "bug", "debug"
    ],
    command="@code"
)
class CodeAgent(BaseExecutor):
    """Code Agent - 代码助手"""

    async def run(self) -> List[BaseMessage]:
        """执行代码相关任务"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
```

- [ ] **Step 2: 提交**

```bash
git add src/agents/code_agent.py
git commit -m "feat: add code agent"
```

---

### Task 4.4: Plan Agent (`agents/plan_agent.py`)

**Files:**
- Create: `src/agents/plan_agent.py`

- [ ] **Step 1: 创建 Plan Agent**

```python
# src/agents/plan_agent.py
"""Plan Agent - 计划管理助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="plan_agent",
    description="帮助用户制定和管理计划、任务",
    keywords=[
        "计划", "任务", "todo", "schedule", "plan", "task",
        "安排", "日程", "待办"
    ],
    command="@plan"
)
class PlanAgent(BaseExecutor):
    """Plan Agent - 计划管理助手"""

    async def run(self) -> List[BaseMessage]:
        """执行计划管理相关任务"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("plan_agent")),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
```

- [ ] **Step 2: 提交**

```bash
git add src/agents/plan_agent.py
git commit -m "feat: add plan agent"
```

---

## Chunk 5: Controller 层和入口

本 Chunk 实现 Controller 层和应用入口。

### Task 5.1: Bot Controller (`controller/bot_controller.py`)

**Files:**
- Create: `src/controller/__init__.py`
- Create: `src/controller/bot_controller.py`

- [ ] **Step 1: 创建 Bot Controller**

```python
# src/controller/bot_controller.py
"""Bot Controller - 机器人入口"""

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from src.orchestration.master_workflow import master_workflow
from src.infra import logger


class ChatRequest(BaseModel):
    """聊天请求"""
    user_id: str
    channel_id: str
    message: str


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    reply: str
    agent_name: str


router = APIRouter()
_logger = logger.getLogger("BotController")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """处理聊天请求

    Args:
        request: 聊天请求

    Returns:
        聊天响应

    Raises:
        HTTPException: 当请求无效时
    """
    try:
        _logger.info(
            f"Chat request from user={request.user_id}, "
            f"channel={request.channel_id}"
        )

        # 执行工作流
        result = await master_workflow.execute(
            user_id=request.user_id,
            channel_id=request.channel_id,
            message=request.message
        )

        _logger.info(
            f"Chat response: agent={result.agent_name}, "
            f"reply={result.final_reply[:50]}..."
        )

        return ChatResponse(
            session_id=f"{request.user_id}_{request.channel_id}",
            reply=result.final_reply,
            agent_name=result.agent_name
        )

    except ValueError as e:
        _logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

- [ ] **Step 2: 更新 controller __init__.py**

```python
# src/controller/__init__.py
from .bot_controller import router

__all__ = ["router"]
```

- [ ] **Step 3: 提交**

```bash
git add src/controller/
git commit -m "feat: add bot controller"
```

---

### Task 5.2: 应用入口 (`main.py`)

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 创建 FastAPI 应用入口**

```python
# main.py
"""Agent 系统应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.controller.bot_controller import router
from src.infra import logger
from src.core.session_manager import session_manager


_logger = logger.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info("Starting Agent System...")
    yield
    _logger.info("Shutting down Agent System...")
    # 清理过期会话
    await session_manager.cleanup_expired()


app = FastAPI(
    title="Agent System",
    description="Multi-Agent routing system based on intent recognition",
    version="0.1.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 2: 验证应用可启动**

Run: `cd D:\workplace\qrc\new3 && python -c "from main import app; print('App loaded successfully')"`
Expected: 输出 "App loaded successfully"

- [ ] **Step 3: 提交**

```bash
git add main.py
git commit -m "feat: add FastAPI application entry point"
```

---

### Task 5.3: 依赖管理 (`requirements.txt`)

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 创建依赖文件**

```
# requirements.txt
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0

# LangChain
langchain>=0.1.0
langchain-openai>=0.0.5
langgraph>=0.0.20

# Database (预留)
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.23.0

# Utilities
python-dotenv>=1.0.0
```

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "feat: add requirements.txt"
```

---

## Chunk 6: 测试和文档

### Task 6.1: 集成测试

**Files:**
- Create: `tests/integration/test_workflow.py`

- [ ] **Step 1: 创建工作流集成测试**

```python
# tests/integration/test_workflow.py
"""工作流集成测试"""

import pytest

from src.orchestration.master_workflow import master_workflow


@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="你好"
    )

    assert result.agent_name == "default_agent"
    assert result.final_reply != ""


@pytest.mark.asyncio
async def test_code_agent_workflow():
    """测试 Code Agent 工作流"""
    result = await master_workflow.execute(
        user_id="test_user",
        channel_id="test_channel",
        message="@code 帮我写一个 hello world 函数"
    )

    assert result.agent_name == "code_agent"
    assert result.final_reply != ""
```

- [ ] **Step 2: 运行集成测试**

Run: `cd D:\workplace\qrc\new3 && pytest tests/integration/ -v`
Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/integration/
git commit -m "test: add integration tests"
```

---

## 总结

本计划共 6 个 Chunk，18 个 Task，涵盖：

1. **Chunk 1**: 基础设施层（配置、LLM、日志、数据库预留）
2. **Chunk 2**: 核心层（会话存储、会话管理器、意图识别）
3. **Chunk 3**: 编排层（执行器基类、注册器、主工作流）
4. **Chunk 4**: Agents 层（default、code、plan 三个 Agent）
5. **Chunk 5**: Controller 层和入口（Bot Controller、FastAPI 应用）
6. **Chunk 6**: 测试和文档

每个 Task 都是独立的、可测试的单元，遵循 TDD 原则：先写测试，再实现功能。
