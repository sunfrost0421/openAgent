"""会话管理器"""

from typing import List

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from src.core.session_store import Session, Turn
from src.core.memory_session_store import MemorySessionStore
from src.config import Config


class SessionManager:
    """会话管理器

    负责：
    - 会话的获取和保存
    - 轮次的添加和压缩
    - 上下文消息的提取
    """

    def __init__(self, store: MemorySessionStore | None = None):
        """初始化会话管理器

        Args:
            store: 会话存储实例，默认使用全局 memory_session_store
        """
        self._store = store or MemorySessionStore()
        self._config = Config.get()

    def create_session_id(self, user_id: str, channel_id: str) -> str:
        """创建会话 ID"""
        return f"{user_id}_{channel_id}"

    async def get_or_create_session(
        self, user_id: str, channel_id: str
    ) -> Session:
        """获取或创建会话"""
        session_id = self.create_session_id(user_id, channel_id)
        return await self._store.get_session(session_id)

    async def add_turn(
        self,
        session: Session,
        agent_name: str,
        user_message: str,
        messages: List[BaseMessage],
        final_reply: str,
    ) -> Turn:
        """添加对话轮次

        Args:
            session: 会话实例
            agent_name: 执行 Agent 名称
            user_message: 用户输入消息
            messages: 完整消息列表（包含中间交互）
            final_reply: 最终回复

        Returns:
            添加的 Turn 实例
        """
        # 确保消息列表包含用户输入
        if not messages or not isinstance(messages[0], HumanMessage):
            messages = [HumanMessage(content=user_message), *messages]

        turn = session.add_turn(
            agent_name=agent_name,
            messages=messages,
            final_reply=final_reply
        )

        # 自动压缩最老的未压缩轮次
        self._compress_old_turns(session)

        await self._store.save_session(session)
        return turn

    def _compress_old_turns(self, session: Session) -> None:
        """压缩旧的轮次，只保留最近的 keep_turns 轮完整上下文"""
        keep_turns = self._config.CONTEXT_KEEP_TURNS
        turns_to_compress = max(0, len(session.turns) - keep_turns)

        for i in range(turns_to_compress):
            if not session.turns[i].is_compressed:
                session.turns[i].compress()

    def get_context_messages(self, session: Session) -> List[BaseMessage]:
        """获取会话上下文消息"""
        return session.get_context_messages(
            keep_turns=self._config.CONTEXT_KEEP_TURNS
        )

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        await self._store.cleanup_expired()


# 全局会话管理器实例
session_manager = SessionManager()
