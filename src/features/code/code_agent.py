"""Code Agent - 代码助手（支持工具调用）"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

from src.core.orchestration.executor import BaseExecutor
from src.core.orchestration.registry import agent_registry
from src.infra.llm import create_llm
from src.features.prompts import Prompts
from src.features.code.tools import get_all_tools
from src.config import Config


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

        # 获取配置
        config = Config.get()

        # 创建 agent（带上下文压缩中间件）
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            middleware=[
                SummarizationMiddleware(
                    model=self.llm,
                    trigger=("tokens", config.CONTEXT_MAX_TOKENS),
                    keep=("messages", config.CONTEXT_KEEP_RECENT_MESSAGES)
                )
            ],
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
            {"messages": messages}
        )

        return result["messages"]
