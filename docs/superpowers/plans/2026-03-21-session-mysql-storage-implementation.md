# MySQL 会话存储实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将会话管理后端从内存存储改造为 MySQL 持久化存储，同时保留内存实现以支持平滑切换。

**Architecture:** 通过依赖注入模式，`SessionManager` 可注入 `MemorySessionStore` 或 `MySQLSessionStore`。配置项 `USE_MYSQL` 控制使用哪种存储。

**Tech Stack:** Python 3.10+, SQLAlchemy 2.0 (async), aiomysql, FastAPI, Pytest

---

## Chunk 1: 基础架构改造

本 Chunk 完成模块结构调整和配置扩展，为 MySQL 实现奠定基础。

### Task 1: 创建 store 目录结构

**Files:**
- Create: `src/core/session/store/__init__.py`
- Create: `src/core/session/store/base.py`
- Create: `src/core/session/store/memory.py`
- Modify: `src/core/session/store.py` → 删除（内容迁移到 store/ 子目录）
- Modify: `src/core/session/models.py` → 移除 BaseSessionStore 类

- [ ] **Step 1: 创建 store 目录**

```bash
mkdir -p src/core/session/store
```

- [ ] **Step 2: 创建 base.py (抽象基类)**

将 `src/core/session/models.py` 中的 `BaseSessionStore` 类移动到新文件：

```python
# src/core/session/store/base.py
"""会话存储抽象基类"""

from abc import ABC, abstractmethod
from src.core.session.models import Session


class BaseSessionStore(ABC):
    """会话存储抽象基类"""

    @abstractmethod
    async def get_session(self, session_id: str) -> Session:
        """获取会话，不存在则创建"""
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

- [ ] **Step 3: 创建 memory.py (内存实现)**

将 `src/core/session/store.py` 内容移动到新文件并修正导入：

```python
# src/core/session/store/memory.py
"""内存会话存储实现"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from src.core.session.models import Session
from src.core.session.store.base import BaseSessionStore


class MemorySessionStore(BaseSessionStore):
    """内存会话存储"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger("MemorySessionStore")

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
memory_store = MemorySessionStore()
```

- [ ] **Step 4: 创建 store/__init__.py**

```python
# src/core/session/store/__init__.py
"""会话存储模块"""

from src.core.session.store.base import BaseSessionStore
from src.core.session.store.memory import MemorySessionStore, memory_store

__all__ = [
    "BaseSessionStore",
    "MemorySessionStore",
    "memory_store",
]
```

- [ ] **Step 5: 删除原 store.py 文件**

```bash
rm src/core/session/store.py
```

- [ ] **Step 6: 更新 models.py 移除 BaseSessionStore**

修改 `src/core/session/models.py`，移除 `BaseSessionStore` 类（已移动到 `store/base.py`）：

```python
# src/core/session/models.py
# 移除: from abc import ABC, abstractmethod
# 移除: class BaseSessionStore(ABC): ...

# 保留 Turn 和 Session 数据类
```

- [ ] **Step 7: 运行测试验证重构**

```bash
pytest tests/ -v
```

Expected: 所有测试通过

- [ ] **Step 8: 提交**

```bash
git add -A
git commit -m "refactor(session): 将存储实现移动到 store 子目录
- 创建 src/core/session/store/ 目录
- 移动 BaseSessionStore 到 store/base.py
- 移动 MemorySessionStore 到 store/memory.py
- 保留原有功能不变"
```

---

### Task 2: 扩展配置支持 MySQL

**Files:**
- Modify: `src/config/config.py:1-34`

- [ ] **Step 1: 编写测试**

```python
# tests/unit/config/test_mysql_config.py
from src.config import Config

def test_mysql_database_url():
    """测试 MySQL 数据库 URL 生成"""
    config = Config()
    config.USE_MYSQL = True
    config.MYSQL_HOST = "localhost"
    config.MYSQL_PORT = 3306
    config.MYSQL_USER = "root"
    config.MYSQL_PASSWORD = "123456"
    config.MYSQL_DATABASE = "qrc_session"

    url = config.get_database_url()
    assert url == "mysql+asyncmy://root:123456@localhost:3306/qrc_session"

