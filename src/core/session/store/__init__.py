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
