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
