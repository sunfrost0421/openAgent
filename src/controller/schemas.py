"""请求/响应模型"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求"""
    user_id: str
    channel_id: str
    message: str


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    reply: str
    agent_name: str
