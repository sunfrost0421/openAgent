"""Agent 注册器"""

import logging
from typing import Callable, Dict, List, Optional, Type

from src.core.orchestration.models import AgentMetadata
from src.core.orchestration.executor import BaseExecutor


class AgentRegistry:
    """Agent 注册器

    使用装饰器注册 Agent，管理元数据和执行器类
    """

    def __init__(self):
        self._executors: Dict[str, Type[BaseExecutor]] = {}
        self._metadata: Dict[str, AgentMetadata] = {}
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

            # 保存元数据
            self._metadata[name] = AgentMetadata(
                name=name,
                description=description,
                keywords=keywords,
                command=command
            )

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

    def get_all_metadata(self) -> Dict[str, AgentMetadata]:
        """获取所有注册的 Agent 元数据

        Returns:
            Agent 名称到元数据的映射
        """
        return self._metadata.copy()


# 全局 Agent 注册器实例
agent_registry = AgentRegistry()
