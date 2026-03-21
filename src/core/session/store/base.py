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
