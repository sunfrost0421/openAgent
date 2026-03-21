"""数据库连接模块"""

from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# 全局 Base 类，用于 ORM 模型定义
Base = declarative_base()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str | None = None):
        """初始化数据库管理器

        Args:
            database_url: 数据库连接 URL，为 None 时从配置读取
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
