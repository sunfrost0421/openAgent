"""Web Controller - 前端 API 接口"""

import logging
from typing import List, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
_logger = logging.getLogger("WebController")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    created_at: str
    updated_at: str


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    user_id: str


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str


@router.get("/sessions", response_model=Dict[str, List[SessionInfo]])
async def list_sessions() -> Dict[str, List[SessionInfo]]:
    """获取会话列表"""
    # 当前实现返回空列表，实际使用时从存储中获取
    return {"sessions": []}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """创建新会话"""
    # 前端生成 session_id，后端只需确认
    return CreateSessionResponse(session_id=f"{request.user_id}_{datetime.now().isoformat()}")


@router.delete("/sessions/{session_id}", response_model=Dict[str, bool])
async def delete_session(session_id: str) -> Dict[str, bool]:
    """删除会话"""
    # 当前实现直接返回成功
    return {"success": True}