def test_sqlite_database_url():
    """测试 SQLite 数据库 URL 生成"""
    config = Config()
    config.USE_MYSQL = False

    url = config.get_database_url()
    assert url == "sqlite+aiosqlite:///:memory:"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/unit/config/test_mysql_config.py -v
```

Expected: FAIL with "AttributeError: 'Config' object has no attribute 'get_database_url'"

- [ ] **Step 3: 扩展 Config 类**

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
    CONTEXT_KEEP_TURNS: int = 3

    # 上下文压缩配置
    CONTEXT_MAX_TOKENS: int = 8000
    CONTEXT_SUMMARY_THRESHOLD: float = 0.8
    CONTEXT_KEEP_RECENT_MESSAGES: int = 10
    SUMMARY_MODEL: str = "qwen3.5-plus"

    # ========== 新增：MySQL 配置 ==========
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "qrc_session"
    USE_MYSQL: bool = False  # 默认使用内存存储，需要时开启

    @classmethod
    def get(cls) -> "Config":
        """获取全局配置实例"""
        return _global_config

    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.USE_MYSQL:
            return (
                f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            )
        else:
            return "sqlite+aiosqlite:///:memory:"


_global_config = Config()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/unit/config/test_mysql_config.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat(config): 添加 MySQL 配置项和 get_database_url 方法

- 新增 MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
- 新增 USE_MYSQL 开关（默认 False）
- 新增 get_database_url() 方法根据配置生成连接 URL"
```

---

### Task 3: 扩展 DatabaseManager 支持自动建表

**Files:**
- Modify: `src/infra/database.py:1-40`

- [ ] **Step 1: 编写测试**

```python
# tests/unit/infra/test_database_manager.py
import pytest
from src.infra.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_manager_init_creates_engine():
    """测试数据库管理器初始化"""
    db = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await db.init()

    assert db.engine is not None
    assert db.async_session_maker is not None

    await db.close()


@pytest.mark.asyncio
async def test_database_manager_mysql_url():
    """测试 MySQL URL 配置"""
    db = DatabaseManager("mysql+asyncmy://root:123456@localhost:3306/test_db")
    assert "mysql+asyncmy" in db.database_url
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/unit/infra/test_database_manager.py -v
```

- [ ] **Step 3: 扩展 DatabaseManager**

```python
# src/infra/database.py
"""数据库连接模块"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 全局 Base 类，用于 ORM 模型定义
Base = declarative_base()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str | None = None):
        """初始化数据库管理器

        Args:
            database_url: 数据库连接 URL，为 None 时使用默认配置
        """
        from src.config import Config
        self.database_url = database_url or Config.get().get_database_url()
        self.engine = None
        self.async_session_maker = None

    async def init(self, create_tables: bool = False) -> None:
        """初始化数据库连接

        Args:
            create_tables: 是否自动创建表结构 (仅 MySQL 时需要)
        """
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        if create_tables and "mysql" in self.database_url:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

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

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/unit/infra/test_database_manager.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat(infra): DatabaseManager 支持自动建表

- 从 Config 读取默认数据库 URL
- init() 新增 create_tables 参数，自动创建 ORM 表结构
- 导出 Base 类供 ORM 模型使用"
```

---

## Chunk 2: MySQL 存储实现

本 Chunk 完成核心 MySQL 存储实现。

### Task 4: 创建 SQLAlchemy ORM 模型

**Files:**
- Create: `src/core/session/db_models.py`

- [ ] **Step 1: 编写测试**

