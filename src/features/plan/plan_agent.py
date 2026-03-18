"""Plan Agent - 计划管理助手（基于 DeepAgents）"""

from pathlib import Path
from typing import List

from langchain_core.messages import BaseMessage

from src.core.orchestration.executor import BaseExecutor
from src.core.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.features.prompts import Prompts


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
    """Plan Agent - 计划管理助手（基于 DeepAgents，支持 skill）"""

    def __init__(self, session, user_message, session_manager=None):
        """初始化 PlanAgent

        Args:
            session: 当前会话
            user_message: 用户输入消息
            session_manager: 会话管理器
        """
        super().__init__(session, user_message, session_manager)

        # 导入 deepagents（延迟导入，避免不必要的依赖）
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend

        # 获取 skills 目录路径
        skills_dir = Path(__file__).parent / "skills"

        # 创建 filesystem backend（virtual_mode=False 禁用虚拟路径，使用真实文件系统）
        self.backend = FilesystemBackend(root_dir=str(skills_dir), virtual_mode=False)

        # 创建 deep agent（带 skill 支持）
        self.agent = create_deep_agent(
            model=create_llm(),
            skills=["./"],  # 相对于 backend root_dir
            backend=self.backend,
            system_prompt=Prompts.get("plan_agent"),
        )

    async def run(self) -> List[BaseMessage]:
        """执行计划管理相关任务

        Returns:
            消息列表（LangChain 格式）
        """
        from langchain_core.messages import HumanMessage

        # 调用 deep agent（自动处理 skill 加载和执行）
        result = await self.agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=self.user_message),
                    *self.get_context_messages(),
                ]
            }
        )

        return result["messages"]
