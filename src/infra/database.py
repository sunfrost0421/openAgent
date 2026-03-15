"""数据库连接模块 - 第一版为内存实现，后续扩展到 MySQL"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


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
