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
    CONTEXT_KEEP_TURNS: int = 3  # 保留多少轮的完整上下文（基于轮次的压缩）

    # 上下文压缩配置（基于 LangChain SummarizationMiddleware）
    CONTEXT_MAX_TOKENS: int = 8000  # 上下文最大 token 数
    CONTEXT_SUMMARY_THRESHOLD: float = 0.8  # 触发摘要的阈值（80%）
    CONTEXT_KEEP_RECENT_MESSAGES: int = 10  # 保留最近 N 条消息（基于 token 的压缩）
    SUMMARY_MODEL: str = "qwen3.5-plus"  # 摘要生成模型

    # ========== 新增：MySQL 配置 ==========
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "qrc_session"
    USE_MYSQL: bool = False  # 默认使用内存存储，需要时开启

    @classmethod
    def get(cls) -> "Config":
        """获取全局配置实例"""
        return _global_config

    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.USE_MYSQL:
            return (
                f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            )
        else:
            return "sqlite+aiosqlite:///:memory:"


_global_config = Config()