"""意图相关的数据结构。"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class IntentType(str, Enum):
    """支持的意图类型。"""
    GENERAL_QA = "general_qa"
    KNOWLEDGE_SEARCH = "knowledge_search"
    COMPLEX_REASONING = "complex_reasoning"
    PLANNING = "planning"
    FALLBACK = "fallback"


@dataclass
class IntentResult:
    """意图分析的结果。"""
    intent: str
    confidence: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "reason": self.reason,
            "metadata": self.metadata
        }


@dataclass
class IntentConfig:
    """意图识别的配置。"""
    keywords: dict[str, list[str]] = field(default_factory=lambda: {
        "planning": ["规划", "分解", "复杂", "plan", "计划", "步骤"],
        "knowledge_search": ["搜索", "查找", "查询", "search", "find"],
        "complex_reasoning": ["推理", "分析", "原因", "reason", "analyze"],
        "general_qa": [],  # Default fallback
    })
    default_intent: str = "general_qa"
    confidence_threshold: float = 0.5
