# MySQL 会话存储设计文档

**日期**: 2026-03-21
**主题**: 会话管理后端改造为本地 MySQL 存储

---

## 1. 现状分析

### 1.1 当前架构

当前会话管理采用**纯内存实现**：

```
src/
├── config/
│   └── config.py              # 会话配置 (SESSION_TIMEOUT_MINUTES, CONTEXT_KEEP_TURNS)
├── core/session/
│   ├── models.py              # Session, Turn 数据类 + BaseSessionStore 抽象基类
│   ├── store.py               # MemorySessionStore 内存实现
│   └── manager.py             # SessionManager 会话管理逻辑
└── infra/
    └── database.py            # DatabaseManager (支持 SQLAlchemy 异步连接)
```

### 1.2 当前数据模型

**Session** (数据类):
- `session_id`: 业务主键 (`{user_id}_{channel_id}`)
- `user_id`, `channel_id`: 用户和渠道标识
- `created_at`, `updated_at`, `expires_at`: 时间戳
- `turns`: 对话轮次列表
- `summary`: 累积摘要

**Turn** (数据类):
- `turn_id`: UUID
- `agent_name`: 执行 Agent 名称
- `messages`: 完整消息列表 (LangChain BaseMessage)
- `final_reply`: 最终回复
- `is_compressed`: 是否已压缩

### 1.3 发现的问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 数据易失 | 内存存储，应用重启后数据丢失 | 无法持久化会话历史 |
| 无法共享 | 多实例部署时会话隔离 | 不支持水平扩展 |
| 无法查询 | 无 SQL 查询能力 | 无法做统计分析 |
| 容量限制 | 受限于内存大小 | 高并发场景有风险 |

### 1.4 现有基础设施

`infra/database.py` 已有 `DatabaseManager` 类，支持 SQLAlchemy 异步连接：
- 当前默认使用 `sqlite+aiosqlite:///:memory:`
- 可无缝切换到 MySQL (`mysql+asyncmy://...`)

---

## 2. 目标架构

### 2.1 设计原则

1. **向后兼容**: 保留 `MemorySessionStore`，支持平滑切换
2. **接口统一**: `BaseSessionStore` 抽象基类保持不变
3. **依赖注入**: `SessionManager` 通过构造函数注入 store 实例
4. **配置开关**: 通过配置项控制使用哪种存储

### 2.2 新模块结构

```
src/
├── config/
│   └── config.py              # 新增 MySQL 配置项
├── infra/
│   └── database.py            # 补充 MySQL 初始化逻辑
├── core/
│   └── session/
│       ├── models.py          # SQLAlchemy ORM 模型
│       ├── store/
│       │   ├── __init__.py    # 统一导出
│       │   ├── base.py        # BaseSessionStore 基类
│       │   ├── memory.py      # MemorySessionStore
│       │   └── mysql.py       # MySQLSessionStore (新建)
│       └── manager.py         # SessionManager (不变)
```

### 2.3 依赖关系

```
controller/
    └── services/
          └── core/session/
                ├── infra/database.py
                └── config/config.py
```

---

## 3. 数据库设计

### 3.1 物理模型

```sql
-- sessions 表
CREATE TABLE sessions (
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
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- turns 表
CREATE TABLE turns (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.2 字段映射

| Session 字段 | 表字段 | 类型 | 说明 |
|--------------|--------|------|------|
| session_id | session_id | VARCHAR(255) | 业务主键 |
| user_id | user_id | VARCHAR(100) | 用户 ID |
| channel_id | channel_id | VARCHAR(100) | 渠道 ID |
| created_at | created_at | DATETIME | 创建时间 |
| updated_at | updated_at | DATETIME | 更新时间 |
| expires_at | expires_at | DATETIME | 过期时间 |
| summary | summary | TEXT | 累积摘要 |
| turns | (关联 turns 表) | - | 一对多关系 |

| Turn 字段 | 表字段 | 类型 | 说明 |
|-----------|--------|------|------|
| turn_id | turn_id | VARCHAR(255) | UUID 主键 |
| session_id | session_id | VARCHAR(255) | 外键 |
| agent_name | agent_name | VARCHAR(100) | Agent 名称 |
| messages | messages | JSON | 消息列表 (JSON 序列化) |
| final_reply | final_reply | TEXT | 最终回复 |
| created_at | created_at | DATETIME | 创建时间 |
| is_compressed | is_compressed | BOOLEAN | 压缩标志 |

### 3.3 SQLAlchemy ORM 模型

```python
# src/core/session/models.py
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.mysql import JSON

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    summary = Column(Text, nullable=True)

    turns = relationship("TurnModel", back_populates="session", cascade="all, delete-orphan")

class TurnModel(Base):
    __tablename__ = "turns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    turn_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), ForeignKey("sessions.session_id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    messages = Column(JSON, nullable=False)
    final_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    is_compressed = Column(Boolean, default=False)

    session = relationship("SessionModel", back_populates="turns")
```

---

## 4. 实现方案

### 4.1 配置变更

`config.py` 新增:

```python
# MySQL 配置
MYSQL_HOST: str = "localhost"
MYSQL_PORT: int = 3306
MYSQL_USER: str = "root"
MYSQL_PASSWORD: str = "123456"
MYSQL_DATABASE: str = "qrc_session"
USE_MYSQL: bool = True  # 开关，False 时使用内存存储

