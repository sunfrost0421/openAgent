"""内存会话存储实现"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from src.core.session_store import BaseSessionStore, Session


class MemorySessionStore(BaseSessionStore):
    """内存会话存储"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger("MemorySessionStore")

    async def get_session(self, session_id: str) -> Session:
        """获取会话，不存在则创建"""
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session(session_id=session_id)
                self._logger.debug(f"Created new session: {session_id}")
            return self._sessions[session_id]

    async def save_session(self, session: Session) -> None:
        """保存会话"""
        async with self._lock:
            self._sessions[session.session_id] = session
            self._logger.debug(f"Saved session: {session.session_id}")

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        async with self._lock:
            now = datetime.now()
            expired = [
                sid for sid, s in self._sessions.items()
                if s.expires_at < now
            ]
            for sid in expired:
                del self._sessions[sid]
                self._logger.debug(f"Cleaned up expired session: {sid}")
            if expired:
                self._logger.info(f"Cleaned up {len(expired)} expired sessions")


# 全局内存会话存储实例
memory_session_store = MemorySessionStore()
