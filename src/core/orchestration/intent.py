"""意图识别模块"""

import logging
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from src.infra.llm import create_intent_llm
from src.config import Config
from src.core.orchestration.models import AgentMetadata, IntentMatch, IntentResult


class IntentRecognizer:
    """意图识别器

    三层识别策略：
    1. 快捷命令匹配：优先匹配 @ 开头的命令
    2. 关键词匹配：基于注册器中定义的关键词
    3. LLM 置信度评估：LLM 对匹配结果做置信度评估
    """

    def __init__(self):
        self._agents: dict[str, AgentMetadata] = {}
        self._llm = create_intent_llm()
        self._parser = PydanticOutputParser(pydantic_object=IntentMatch)
        self._config = Config.get()
        self._logger = logging.getLogger("IntentRecognizer")

    def register_agent(self, metadata: AgentMetadata) -> None:
        """注册 Agent"""
        self._agents[metadata.name] = metadata
        self._logger.debug(f"Registered agent: {metadata.name}")

    async def recognize(self, message: str) -> IntentResult:
        """识别用户意图

        Args:
            message: 用户输入消息

        Returns:
            意图识别结果
        """
        # 1. 快捷命令匹配
        command_result = self._match_command(message)
        if command_result:
            return command_result

        # 2. 关键词匹配
        keyword_result = self._match_keywords(message)
        if keyword_result:
            # 3. LLM 置信度评估
            llm_result = await self._llm_evaluate(keyword_result, message)
            return llm_result

        # 默认进入 default_agent
        return IntentResult(
            agent_name="default_agent",
            confidence=0.0,
            reason="No matching agent found, using default",
            match_type="default"
        )

    def _match_command(self, message: str) -> Optional[IntentResult]:
        """快捷命令匹配

        匹配 @command 格式的命令
        """
        match = re.match(r"^@(\w+)\s*", message)
        if not match:
            return None

        command = match.group(1)

        for agent in self._agents.values():
            if agent.command and agent.command.strip("@") == command:
                self._logger.info(f"Command match: {command} -> {agent.name}")
                return IntentResult(
                    agent_name=agent.name,
                    confidence=1.0,  # 命令匹配 100% 准确
                    reason=f"Matched command: {agent.command}",
                    match_type="command"
                )

        return None

    def _match_keywords(self, message: str) -> Optional[IntentResult]:
        """关键词匹配

        匹配至少 1 个关键词
        """
        message_lower = message.lower()
        best_match = None
        best_count = 0

        for agent in self._agents.values():
            match_count = sum(
                1 for kw in agent.keywords if kw.lower() in message_lower
            )
            if match_count > best_count:
                best_count = match_count
                best_match = agent

        if best_count > 0:
            confidence = min(0.8, 0.3 + best_count * 0.1)  # 1 个词 0.4, 2 个 0.5, 最多 0.8
            self._logger.info(
                f"Keyword match: {best_match.name} with {best_count} keywords"
            )
            return IntentResult(
                agent_name=best_match.name,
                confidence=confidence,
                reason=f"Matched {best_count} keywords: {best_match.keywords}",
                match_type="keyword"
            )

        return None

    async def _llm_evaluate(
        self, intent_result: IntentResult, message: str
    ) -> IntentResult:
        """LLM 置信度评估

        使用 LLM 评估关键词匹配的结果是否准确
        """
        agent = self._agents.get(intent_result.agent_name)
        if not agent:
            return intent_result

        prompt = f"""
You are an intent classifier. Evaluate whether the user's message should be handled by the specified agent.

User message: "{message}"

Agent info:
- Name: {agent.name}
- Description: {agent.description}
- Keywords: {agent.keywords}

Current match reason: {intent_result.reason}

Evaluate if this is the correct agent for this message. Consider:
1. Does the message semantically match the agent's purpose?
2. Are the matched keywords actually relevant to the message's intent?

Respond with a confidence score (0.0-1.0) and brief reason.
"""

        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            # 简单解析，假设 LLM 返回一个 0-1 的数字
            content = response.content.strip()
            # 尝试提取置信度
            confidence = intent_result.confidence  # 默认保持原置信度

            # 如果 LLM 明确表达了低置信度，调整
            if any(word in content.lower() for word in ["not relevant", "wrong", "incorrect"]):
                confidence = 0.3
            elif any(word in content.lower() for word in ["correct", "appropriate", "suitable"]):
                confidence = max(confidence, 0.7)

            self._logger.debug(f"LLM evaluation confidence: {confidence}")

            return IntentResult(
                agent_name=intent_result.agent_name,
                confidence=confidence,
                reason=f"{intent_result.reason}. LLM: {content[:100]}",
                match_type="llm"
            )
        except Exception as e:
            self._logger.error(f"LLM evaluation failed: {e}")
            return intent_result

    def get_all_agents(self) -> List[AgentMetadata]:
        """获取所有注册的 Agent"""
        return list(self._agents.values())


# 全局意图识别器实例
intent_recognizer = IntentRecognizer()