```python
# tests/unit/session/test_orm_models.py
from src.core.session.db_models import SessionModel, TurnModel
from sqlalchemy import inspect


def test_session_model_columns():
    """测试 SessionModel 字段"""
    columns = [c.name for c in inspect(SessionModel).columns]
    expected = [
        "id", "session_id", "user_id", "channel_id",
        "created_at", "updated_at", "expires_at", "summary"
    ]
    for col in expected:
        assert col in columns


def test_turn_model_columns():
    """测试 TurnModel 字段"""
    columns = [c.name for c in inspect(TurnModel).columns]
    expected = [
        "id", "turn_id", "session_id", "agent_name",
        "messages", "final_reply", "created_at", "is_compressed"
    ]
    for col in expected:
        assert col in columns


def test_turn_foreign_key():
    """测试 TurnModel 外键约束"""
    fk = TurnModel.__table__.foreign_keys
    assert len(fk) == 1
    fk_col = list(fk)[0]
    assert fk_col.column.name == "session_id"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/unit/session/test_orm_models.py -v
```

Expected: FAIL (模块不存在)

- [ ] **Step 3: 创建 ORM 模型**

```python
# src/core/session/db_models.py
"""SQLAlchemy ORM 模型 - 会话存储"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    BigInteger,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.mysql import JSON

# 从 infra.database 导入 Base，避免重复定义
from src.infra.database import Base


class SessionModel(Base):
    """会话 ORM 模型"""

    __tablename__ = "sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, nullable=False, index=True)
    summary = Column(Text, nullable=True)

    # 一对多关系
    turns = relationship(
        "TurnModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"  # 预加载 turns
    )

    __table_args__ = (
        Index("idx_user_channel", "user_id", "channel_id"),
    )


class TurnModel(Base):
    """对话轮次 ORM 模型"""

    __tablename__ = "turns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    turn_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(
        String(255),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_name = Column(String(100), nullable=False)
    messages = Column(JSON, nullable=False)  # LangChain 消息列表的 JSON 序列化
    final_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    is_compressed = Column(Boolean, default=False)

    # 反向关系
    session = relationship("SessionModel", back_populates="turns")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/unit/session/test_orm_models.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat(session): 创建 SQLAlchemy ORM 模型

- SessionModel: sessions 表，包含索引和外键定义
- TurnModel: turns 表，JSON 字段存储 messages，级联删除
- 使用 mysql+asyncmy 驱动"
```

---

### Task 5: 实现 MySQLSessionStore

**Files:**
- Create: `src/core/session/store/mysql.py`
- Modify: `src/core/session/store/__init__.py`

- [ ] **Step 1: 编写测试（使用 mock）**

```python
# tests/unit/session/test_mysql_store.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.core.session.store.mysql import MySQLSessionStore
from src.core.session.models import Session


@pytest.fixture
def mock_session_maker():
    """模拟 session_maker"""
    maker = AsyncMock()
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    maker.return_value = session
    return maker


@pytest.mark.asyncio
async def test_mysql_get_session_creates_new(mock_session_maker):
    """测试获取不存在的会话时创建新会话"""
    store = MySQLSessionStore(mock_session_maker)

    # Mock 查询结果为空
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_session_maker.return_value.__aenter__.return_value.execute.return_value = result_mock

    session = await store.get_session("test_user_test_channel")

    assert session.session_id == "test_user_test_channel"
    assert session.user_id == "test_user"
    assert session.channel_id == "test_channel"


@pytest.mark.asyncio
async def test_mysql_save_session(mock_session_maker):
    """测试保存会话"""
    store = MySQLSessionStore(mock_session_maker)
    session = Session(
        session_id="test_session",
        user_id="test_user",
        channel_id="test_channel",
    )

    # Mock commit
    mock_session_maker.return_value.__aenter__.return_value.commit = AsyncMock()

    await store.save_session(session)

    mock_session_maker.return_value.__aenter__.return_value.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_cleanup_expired(mock_session_maker):
    """测试清理过期会话"""
    store = MySQLSessionStore(mock_session_maker)
    mock_session_maker.return_value.__aenter__.return_value.commit = AsyncMock()

    await store.cleanup_expired()

    mock_session_maker.return_value.__aenter__.return_value.commit.assert_called_once()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/unit/session/test_mysql_store.py -v
```

Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现 MySQLSessionStore**

