"""会话管理器 - Thread ID 生成和会话管理。"""

import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionInfo:
    """会话信息。"""
    user_id: str
    channel: str
    session_id: str

    @property
    def thread_id(self) -> str:
        """以格式生成 thread_id: {user_id}::{channel}::{session_id}"""
        return f"{self.user_id}::{self.channel}::{self.session_id}"

    @classmethod
    def from_thread_id(cls, thread_id: str) -> "SessionInfo":
        """将 thread_id 解析回 SessionInfo。"""
        parts = thread_id.split("::")
        if len(parts) != 3:
            raise ValueError(f"Invalid thread_id format: {thread_id}")
        return cls(
            user_id=parts[0],
            channel=parts[1],
            session_id=parts[2]
        )


class SessionManager:
    """管理会话和 thread_id 生成。"""

    def create_session(
        self,
        user_id: str,
        channel: str,
        session_id: Optional[str] = None
    ) -> SessionInfo:
        """
        创建新会话。

        Args:
            user_id: 用户标识符
            channel: 渠道标识符
            session_id: 可选的会话 ID（如不提供则自动生成）

        Returns:
            包含生成的 thread_id 的 SessionInfo
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        return SessionInfo(
            user_id=user_id,
            channel=channel,
            session_id=session_id
        )

    def get_thread_id(
        self,
        user_id: str,
        channel: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        为给定的会话参数生成 thread_id。

        Args:
            user_id: 用户标识符
            channel: 渠道标识符
            session_id: 可选的会话 ID（如不提供则自动生成）

        Returns:
            Thread ID 字符串
        """
        session = self.create_session(user_id, channel, session_id)
        return session.thread_id

    def parse_thread_id(self, thread_id: str) -> SessionInfo:
        """
        将 thread_id 解析回会话组件。

        Args:
            thread_id: Thread ID 字符串

        Returns:
            SessionInfo 对象
        """
        return SessionInfo.from_thread_id(thread_id)

    def create_config(self, thread_id: str) -> dict:
        """
        创建包含 thread_id 的 LangGraph 配置。

        Args:
            thread_id: Thread ID 字符串

        Returns:
            用于 LangGraph 的配置字典
        """
        return {
            "configurable": {
                "thread_id": thread_id
            }
        }


# 全局会话管理器实例
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例。"""
    return session_manager
