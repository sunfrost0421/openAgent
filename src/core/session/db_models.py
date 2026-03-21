"""SQLAlchemy ORM 模型 - 会话存储"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    BigInteger,
    Index,
)
from sqlalchemy.orm import relationship

from src.infra.database import Base


class SessionModel(Base):
    """会话 ORM 模型"""

    __tablename__ = "sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, nullable=False, index=True)
    summary = Column(Text, nullable=True)

    # 一对多关系
    turns = relationship(
        "TurnModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"  # 预加载 turns
    )

    __table_args__ = (
        Index("idx_user_channel", "user_id", "channel_id"),
    )


class TurnModel(Base):
    """对话轮次 ORM 模型"""

    __tablename__ = "turns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    turn_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(
        String(255),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_name = Column(String(100), nullable=False)
    messages = Column(Text, nullable=False)  # JSON 字符串
    final_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    is_compressed = Column(Boolean, default=False)

    # 反向关系
    session = relationship("SessionModel", back_populates="turns")
