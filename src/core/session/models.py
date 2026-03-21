"""会话数据模型"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from langchain_core.messages import BaseMessage


@dataclass
class Turn:
    """对话轮次"""
    turn_id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    messages: List[BaseMessage] = field(default_factory=list)
    final_reply: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_compressed: bool = False

    def compress(self) -> None:
        """压缩轮次，只保留最终回复"""
        self.is_compressed = True


@dataclass
class Session:
    """会话"""
    session_id: str = ""
    user_id: str = ""
    channel_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=30))
    turns: List[Turn] = field(default_factory=list)
    summary: str = ""  # 累积摘要（用于 LangChain 式压缩）

    def add_turn(self, agent_name: str, messages: List[BaseMessage], final_reply: str) -> Turn:
        """添加新轮次，并压缩最老的轮次"""
        # 压缩最老的未压缩轮次
        for turn in self.turns:
            if not turn.is_compressed:
                turn.compress()
                break

        turn = Turn(
            agent_name=agent_name,
            messages=messages,
            final_reply=final_reply
        )
        self.turns.append(turn)
        self.updated_at = datetime.now()
        return turn

    def get_context_messages(self, keep_turns: int = 3, max_tokens: int = 8000) -> List[BaseMessage]:
        """获取上下文消息

        Args:
            keep_turns: 保留完整上下文的轮次数
            max_tokens: 最大 token 数，超过时启用摘要

        Returns:
            用于 LLM 上下文的消息列表
        """
        messages = []

        # 如果有摘要，先添加摘要
        if self.summary:
            from langchain_core.messages import SystemMessage
            messages.append(SystemMessage(content=f"[历史对话摘要]: {self.summary}"))

        # 最近的 keep_turns 轮使用完整消息，之前的只使用 final_reply
        for i, turn in enumerate(self.turns):
            if i >= len(self.turns) - keep_turns:
                # 最近的轮次，使用完整消息
                messages.extend(turn.messages)
            else:
                # 较远的轮次，只使用最终回复
                if turn.final_reply:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=turn.final_reply))

        # 检查 token 数量，超过阈值时压缩
        from langchain_core.messages.utils import count_tokens_approximately
        current_tokens = count_tokens_approximately(messages)

        # 如果超过最大 token 数且有未压缩的轮次，压缩最老的轮次
        if current_tokens > max_tokens and len(self.turns) > keep_turns:
            # 找到第一个未压缩的轮次并压缩
            for turn in self.turns:
                if not turn.is_compressed:
                    turn.compress()
                    break

        return messages
