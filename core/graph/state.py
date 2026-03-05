"""LangGraph 状态定义，用于编排器。"""

from typing import TypedDict, Optional, Any, Dict, List, Annotated
from langchain_core.messages import BaseMessage


def messages_reducer(
    existing: Optional[List[BaseMessage]],
    new: Optional[List[BaseMessage]]
) -> List[BaseMessage]:
    """通过追加新消息来归约消息列表。"""
    if existing is None:
        return new or []
    if new is None:
        return existing
    return existing + new


class OrchestratorState(TypedDict, total=False):
    """
    编排器 LangGraph 的状态。

    Attributes:
        user_id: 用户标识符
        channel: 渠道标识符（例如 'web'、'api'、'slack'）
        session_id: 会话标识符
        input_text: 用户输入文本
        # 意图识别结果
        intent: 识别的意图类型
        confidence: 意图识别的置信度
        reason: 意图分类的原因
        # 路由
        target_agent: 要执行的目标代理名称
        agent_params: 传递给代理的参数
        # 对话和输出
        messages: 对话消息列表
        output_text: 最终输出文本
        error: 错误消息（如果有）
    """
    # 会话信息
    user_id: str
    channel: str
    session_id: str

    # 输入
    input_text: str

    # 意图识别结果
    intent: Optional[str]
    confidence: float
    reason: str

    # 路由
    target_agent: Optional[str]
    agent_params: Dict[str, Any]

    # 对话和输出
    messages: Annotated[List[BaseMessage], messages_reducer]
    output_text: str
    error: Optional[str]
