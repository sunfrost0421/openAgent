"""
配置管理模块
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import timedelta


class Settings(BaseSettings):
    """系统配置"""

    # LLM 配置
    OPENAI_API_KEY: Optional[str] = "***"
    OPENAI_BASE_URL: Optional[str] = "https://coding.dashscope.aliyuncs.com/v1"
    DEFAULT_MODEL: str = "glm-4.7"

    # 会话管理配置
    SESSION_TIMEOUT_MINUTES: int = 30  # 30 分钟无活动自动释放
    SESSION_CHECK_INTERVAL: int = 60  # 每 60 秒检查一次过期会话

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # 日志配置
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
