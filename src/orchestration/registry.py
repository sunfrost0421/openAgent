"""Agent 注册器"""

import logging
from typing import Callable, Dict, List, Optional, Type

from src.core.intent import AgentMetadata
from src.core import intent
from src.orchestration.base_executor import BaseExecutor


class AgentRegistry:
    """Agent 注册器

    使用装饰器注册 Agent，管理元数据和执行器类
    """

    def __init__(self):
        self._executors: Dict[str, Type[BaseExecutor]] = {}
        self._logger = logging.getLogger("AgentRegistry")

    def register(
        self,
        name: str,
        description: str,
        keywords: List[str],
        command: Optional[str] = None,
    ) -> Callable[[Type[BaseExecutor]], Type[BaseExecutor]]:
        """注册 Agent 装饰器

        Args:
            name: Agent 名称
            description: Agent 描述
            keywords: 关键词列表
            command: 快捷命令（如 @code）

        Returns:
            装饰器函数

        Example:
            @agent_registry.register(
                name="code_agent",
                description="处理代码相关请求",
                keywords=["代码", "编程", "function"],
                command="@code"
            )
            class CodeAgent(BaseExecutor):
                async def run(self):
                    ...
        """
        def decorator(cls: Type[BaseExecutor]) -> Type[BaseExecutor]:
            # 注册执行器类
            self._executors[name] = cls

            # 注册到意图识别器
            metadata = AgentMetadata(
                name=name,
                description=description,
                keywords=keywords,
                command=command
            )
            intent.intent_recognizer.register_agent(metadata)

            self._logger.info(f"Registered agent: {name}")
            return cls

        return decorator

    def get_executor(self, agent_name: str) -> Type[BaseExecutor]:
        """获取 Agent 执行器类"""
        if agent_name not in self._executors:
            raise ValueError(f"Agent not found: {agent_name}")
        return self._executors[agent_name]

    def get_all_executors(self) -> Dict[str, Type[BaseExecutor]]:
        """获取所有执行器类"""
        return self._executors.copy()


# 全局 Agent 注册器实例
agent_registry = AgentRegistry()
