"""Core 模块统一导出"""

# 工作流相关
from src.core.orchestration.master_workflow import MasterWorkflow, master_workflow
from src.core.orchestration.registry import AgentRegistry, agent_registry
from src.core.orchestration.intent import IntentRecognizer, intent_recognizer
from src.core.orchestration.executor import BaseExecutor

# 会话管理相关
from src.core.session.models import Session, Turn
from src.core.session.store.base import BaseSessionStore
from src.core.session.store import MemorySessionStore, memory_store
from src.core.session.manager import SessionManager, session_manager

# 类型
from src.core.orchestration.models import AgentMetadata, IntentResult, IntentMatch

# ============================================================================
# 向后兼容导出（带 DeprecationWarning）
# ============================================================================
import warnings

# 旧的 orchestration 模块导出
def __getattr__(name):
    """向后兼容：旧的导入路径"""
    deprecated_mappings = {
        # orchestration 模块
        "orchestration": "src.core.orchestration",
        "IntentRecognizer_old": "src.core.orchestration.intent",
        "intent_recognizer_old": "src.core.orchestration.intent",
        "BaseExecutor_old": "src.core.orchestration.executor",
        "agent_registry_old": "src.core.orchestration.registry",
        "master_workflow_old": "src.core.orchestration.master",
        # session 模块
        "session_store": "src.core.session.models",
        "memory_store_old": "src.core.session.store",
        "memory_session_store": "src.core.session.store",
        "session_manager_old": "src.core.session.manager",
    }

    if name in deprecated_mappings:
        warnings.warn(
            f"{name} is deprecated, use the new module structure instead",
            DeprecationWarning,
            stacklevel=2
        )
        # 返回适当的对象或抛出 AttributeError
        raise AttributeError(f"{name} is deprecated")

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 工作流相关
    "MasterWorkflow",
    "master_workflow",
    "AgentRegistry",
    "agent_registry",
    "IntentRecognizer",
    "intent_recognizer",
    "BaseExecutor",
    # 会话管理相关
    "Session",
    "Turn",
    "BaseSessionStore",
    "MemorySessionStore",
    "memory_store",
    "SessionManager",
    "session_manager",
    # 类型
    "AgentMetadata",
    "IntentResult",
    "IntentMatch",
]