@classmethod
def get_database_url(cls) -> str:
    """获取数据库连接 URL"""
    if cls.USE_MYSQL:
        return f"mysql+asyncmy://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
    else:
        return "sqlite+aiosqlite:///:memory:"
```

### 4.2 DatabaseManager 扩展

`infra/database.py` 补充:

```python
class DatabaseManager:
    def __init__(self, database_url: str | None = None):
        """初始化数据库管理器

        Args:
            database_url: 数据库连接 URL，为 None 时从配置读取
        """
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
```

### 4.3 BaseSessionStore 接口

`core/session/store/base.py`:

```python
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

### 4.4 MySQLSessionStore 实现

`core/session/store/mysql.py`:

```python
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
                # 创建新会话
                return self._create_new_session(session_id)

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
```

### 4.5 SessionManager 依赖注入

`core/session/manager.py` 修改:

```python
class SessionManager:
    def __init__(self, store: BaseSessionStore | None = None):
        """初始化会话管理器

        Args:
            store: 会话存储实例，为 None 时使用默认配置
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
        # ... 其余逻辑不变
```

---

## 5. 工作流程

### 5.1 应用启动流程

```
1. main.py 启动
   │
   ▼
2. 读取 Config.USE_MYSQL
   │
   ├─ True ──→ DatabaseManager.init(create_tables=True)
   │            → 创建 MySQL 连接
   │            → 执行 Base.metadata.create_all() 建表
   │            → 初始化 MySQLSessionStore
   │
   └─ False ──→ 使用 MemorySessionStore (默认)
   │
   ▼
3. SessionManager(store=xxx) 注入 store 实例
   │
   ▼
4. FastAPI lifespan 返回，应用就绪
```

### 5.2 会话读写流程

```
读会话:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│SessionManager│────▶│MySQLSessionStore│────▶│  MySQL DB   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                     │                     │
      │ get_session(id)     │                     │
      ├────────────────────▶│                     │
      │                     │ SELECT sessions    │
      │                     ├────────────────────▶│
      │                     │                     │
      │                     │ SELECT turns       │
      │                     ├────────────────────▶│
      │                     │                     │
      │                     │◀────────────────────┤
      │◀────────────────────┤                     │
      │ Session 对象         │                     │
```

```
写会话:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│SessionManager│────▶│MySQLSessionStore│────▶│  MySQL DB   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                     │                     │
      │ save_session(s)     │                     │
      ├────────────────────▶│                     │
      │                     │ BEGIN TRANSACTION  │
      │                     ├────────────────────▶│
      │                     │                     │
      │                     │ INSERT/UPDATE      │
      │                     │ sessions + turns   │
      │                     ├────────────────────▶│
      │                     │                     │
      │                     │ COMMIT             │
      │                     ├────────────────────▶│
      │                     │                     │
      │◀────────────────────┤                     │
      │ OK                  │                     │
```

---

## 6. 迁移步骤

### 6.1 步骤分解

| 步骤 | 任务 | 预计工作量 |
|------|------|-----------|
| 1 | 创建 store/ 目录结构，移动 base.py, memory.py | 0.5h |
| 2 | 编写 models.py ORM 模型 | 0.5h |
| 3 | 实现 MySQLSessionStore | 1h |
| 4 | 扩展 DatabaseManager 支持自动建表 | 0.5h |
| 5 | 扩展 Config 增加 MySQL 配置项 | 0.3h |
| 6 | 修改 SessionManager 支持依赖注入 | 0.5h |
| 7 | 修改 main.py lifespan 初始化逻辑 | 0.3h |
| 8 | 编写单元测试 | 1h |
| 9 | 编写集成测试（需 MySQL 环境） | 1h |

### 6.2 测试策略

**单元测试**:
```python
# tests/unit/session/test_mysql_store.py
async def test_mysql_get_session_creates_if_not_exists():
    store = MySQLSessionStore(mock_session_maker)
    session = await store.get_session("test_user_test_channel")
    assert session.session_id == "test_user_test_channel"
```

**集成测试**:
```python
# tests/integration/test_session_mysql.py
@pytest.fixture
async def mysql_store():
    # 使用 docker-compose 启动临时 MySQL
    # 创建测试数据库
    # 初始化 DatabaseManager + MySQLSessionStore
    yield store
    # 清理测试数据

async def test_full_lifecycle(mysql_store):
    # get_session → add_turn → save_session → get_session → cleanup
    ...
```

---

## 7. 验收标准

- [ ] MySQL 存储可正常读写会话
- [ ] MemorySessionStore 仍然可用（向后兼容）
- [ ] 配置 `USE_MYSQL=false` 可切换回内存模式
- [ ] 应用启动自动建表（首次运行）
- [ ] 过期会话清理功能正常工作
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过（需 MySQL 环境）
- [ ] 文档更新（README 说明配置方法）

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| MySQL 连接失败 | 应用无法启动 | 添加连接重试机制，提供降级开关 |
| 序列化失败 (messages) | 数据丢失 | JSON 序列化前校验，失败时降级为 TEXT |
| 外键约束 | 删除 session 时 turns 未清理 | 使用 ON DELETE CASCADE |
| 时区问题 | 时间戳不一致 | 统一使用 UTC，应用层转换 |
| 字符集 | 中文乱码 | 使用 utf8mb4 字符集 |

---

## 9. 后续扩展

- [ ] Redis 缓存层（热点会话加速）
- [ ] 会话归档（冷数据迁移到历史表）
- [ ] 统计分析接口（基于 SQL 聚合查询）
- [ ] 分布式锁（多实例并发安全）
