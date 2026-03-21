"""MySQL 配置测试"""
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
