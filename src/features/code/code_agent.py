"""Code Agent - 代码助手（支持工具调用）"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from src.core.orchestration.executor import BaseExecutor
from src.core.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.features.prompts import Prompts
from src.features.code.tools import get_all_tools


@agent_registry.register(
    name="code_agent",
    description="处理代码相关请求，包括编写、解释、调试代码，支持文件读写和代码执行",
    keywords=[
        "代码", "编程", "function", "class", "def", "import",
        "write code", "code", "function", "class", "bug", "debug",
        "file", "read", "write", "execute", "run"
    ],
    command="@code"
)
class CodeAgent(BaseExecutor):
    """Code Agent - 代码助手（支持工具调用）"""

    def __init__(self, session, user_message, session_manager=None):
        """初始化 CodeAgent

        Args:
            session: 当前会话
            user_message: 用户输入消息
            session_manager: 会话管理器
        """
        super().__init__(session, user_message, session_manager)

        # 初始化工具和 agent
        self.tools = get_all_tools()
        self.llm = create_llm()

        # 创建 agent（使用内存 Checkpointer）
        # 注：checkpointer 用于 Agent 内部状态持久化，与 SessionManager 独立
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=MemorySaver()  # 开发阶段使用内存
        )

    async def run(self) -> List[BaseMessage]:
        """执行代码相关任务

        Returns:
            消息列表（LangChain 格式）
        """
        # 构建消息
        messages = [
            SystemMessage(content=Prompts.get("code_agent")),
            *self.get_context_messages(),
            HumanMessage(content=self.user_message)
        ]

        # 调用 agent（自动工具选择和执行）
        result = await self.agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": f"{self.session.user_id}_{self.session.channel_id}"}}
        )

        return result["messages"]
