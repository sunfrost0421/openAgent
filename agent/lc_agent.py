"""LangChain 代理 - 使用 LangChain create_agent 与 OpenAI。"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from core.registry.agent_registry import get_registry

# 初始化注册表
registry = get_registry()


def create_lc_agent() -> ChatOpenAI:
    """创建 LangChain OpenAI 代理。"""
    return ChatOpenAI(
        model="glm-4.7",
        base_url="https://coding.dashscope.aliyuncs.com/v1",
        api_key="sk-sp-b6c188b0bd9d478ca5fba8b8b34cc5f1"
    )


@registry.register(
    name="lc_agent",
    description="使用 LangChain 和 OpenAI 的通用 Q&A 代理",
    intents=["general_qa", "knowledge_search"]
)
def run_lc_agent(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行 LangChain 代理。

    Args:
        params: 包含 'input_text'、'messages' 和 'intent' 的字典

    Returns:
        包含 'output_text' 和 'messages' 的字典
    """
    input_text = params.get("input_text", "")
    messages = params.get("messages", [])
    intent = params.get("intent", "general_qa")

    # 创建 LLM
    llm = create_lc_agent()

    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个有用的 AI 助手。
        你专注于 {intent} 任务。

        对于 general_qa：直接且简洁地回答问题。
        对于 knowledge_search：帮助搜索和总结信息。

        让你的回答有帮助、准确且简洁。"""),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{input}")
    ])

    # 创建代理
    agent_prompt = prompt.partial(
        intent=intent,
        messages=messages,
        input=input_text
    )

    # 生成响应
    response = llm.invoke(agent_prompt.messages)

    # 添加到消息列表
    updated_messages = messages + [
        HumanMessage(content=input_text),
        response
    ]

    return {
        "output_text": response.content if hasattr(response, 'content') else str(response),
        "messages": updated_messages,
        "agent_name": "lc_agent"
    }


# 导出供直接使用
__all__ = ["run_lc_agent", "create_lc_agent"]
