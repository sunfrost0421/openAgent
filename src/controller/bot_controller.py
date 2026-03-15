"""Bot Controller - 机器人入口"""

import logging

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from src.orchestration.master_workflow import master_workflow


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


router = APIRouter()
_logger = logging.getLogger("BotController")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """处理聊天请求

    Args:
        request: 聊天请求

    Returns:
        聊天响应

    Raises:
        HTTPException: 当请求无效时
    """
    try:
        _logger.info(
            f"Chat request from user={request.user_id}, "
            f"channel={request.channel_id}"
        )

        # 执行工作流
        result = await master_workflow.execute(
            user_id=request.user_id,
            channel_id=request.channel_id,
            message=request.message
        )

        _logger.info(
            f"Chat response: agent={result.agent_name}, "
            f"reply={result.final_reply[:50]}..."
        )

        return ChatResponse(
            session_id=f"{request.user_id}_{request.channel_id}",
            reply=result.final_reply,
            agent_name=result.agent_name
        )

    except ValueError as e:
        _logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
