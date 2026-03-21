"""MySQL 会话存储实现"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.session.models import Session, Turn
from src.core.session.store.base import BaseSessionStore
from src.core.session.db_models import SessionModel, TurnModel


class MySQLSessionStore(BaseSessionStore):
    """MySQL 会话存储"""

    def __init__(self, session_maker: async_sessionmaker):
        self._session_maker = session_maker
        self._logger = logging.getLogger("MySQLSessionStore")

    async def get_session(self, session_id: str) -> Session:
        """获取会话，不存在则创建"""
        async with self._session_maker() as session:
            # 查询 SessionModel
            result = await session.execute(
                select(SessionModel).where(SessionModel.session_id == session_id)
            )
            session_model = result.scalar_one_or_none()

            if session_model is None:
                # 解析 session_id 获取 user_id 和 channel_id
                parts = session_id.split("_", 1)
                user_id = parts[0] if len(parts) > 0 else ""
                channel_id = parts[1] if len(parts) > 1 else ""

                return self._create_new_session(session_id, user_id, channel_id)

            # 转换为领域模型
            return self._to_domain_session(session_model)

    async def save_session(self, session: Session) -> None:
        """保存会话"""
        async with self._session_maker() as db_session:
            # 先保存/更新 Session
            session_model = await self._upsert_session(db_session, session)

            # 同步 Turns（差量更新）
            await self._sync_turns(db_session, session_model, session)

            await db_session.commit()

    async def cleanup_expired(self) -> None:
        """清理过期会话"""
        async with self._session_maker() as session:
            now = datetime.now()
            await session.execute(
                delete(SessionModel).where(SessionModel.expires_at < now)
            )
            await session.commit()
            self._logger.info("Cleaned up expired sessions")

    def _create_new_session(
        self, session_id: str, user_id: str, channel_id: str
    ) -> Session:
        """创建新会话"""
        self._logger.debug(f"Created new session in DB: {session_id}")
        return Session(
            session_id=session_id,
            user_id=user_id,
            channel_id=channel_id,
        )

    def _to_domain_session(self, model: SessionModel) -> Session:
        """将 ORM 模型转换为领域模型"""
        session = Session(
            session_id=model.session_id,
            user_id=model.user_id,
            channel_id=model.channel_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
            summary=model.summary or "",
        )

        # 转换 Turns
        for turn_model in model.turns:
            turn = Turn(
                turn_id=turn_model.turn_id,
                agent_name=turn_model.agent_name,
                messages=self._deserialize_messages(turn_model.messages),
                final_reply=turn_model.final_reply or "",
                created_at=turn_model.created_at,
                is_compressed=turn_model.is_compressed,
            )
            session.turns.append(turn)

        return session

    async def _upsert_session(
        self, db_session, session: Session
    ) -> SessionModel:
        """保存或更新 Session"""
        # 尝试查询现有记录
        result = await db_session.execute(
            select(SessionModel).where(SessionModel.session_id == session.session_id)
        )
        session_model = result.scalar_one_or_none()

        if session_model is None:
            # 插入新记录
            session_model = SessionModel(
                session_id=session.session_id,
                user_id=session.user_id,
                channel_id=session.channel_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                expires_at=session.expires_at,
                summary=session.summary,
            )
            db_session.add(session_model)
            await db_session.flush()  # 获取 ID
        else:
            # 更新现有记录
            session_model.user_id = session.user_id
            session_model.channel_id = session.channel_id
            session_model.updated_at = session.updated_at
            session_model.expires_at = session.expires_at
            session_model.summary = session.summary

        return session_model

    async def _sync_turns(
        self, db_session, session_model: SessionModel, session: Session
    ) -> None:
        """同步 Turns 数据（差量更新）"""
        # 获取现有 turn_ids
        existing_turn_ids = {t.turn_id for t in session_model.turns}
        new_turn_ids = {t.turn_id for t in session.turns}

        # 删除不存在的 turns
        turns_to_delete = existing_turn_ids - new_turn_ids
        if turns_to_delete:
            await db_session.execute(
                delete(TurnModel).where(
                    TurnModel.turn_id.in_(turns_to_delete)
                )
            )

        # 更新或插入 turns
        for turn in session.turns:
            if turn.turn_id in existing_turn_ids:
                # 更新现有
                turn_model = next(
                    t for t in session_model.turns if t.turn_id == turn.turn_id
                )
                turn_model.agent_name = turn.agent_name
                turn_model.messages = self._serialize_messages(turn.messages)
                turn_model.final_reply = turn.final_reply
                turn_model.is_compressed = turn.is_compressed
            else:
                # 插入新 turn
                turn_model = TurnModel(
                    turn_id=turn.turn_id,
                    session_id=session_model.session_id,
                    agent_name=turn.agent_name,
                    messages=self._serialize_messages(turn.messages),
                    final_reply=turn.final_reply,
                    is_compressed=turn.is_compressed,
                )
                db_session.add(turn_model)

    def _serialize_messages(self, messages: list) -> str:
        """序列化消息列表为 JSON"""
        from langchain_core.messages import BaseMessage

        serialized = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                serialized.append(msg.model_dump())
            else:
                serialized.append(msg)
        return json.dumps(serialized, ensure_ascii=False, default=str)

    def _deserialize_messages(self, data: str) -> list:
        """从 JSON 反序列化消息列表"""
        if not data:
            return []

        try:
            messages_data = json.loads(data)
            # 返回原始数据，由 Session.get_context_messages 处理
            return messages_data
        except json.JSONDecodeError:
            self._logger.error(f"Failed to deserialize messages: {data}")
            return []