```python
# src/core/session/store/mysql.py
"""MySQL 会话存储实现"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.session.models import Session, Turn
from src.core.session.store.base import BaseSessionStore
from src.core.session.db_models import SessionModel, TurnModel


class MySQLSessionStore(BaseSessionStore):
    """MySQL 会话存储"""

    def __init__(self, session_maker: async_sessionmaker):
        self._session_maker = session_maker
        self._logger = logging.getLogger("MySQLSessionStore")

    async def get_session(self, session_id: str) -> Session:
        """获取会话，不存在则创建"""
        async with self._session_maker() as session:
            # 查询 SessionModel
            result = await session.execute(
                select(SessionModel).where(SessionModel.session_id == session_id)
            )
            session_model = result.scalar_one_or_none()

            if session_model is None:
                # 解析 session_id 获取 user_id 和 channel_id
                parts = session_id.split("_", 1)
                user_id = parts[0] if len(parts) > 0 else ""
                channel_id = parts[1] if len(parts) > 1 else ""

                return self._create_new_session(session_id, user_id, channel_id)

            # 转换为领域模型
            return self._to_domain_session(session_model)

    async def save_session(self, session: Session) -> None:
        """保存会话"""
        async with self._session_maker() as db_session:
            # 先保存/更新 Session
            session_model = await self._upsert_session(db_session, session)

            # 同步 Turns（差量更新）
            await self._sync_turns(db_session, session_model, session)

            await db_session.commit()

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        async with self._session_maker() as session:
            now = datetime.now()
            await session.execute(
                delete(SessionModel).where(SessionModel.expires_at < now)
            )
            await session.commit()
            self._logger.info("Cleaned up expired sessions")

    def _create_new_session(
        self, session_id: str, user_id: str, channel_id: str
    ) -> Session:
        """创建新会话"""
        self._logger.debug(f"Created new session in DB: {session_id}")
        return Session(
            session_id=session_id,
            user_id=user_id,
            channel_id=channel_id,
        )

    def _to_domain_session(self, model: SessionModel) -> Session:
        """将 ORM 模型转换为领域模型"""
        session = Session(
            session_id=model.session_id,
            user_id=model.user_id,
            channel_id=model.channel_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
            summary=model.summary or "",
        )

        # 转换 Turns
        for turn_model in model.turns:
            turn = Turn(
                turn_id=turn_model.turn_id,
                agent_name=turn_model.agent_name,
                messages=self._deserialize_messages(turn_model.messages),
                final_reply=turn_model.final_reply or "",
                created_at=turn_model.created_at,
                is_compressed=turn_model.is_compressed,
            )
            session.turns.append(turn)

        return session

    async def _upsert_session(
        self, db_session, session: Session
    ) -> SessionModel:
        """保存或更新 Session"""
        # 尝试查询现有记录
        result = await db_session.execute(
            select(SessionModel).where(SessionModel.session_id == session.session_id)
        )
        session_model = result.scalar_one_or_none()

        if session_model is None:
            # 插入新记录
            session_model = SessionModel(
                session_id=session.session_id,
                user_id=session.user_id,
                channel_id=session.channel_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                expires_at=session.expires_at,
                summary=session.summary,
            )
            db_session.add(session_model)
            await db_session.flush()  # 获取 ID
        else:
            # 更新现有记录
            session_model.user_id = session.user_id
            session_model.channel_id = session.channel_id
            session_model.updated_at = session.updated_at
            session_model.expires_at = session.expires_at
            session_model.summary = session.summary

        return session_model

    async def _sync_turns(
        self, db_session, session_model: SessionModel, session: Session
    ) -> None:
        """同步 Turns 数据（差量更新）"""
        # 获取现有 turn_ids
        existing_turn_ids = {t.turn_id for t in session_model.turns}
        new_turn_ids = {t.turn_id for t in session.turns}

        # 删除不存在的 turns
        turns_to_delete = existing_turn_ids - new_turn_ids
        if turns_to_delete:
            await db_session.execute(
                delete(TurnModel).where(
                    TurnModel.turn_id.in_(turns_to_delete)
                )
            )

        # 更新或插入 turns
        for turn in session.turns:
            if turn.turn_id in existing_turn_ids:
                # 更新现有
                turn_model = next(
                    t for t in session_model.turns if t.turn_id == turn.turn_id
                )
                turn_model.agent_name = turn.agent_name
                turn_model.messages = self._serialize_messages(turn.messages)
                turn_model.final_reply = turn.final_reply
                turn_model.is_compressed = turn.is_compressed
            else:
                # 插入新 turn
                turn_model = TurnModel(
                    turn_id=turn.turn_id,
                    session_id=session_model.session_id,
                    agent_name=turn.agent_name,
                    messages=self._serialize_messages(turn.messages),
                    final_reply=turn.final_reply,
                    is_compressed=turn.is_compressed,
                )
                db_session.add(turn_model)

    def _serialize_messages(self, messages: list) -> str:
        """序列化消息列表为 JSON"""
        from langchain_core.messages import BaseMessage

        serialized = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                serialized.append(msg.model_dump())
            else:
                serialized.append(msg)
        return json.dumps(serialized, ensure_ascii=False, default=str)

    def _deserialize_messages(self, data: str) -> list:
        """从 JSON 反序列化消息列表"""
        if not data:
            return []

        try:
            messages_data = json.loads(data)
            # 返回原始数据，由 Session.get_context_messages 处理
            return messages_data
        except json.JSONDecodeError:
            self._logger.error(f"Failed to deserialize messages: {data}")
            return []
```

