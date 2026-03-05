"""LangGraph 编排器 - 多代理协调。"""

from typing import Optional, Callable
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import OrchestratorState
from ..registry.agent_registry import get_registry, AgentSpec
from ..schemas.intent import IntentResult, IntentConfig


class Orchestrator:
    """
    基于 LangGraph 的多代理协调编排器。

    流程:
        analyze_intent → route_to_agent → execute_agent → fallback
    """

    def __init__(self, intent_config: Optional[IntentConfig] = None):
        """
        初始化编排器。

        Args:
            intent_config: 意图识别配置
        """
        self.intent_config = intent_config or IntentConfig()
        self.registry = get_registry()
        self._graph = self._build_graph()

    def _analyze_intent(self, state: OrchestratorState) -> OrchestratorState:
        """
        分析用户输入以确定意图。

        初始使用基于关键词的匹配。
        """
        input_text = state.get("input_text", "").lower()

        # 关键词匹配
        best_intent = self.intent_config.default_intent
        best_confidence = 0.5
        reason = "默认回退意图"

        for intent, keywords in self.intent_config.keywords.items():
            if not keywords:
                continue

            match_count = sum(1 for kw in keywords if kw.lower() in input_text)
            if match_count > 0:
                confidence = min(0.9, 0.5 + (match_count * 0.1))
                if confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
                    reason = f"匹配的关键词：{[kw for kw in keywords if kw.lower() in input_text]}"

        # 对规划意图的特殊处理
        if any(kw in input_text for kw in ["规划", "plan", "计划", "分解"]):
            best_intent = "planning"
            best_confidence = 0.85
            reason = "检测到规划相关关键词"

        # 显式构建新状态以避免重复键问题
        return OrchestratorState(
            user_id=state.get("user_id", ""),
            channel=state.get("channel", ""),
            session_id=state.get("session_id", ""),
            input_text=state.get("input_text", ""),
            intent=best_intent,
            confidence=best_confidence,
            reason=reason,
            target_agent=state.get("target_agent"),
            agent_params=state.get("agent_params", {}),
            messages=state.get("messages", []),
            output_text=state.get("output_text", ""),
            error=state.get("error")
        )

    def _route_to_agent(self, state: OrchestratorState) -> OrchestratorState:
        """根据意图路由到相应的代理。"""
        intent = state.get("intent", "general_qa")

        # 查找此意图的代理
        agent_spec = self.registry.find_agent_by_intent(intent)

        if agent_spec is None:
            # 回退到 general_qa 代理
            agent_spec = self.registry.find_agent_by_intent("general_qa")

        if agent_spec is None:
            new_state = dict(state)
            new_state["error"] = f"未找到意图对应的代理：{intent}"
            return OrchestratorState(**new_state)

        # 显式构建新状态以避免重复键问题
        return OrchestratorState(
            user_id=state.get("user_id", ""),
            channel=state.get("channel", ""),
            session_id=state.get("session_id", ""),
            input_text=state.get("input_text", ""),
            intent=state.get("intent", ""),
            confidence=state.get("confidence", 0.0),
            reason=state.get("reason", ""),
            target_agent=agent_spec.name,
            agent_params={
                "intent": intent,
                "input_text": state.get("input_text", ""),
                "messages": state.get("messages", [])
            },
            messages=state.get("messages", []),
            output_text=state.get("output_text", ""),
            error=state.get("error")
        )

    def _execute_agent(self, state: OrchestratorState) -> OrchestratorState:
        """执行目标代理。"""
        target_agent = state.get("target_agent")

        if not target_agent:
            return OrchestratorState(
                **state,
                error="未指定目标代理"
            )

        agent_spec = self.registry.get_agent(target_agent)

        if not agent_spec:
            return OrchestratorState(
                **state,
                error=f"代理不存在：{target_agent}"
            )

        try:
            agent_params = state.get("agent_params", {})
            result = agent_spec.runner(agent_params)

            # 从结果中提取输出
            output_text = result.get("output_text", "")
            messages = result.get("messages", [])

            # 构建新状态，避免重复键
            new_state = dict(state)
            new_state["output_text"] = output_text
            if messages:
                new_state["messages"] = messages

            return OrchestratorState(**new_state)

        except Exception as e:
            new_state = dict(state)
            new_state["error"] = str(e)
            return OrchestratorState(**new_state)

    def _should_fallback(self, state: OrchestratorState) -> str:
        """确定是否应该触发回退。"""
        if state.get("error"):
            return "fallback"
        if state.get("intent") == "fallback":
            return "fallback"
        return "execute_agent"

    def _fallback(self, state: OrchestratorState) -> OrchestratorState:
        """错误的回退处理器。"""
        error = state.get("error", "发生未知错误")

        # 尝试使用 general_qa 代理作为回退
        general_agent = self.registry.find_agent_by_intent("general_qa")

        if general_agent:
            try:
                result = general_agent.runner({
                    "intent": "fallback",
                    "input_text": state.get("input_text", ""),
                    "error_context": error
                })
                new_state = dict(state)
                new_state["output_text"] = result.get("output_text", f"回退响应：{error}")
                new_state["error"] = None
                return OrchestratorState(**new_state)
            except Exception as e:
                pass

        new_state = dict(state)
        new_state["output_text"] = f"很抱歉，我遇到了一个错误：{error}"
        new_state["error"] = error
        return OrchestratorState(**new_state)

    def _should_continue(self, state: OrchestratorState) -> str:
        """确定意图分析后的下一步。"""
        if state.get("error"):
            return "fallback"
        if state.get("target_agent"):
            return "execute_agent"
        return "fallback"

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流。"""
        builder = StateGraph(OrchestratorState)

        # 添加节点
        builder.add_node("analyze_intent", self._analyze_intent)
        builder.add_node("route_to_agent", self._route_to_agent)
        builder.add_node("execute_agent", self._execute_agent)
        builder.add_node("fallback", self._fallback)

        # 设置入口点
        builder.set_entry_point("analyze_intent")

        # 在意图分析后添加条件边
        builder.add_conditional_edges(
            source="analyze_intent",
            path=self._should_continue,
            path_map={
                "execute_agent": "route_to_agent",
                "fallback": "fallback"
            }
        )

        # 路由到执行者
        builder.add_edge("route_to_agent", "execute_agent")

        # 设置结束点
        builder.add_edge("execute_agent", END)
        builder.add_edge("fallback", END)

        # 使用内存保存器进行编译以实现持久化
        memory = MemorySaver()
        graph = builder.compile(checkpointer=memory)

        return graph

    async def arun(
        self,
        user_id: str,
        channel: str,
        input_text: str,
        session_id: Optional[str] = None,
        messages: Optional[list] = None
    ) -> dict:
        """
        异步运行编排器。

        Args:
            user_id: 用户标识符
            channel: 渠道标识符
            input_text: 用户输入文本
            session_id: 可选的会话 ID
            messages: 可选的对话历史

        Returns:
            包含 output_text 和元数据的结果字典
        """
        from ..session.session_manager import get_session_manager

        session_mgr = get_session_manager()
        thread_id = session_mgr.get_thread_id(user_id, channel, session_id)
        config = session_mgr.create_config(thread_id)

        initial_state = OrchestratorState(
            user_id=user_id,
            channel=channel,
            session_id=session_id or "default",
            input_text=input_text,
            messages=messages or []
        )

        result = await self._graph.ainvoke(initial_state, config=config)

        return {
            "output_text": result.get("output_text", ""),
            "intent": result.get("intent", ""),
            "confidence": result.get("confidence", 0.0),
            "reason": result.get("reason", ""),
            "target_agent": result.get("target_agent", ""),
            "error": result.get("error"),
            "thread_id": thread_id
        }

    def run(
        self,
        user_id: str,
        channel: str,
        input_text: str,
        session_id: Optional[str] = None,
        messages: Optional[list] = None
    ) -> dict:
        """
        同步运行编排器。

        Args:
            user_id: 用户标识符
            channel: 渠道标识符
            input_text: 用户输入文本
            session_id: 可选的会话 ID
            messages: 可选的对话历史

        Returns:
            包含 output_text 和元数据的结果字典
        """
        import asyncio
        return asyncio.run(
            self.arun(
                user_id=user_id,
                channel=channel,
                input_text=input_text,
                session_id=session_id,
                messages=messages
            )
        )


def create_orchestrator(intent_config: Optional[IntentConfig] = None) -> Orchestrator:
    """创建编排器的工厂函数。"""
    return Orchestrator(intent_config=intent_config)
