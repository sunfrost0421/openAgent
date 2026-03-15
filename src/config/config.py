from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """系统配置"""

    # LLM 配置
    OPENAI_API_KEY: Optional[str] = "sk-sp-b6c188b0bd9d478ca5fba8b8b34cc5f1"
    OPENAI_BASE_URL: Optional[str] = "https://coding.dashscope.aliyuncs.com/v1"
    DEFAULT_MODEL: str = "qwen3.5-plus"
    INTENT_MODEL: str = "qwen3.5-plus"

    # 意图识别配置
    INTENT_CONFIDENCE_THRESHOLD: float = 0.6

    # 会话管理配置
    SESSION_TIMEOUT_MINUTES: int = 30
    CONTEXT_KEEP_TURNS: int = 3  # 保留多少轮的完整上下文

    @classmethod
    def get(cls) -> "Config":
        """获取全局配置实例"""
        return _global_config


_global_config = Config()