- [ ] **Step 4: 更新 store/__init__.py 导出 MySQLSessionStore**

```python
# src/core/session/store/__init__.py
"""会话存储模块"""

from src.core.session.store.base import BaseSessionStore
from src.core.session.store.memory import MemorySessionStore, memory_store

# 条件导入，避免 MySQL 未安装时报错
try:
    from src.core.session.store.mysql import MySQLSessionStore
    __all__ = [
        "BaseSessionStore",
        "MemorySessionStore",
        "memory_store",
        "MySQLSessionStore",
    ]
except ImportError:
    __all__ = [
        "BaseSessionStore",
        "MemorySessionStore",
        "memory_store",
    ]
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/unit/session/test_mysql_store.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat(session): 实现 MySQLSessionStore

- get_session: 查询或创建会话
- save_session: 差量同步 Session 和 Turns
- cleanup_expired: 删除过期会话
- 支持 LangChain 消息的 JSON 序列化/反序列化"
```

---

### Task 6: 修改 SessionManager 支持依赖注入

**Files:**
- Modify: `src/core/session/manager.py:1-50`

- [ ] **Step 1: 编写测试**

```python
# tests/unit/session/test_session_manager_injection.py
import pytest
from unittest.mock import AsyncMock

from src.core.session.manager import SessionManager
from src.core.session.store.memory import MemorySessionStore


@pytest.mark.asyncio
async def test_session_manager_with_explicit_store():
    """测试显式注入 store"""
    store = MemorySessionStore()
    manager = SessionManager(store=store)

    session = await manager.get_or_create_session("user1", "channel1")
    assert session.session_id == "user1_channel1"


@pytest.mark.asyncio
async def test_session_manager_with_default():
    """测试默认配置（不传入 store）"""
    # 通过 patch Config 来测试默认行为
    manager = SessionManager()

    session = await manager.get_or_create_session("user2", "channel2")
    assert session.session_id == "user2_channel2"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/unit/session/test_session_manager_injection.py -v
```

- [ ] **Step 3: 修改 SessionManager**

