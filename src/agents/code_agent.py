"""Code Agent - 代码助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求，包括编写、解释、调试代码",
    keywords=[
        "代码", "编程", "function", "class", "def", "import",
        "write code", "code", "function", "class", "bug", "debug"
    ],
    command="@code"
)
class CodeAgent(BaseExecutor):
    """Code Agent - 代码助手"""

    async def run(self) -> List[BaseMessage]:
        """执行代码相关任务"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
