"""执行器基类"""

from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import BaseMessage

from src.core.session.models import Session
from src.core.session.manager import SessionManager


class BaseExecutor(ABC):
    """执行器基类

    所有 Agent 必须继承该类并实现 run 方法
    """

    def __init__(
        self,
        session: Session,
        user_message: str,
        session_manager: SessionManager | None = None,
    ):
        """初始化执行器

        Args:
            session: 当前会话
            user_message: 用户输入消息
            session_manager: 会话管理器，用于获取历史上下文
        """
        self.session = session
        self.user_message = user_message
        self._session_manager = session_manager

    @property
    def agent_name(self) -> str:
        """获取 Agent 名称（子类名）"""
        return self.__class__.__name__

    def get_context_messages(self) -> List[BaseMessage]:
        """获取历史上下文消息

        从配置中获取参数，委托给 Session.get_context_messages() 实现

        Returns:
            历史上下文消息列表，如果没有 session_manager 则返回空列表
        """
        if self._session_manager is None:
            return []
        from src.config import Config
        config = Config.get()
        return self.session.get_context_messages(
            keep_turns=config.CONTEXT_KEEP_TURNS,
            max_tokens=config.CONTEXT_MAX_TOKENS
        )

    @abstractmethod
    async def run(self) -> List[BaseMessage]:
        """执行 Agent 逻辑

        Returns:
            消息列表（LangChain 格式）
        """
        pass
