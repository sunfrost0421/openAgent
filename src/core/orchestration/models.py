"""共享类型定义"""

from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class AgentMetadata:
    """Agent 元数据"""
    name: str
    description: str
    keywords: List[str]
    command: Optional[str] = None


class IntentMatch(BaseModel):
    """意图匹配结果"""
    agent_name: str = Field(description="匹配的 Agent 名称")
    confidence: float = Field(description="置信度，0-1 之间")
    reason: str = Field(description="匹配原因")


class IntentResult(BaseModel):
    """意图识别结果"""
    agent_name: str
    confidence: float
    reason: str
    match_type: str  # "command", "keyword", "llm"