```python
# src/core/session/manager.py
"""会话管理器"""

from typing import List, TYPE_CHECKING

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from src.core.session.models import Session, Turn
from src.core.session.store.base import BaseSessionStore
from src.config import Config
from src.infra.llm import create_llm

# 延迟导入以避免循环依赖
if TYPE_CHECKING:
    from src.core.session.store.memory import MemorySessionStore


class SessionManager:
    """会话管理器

    负责：
    - 会话的获取和保存
    - 轮次的添加和压缩
    - 上下文消息的提取
    - Token 计数和摘要生成
    """

    def __init__(self, store: BaseSessionStore | None = None):
        """初始化会话管理器

        Args:
            store: 会话存储实例，为 None 时根据配置自动选择
        """
        if store is None:
            # 根据配置选择 store
            config = Config.get()
            if config.USE_MYSQL:
                from src.core.session.store.mysql import MySQLSessionStore
                from src.infra.database import db_manager
                store = MySQLSessionStore(db_manager.get_session_maker())
            else:
                from src.core.session.store.memory import MemorySessionStore
                store = MemorySessionStore()

        self._store = store
        self._config = Config.get()
        self._summary_llm = None  # 懒加载摘要模型

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

    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的 token 数量"""
        return count_tokens_approximately(messages)

    def _get_summary_llm(self):
        """获取用于摘要的 LLM 实例（懒加载）"""
        if self._summary_llm is None:
            self._summary_llm = create_llm(
                model_name=self._config.SUMMARY_MODEL
            )
        return self._summary_llm

    async def _generate_summary(self, messages: List[BaseMessage]) -> str:
        """使用 LLM 生成消息摘要"""
        if not messages:
            return ""

        llm = self._get_summary_llm()
        from langchain_core.messages import HumanMessage, SystemMessage

        summary_prompt = SystemMessage(
            content="请用简洁的语言总结以下对话内容，保留关键信息（如文件名、函数名、执行结果等）。"
        )
        messages_to_summarize = [
            summary_prompt,
            HumanMessage(content=f"请总结以下对话：\n\n{messages}")
        ]

        try:
            result = await llm.ainvoke(messages_to_summarize)
            return result.content
        except Exception as e:
            return f"[摘要生成失败：{str(e)}]"

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        await self._store.cleanup_expired()


# 全局会话管理器实例
session_manager = SessionManager()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/unit/session/test_session_manager_injection.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat(session): SessionManager 支持依赖注入

- __init__ 可选注入 BaseSessionStore 实例
- 未注入时根据 Config.USE_MYSQL 自动选择实现
- 保持全局 session_manager 实例向后兼容"
```

---

## Chunk 3: 集成与启动

本 Chunk 完成应用集成和启动流程。

### Task 7: 修改 main.py lifespan 初始化数据库

**Files:**
- Modify: `src/main.py:1-35`

- [ ] **Step 1: 编写测试**

集成测试，需要真实的 MySQL 环境，暂时跳过，手动测试。

- [ ] **Step 2: 修改 lifespan 函数**

```python
# src/main.py
"""Agent 系统应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# 导入 features 模块以注册 Agent
from src.features.code import code_agent  # noqa: F401
from src.features.plan import plan_agent
from src.features.default import default_agent
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer
from src.controller.bot_controller import router
from src.core.session.manager import session_manager
from src.infra.database import db_manager
from src.config import Config

_logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info("Starting Agent System...")

    # 初始化数据库（如果使用 MySQL）
    config = Config.get()
    if config.USE_MYSQL:
        _logger.info(f"Connecting to MySQL at {config.MYSQL_HOST}:{config.MYSQL_PORT}")
        await db_manager.init(create_tables=True)
        _logger.info("Database initialized")
    else:
        _logger.info("Using in-memory session storage")

    # 显式注册所有 Agent 到意图识别器
    for name, metadata in agent_registry.get_all_metadata().items():
        intent_recognizer.register_agent(metadata)
        _logger.info(f"Registered agent with intent_recognizer: {name}")

    yield

    _logger.info("Shutting down Agent System...")
    # 清理过期会话
    await session_manager.cleanup_expired()
    # 关闭数据库连接
    if config.USE_MYSQL:
        await db_manager.close()


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
    import asyncio
    import os

    # 配置根日志级别，显示应用内部日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 始终使用调试兼容的启动方式
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    if debug_mode:
        # 显式调试模式：使用 Server.serve() 直接启动
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
        server = uvicorn.Server(config)
        print("Starting in explicit debug mode...")
        asyncio.run(server.serve())
    else:
        # 默认模式：使用 uvicorn.run()
        try:
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except TypeError as e:
            if "loop_factory" in str(e):
                print("Detected loop_factory compatibility issue, switching to debug mode...")
                config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
                server = uvicorn.Server(config)
                asyncio.run(server.serve())
            else:
                raise
```

