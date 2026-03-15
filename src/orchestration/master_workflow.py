"""主工作流：预处理 → 意图识别 → 执行器 → 后处理"""

import logging
from typing import NamedTuple

from langchain_core.messages import BaseMessage, AIMessage

from src.core.session_manager import SessionManager, session_manager as global_session_manager
from src.core.intent import IntentRecognizer, intent_recognizer as global_intent_recognizer, IntentResult
from src.core.session_store import Session
from src.orchestration.base_executor import BaseExecutor
from src.orchestration.registry import agent_registry
from src.config import Config


class WorkflowResult(NamedTuple):
    """工作流执行结果"""
    agent_name: str
    final_reply: str
    messages: list[BaseMessage]


class MasterWorkflow:
    """主工作流

    流程：
    1. 预处理：输入验证
    2. 意图识别：三层识别策略
    3. 执行器：执行对应 Agent
    4. 后处理：保存会话，格式化输出
    """

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        intent_recognizer: IntentRecognizer | None = None,
    ):
        self._session_manager = session_manager or global_session_manager
        self._intent_recognizer = intent_recognizer or global_intent_recognizer
        self._config = Config.get()
        self._logger = logging.getLogger("MasterWorkflow")

    async def execute(
        self, user_id: str, channel_id: str, message: str
    ) -> WorkflowResult:
        """执行工作流

        Args:
            user_id: 用户 ID
            channel_id: 渠道 ID
            message: 用户输入消息

        Returns:
            工作流执行结果
        """
        # 1. 预处理
        self._preprocess(message)

        # 2. 意图识别
        intent_result = await self._recognize_intent(message)

        # 3. 执行器
        messages = await self._execute_agent(
            user_id, channel_id, message, intent_result
        )

        # 4. 后处理
        final_reply = self._postprocess(messages)

        return WorkflowResult(
            agent_name=intent_result.agent_name,
            final_reply=final_reply,
            messages=messages
        )

    def _preprocess(self, message: str) -> None:
        """预处理：输入验证"""
        if not message or not message.strip():
            raise ValueError("Empty message")
        self._logger.debug(f"Preprocess: message length={len(message)}")

    async def _recognize_intent(self, message: str) -> IntentResult:
        """意图识别"""
        self._logger.info(f"Recognizing intent for: {message[:50]}...")
        result = await self._intent_recognizer.recognize(message)
        self._logger.info(
            f"Intent recognized: {result.agent_name} "
            f"(confidence={result.confidence}, type={result.match_type})"
        )
        return result

    async def _execute_agent(
        self,
        user_id: str,
        channel_id: str,
        message: str,
        intent_result: IntentResult,
    ) -> list[BaseMessage]:
        """执行 Agent"""
        # 获取会话
        session = await self._session_manager.get_or_create_session(
            user_id, channel_id
        )

        # 获取执行器类并实例化
        executor_class = agent_registry.get_executor(intent_result.agent_name)
        executor: BaseExecutor = executor_class(
            session=session,
            user_message=message,
            session_manager=self._session_manager
        )

        # 执行
        self._logger.info(f"Executing agent: {intent_result.agent_name}")
        messages = await executor.run()

        # 保存会话
        final_reply = messages[-1].content if messages else ""
        await self._session_manager.add_turn(
            session=session,
            agent_name=intent_result.agent_name,
            user_message=message,
            messages=messages,
            final_reply=final_reply
        )

        return messages

    def _postprocess(self, messages: list[BaseMessage]) -> str:
        """后处理：获取最终回复"""
        if not messages:
            return ""

        # 取最后一条 AI 消息
        final_message = messages[-1]
        if isinstance(final_message, AIMessage):
            return final_message.content
        return str(final_message.content)


# 全局工作流实例
master_workflow = MasterWorkflow()
