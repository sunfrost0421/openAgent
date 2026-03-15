"""Plan Agent - 计划管理助手"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.agents.prompts import Prompts


@agent_registry.register(
    name="plan_agent",
    description="帮助用户制定和管理计划、任务",
    keywords=[
        "计划", "任务", "todo", "schedule", "plan", "task",
        "安排", "日程", "待办"
    ],
    command="@plan"
)
class PlanAgent(BaseExecutor):
    """Plan Agent - 计划管理助手"""

    async def run(self) -> List[BaseMessage]:
        """执行计划管理相关任务"""
        llm = create_llm()

        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("plan_agent")),
            HumanMessage(content=self.user_message)
        ]

        # 调用 LLM
        response = await llm.ainvoke(messages)

        return [response]
