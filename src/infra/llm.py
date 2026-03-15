"""LLM 封装模块"""

from langchain_openai import ChatOpenAI
from src.config import Config


def create_llm(model: str | None = None, **kwargs) -> ChatOpenAI:
    """创建 LLM 实例

    Args:
        model: 模型名称，默认使用 DEFAULT_MODEL
        **kwargs: 传递给 ChatOpenAI 的其他参数

    Returns:
        ChatOpenAI 实例
    """
    config = Config.get()

    return ChatOpenAI(
        model=model or config.DEFAULT_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
        **kwargs
    )


def create_intent_llm() -> ChatOpenAI:
    """创建意图识别专用 LLM 实例

    Returns:
        ChatOpenAI 实例，使用 INTENT_MODEL
    """
    return create_llm(model=Config.get().INTENT_MODEL, temperature=0)
