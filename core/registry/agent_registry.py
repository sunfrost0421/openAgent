"""代理注册表 - 基于装饰器的注册机制。"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional
import threading


@dataclass
class AgentSpec:
    """代理规范。"""
    name: str
    description: str
    intents: list[str]
    runner: Callable[[dict], dict]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """使用装饰器模式的全局代理注册表。"""

    _instance: Optional["AgentRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "AgentRegistry":
        """单例模式确保单一注册表实例。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._agents: Dict[str, AgentSpec] = {}
                    cls._instance._intent_map: Dict[str, str] = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置注册表（主要用于测试）。"""
        with cls._lock:
            cls._instance = None

    def register(
        self,
        name: str,
        description: str,
        intents: list[str],
        **metadata: Any
    ) -> Callable[[Callable], Callable]:
        """
        注册代理的装饰器。

        Args:
            name: 唯一代理标识符
            description: 人类可读的描述
            intents: 此代理处理的意图列表
            **metadata: 附加元数据

        Returns:
            装饰器函数
        """
        def decorator(runner: Callable[[dict], dict]) -> Callable[[dict], dict]:
            with self._lock:
                # 创建代理规范
                spec = AgentSpec(
                    name=name,
                    description=description,
                    intents=intents,
                    runner=runner,
                    metadata=metadata
                )

                # 注册代理
                self._agents[name] = spec

                # 映射意图到代理
                for intent in intents:
                    self._intent_map[intent.lower()] = name

            return runner

        return decorator

    def get_agent(self, name: str) -> Optional[AgentSpec]:
        """根据名称获取代理。"""
        with self._lock:
            return self._agents.get(name)

    def find_agent_by_intent(self, intent: str) -> Optional[AgentSpec]:
        """查找处理给定意图的代理。"""
        with self._lock:
            agent_name = self._intent_map.get(intent.lower())
            if agent_name:
                return self._agents.get(agent_name)
            return None

    def list_agents(self) -> list[AgentSpec]:
        """列出所有已注册的代理。"""
        with self._lock:
            return list(self._agents.values())

    def list_intents(self) -> list[str]:
        """列出所有已注册的意图。"""
        with self._lock:
            return list(self._intent_map.keys())

    def has_agent(self, name: str) -> bool:
        """检查代理是否已注册。"""
        with self._lock:
            return name in self._agents


# 全局注册表实例
registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """获取全局注册表实例。"""
    return registry
