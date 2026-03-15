"""Default Agent - 通用聊天助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="default_agent",
    description="通用聊天助手，处理意图不清晰的请求",
    keywords=["你好", "hello", "hi", "早上好", "下午好", "晚上好"],
    command=None
)
class DefaultAgent(BaseExecutor):
    """Default Agent - 通用聊天助手"""

    async def run(self) -> List[BaseMessage]:
        """执行通用聊天逻辑"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("default_agent")),
            *self.get_context_messages(),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