- [ ] **Step 3: 验证导入**

```bash
python -c "from src.main import app; print('Import OK')"
```

Expected: No errors

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "feat(main): lifespan 初始化数据库连接

- 根据 Config.USE_MYSQL 决定是否连接 MySQL
- create_tables=True 自动创建表结构
- 关闭时清理过期会话并断开数据库连接"
```

---

### Task 8: 创建数据库初始化脚本

**Files:**
- Create: `scripts/init_db.sql`

- [ ] **Step 1: 创建 SQL 初始化脚本**

```sql
-- scripts/init_db.sql
-- MySQL 会话数据库初始化脚本
-- 使用方法：mysql -u root -p < scripts/init_db.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS qrc_session
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE qrc_session;

-- sessions 表
CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    channel_id VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    summary TEXT,
    INDEX idx_user_id (user_id),
    INDEX idx_channel_id (channel_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_channel (user_id, channel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- turns 表
CREATE TABLE IF NOT EXISTS turns (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    turn_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    messages JSON NOT NULL,
    final_reply TEXT,
    created_at DATETIME NOT NULL,
    is_compressed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_turn_id (turn_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Database initialized successfully!' AS status;
```

- [ ] **Step 2: 创建 README 说明**

```markdown
# scripts/README.md

## 数据库初始化

### 手动初始化

```bash
# 使用 root 用户初始化
mysql -u root -p < scripts/init_db.sql

# 或指定 host
mysql -h localhost -u root -p < scripts/init_db.sql
```

### 应用自动初始化

设置环境变量启用 MySQL：

```bash
export USE_MYSQL=true
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=qrc_session

python main.py
```

应用启动时会自动创建表结构（如果不存在）。
```

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "docs: 添加数据库初始化脚本和说明

- scripts/init_db.sql: 创建数据库和表结构
- scripts/README.md: 初始化和配置说明"
```

---

## Chunk 4: 测试与验证

### Task 9: 创建集成测试

**Files:**
- Create: `tests/integration/test_session_mysql.py`

- [ ] **Step 1: 编写集成测试**

```python
# tests/integration/test_session_mysql.py
"""
MySQL 会话存储集成测试

需要本地 MySQL 服务运行：
- docker run --name mysql-test -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -d mysql:8.0

运行测试：
    pytest tests/integration/test_session_mysql.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.session.store.mysql import MySQLSessionStore
from src.core.session.models import Session, Turn
from langchain_core.messages import HumanMessage, AIMessage


@pytest.fixture
async def mysql_store():
    """创建测试用 MySQL store"""
    # 测试数据库
    database_url = "mysql+asyncmy://root:123456@localhost:3306/qrc_session_test"

    engine = create_async_engine(database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=type("AsyncSession", (), {}), expire_on_commit=False)

    # 创建测试表
    from src.core.session.db_models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    store = MySQLSessionStore(session_maker)
    yield store

    # 清理测试数据
    async with session_maker() as session:
        from sqlalchemy import delete, text
        from src.core.session.db_models import SessionModel
        await session.execute(delete(SessionModel))
        await session.commit()

    await engine.dispose()

    # 等待异步清理完成
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_get_or_create_session(mysql_store):
    """测试获取或创建会话"""
    session = await mysql_store.get_session("test_user_test_channel")

    assert session.session_id == "test_user_test_channel"
    assert session.user_id == "test_user"
    assert session.channel_id == "test_channel"


@pytest.mark.asyncio
async def test_save_and_reload_session(mysql_store):
    """测试保存和重新加载会话"""
    # 创建会话
    session = Session(
        session_id="save_test_session",
        user_id="save_test",
        channel_id="test",
    )

    # 添加一个 turn
    session.add_turn(
        agent_name="test_agent",
        messages=[HumanMessage(content="Hello"), AIMessage(content="Hi")],
        final_reply="Hi there!",
    )

    # 保存
    await mysql_store.save_session(session)

    # 重新加载
    reloaded = await mysql_store.get_session("save_test_session")

    assert reloaded.session_id == session.session_id
    assert len(reloaded.turns) == 1
    assert reloaded.turns[0].agent_name == "test_agent"
    assert reloaded.turns[0].final_reply == "Hi there!"


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(mysql_store):
    """测试清理过期会话"""
    # 创建一个已过期会话
    session = Session(
        session_id="expired_session",
        user_id="expired",
        channel_id="test",
        expires_at=datetime.now() - timedelta(minutes=1),  # 已过期
    )

    await mysql_store.save_session(session)

    # 清理
    await mysql_store.cleanup_expired()

    # 验证已删除
    result = await mysql_store.get_session("expired_session")
    # 应该创建新会话，而不是返回过期的
    assert result.created_at > session.created_at or result.session_id != "expired_session"
```

- [ ] **Step 2: 运行集成测试（需要 MySQL）**

```bash
# 先启动测试用 MySQL
docker run --name mysql-test -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -d mysql:8.0

# 等待 MySQL 就绪
sleep 10

# 创建测试数据库
mysql -h 127.0.0.1 -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS qrc_session_test;"

# 运行测试
pytest tests/integration/test_session_mysql.py -v

# 清理
docker rm -f mysql-test
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "test: 添加 MySQL 会话存储集成测试

- 测试 get_session 创建和加载
- 测试 save_session 持久化
- 测试 cleanup_expired 清理过期会话"
```

---

### Task 10: 运行所有测试验证

**Files:** 无

- [ ] **Step 1: 运行单元测试**

```bash
pytest tests/unit/ -v
```

Expected: 所有单元测试通过

- [ ] **Step 2: 运行集成测试**

```bash
pytest tests/integration/ -v
```

Expected: 集成测试通过（需要 MySQL）

- [ ] **Step 3: 手动启动应用验证**

```bash
# 使用内存模式（默认）
python main.py

# 使用 MySQL 模式
export USE_MYSQL=true
python main.py

# 健康检查
curl http://localhost:8000/api/v1/health
```

Expected: 应用正常启动，日志显示正确的存储模式

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: 验证所有测试通过"
```

---

## 验收检查

完成所有任务后，运行以下检查：

```bash
# 1. 检查配置切换
python -c "
from src.config import Config
c = Config()
c.USE_MYSQL = False
print(f'Memory mode: {c.get_database_url()}')
c.USE_MYSQL = True
print(f'MySQL mode: {c.get_database_url()}')
"

# 2. 检查 ORM 模型
python -c "
from src.core.session.db_models import SessionModel, TurnModel
print('ORM models imported successfully')
"

# 3. 检查存储实现
python -c "
from src.core.session.store import BaseSessionStore, MemorySessionStore
print('Store implementations available')
"

# 4. 运行所有测试
pytest tests/ -v
```

---

## 后续工作

- [ ] 性能测试（对比内存和 MySQL 模式）
- [ ] 连接池配置优化
- [ ] 监控和日志增强
- [ ] 生产环境配置（环境变量覆盖）
