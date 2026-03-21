"""DatabaseManager 单元测试"""
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
