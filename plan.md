一、总体架构
1）核心目标映射
意图识别 + 路由分发（LangGraph）

用你给的节点模型：

analyze_intent
route_to_agent
execute_agent
fallback
注册装饰器机制

通过 @register_agent(...) 快速接入新的子 Agent，不改主流程。

会话管理隔离

维度：user_id + channel + session_id

组合成 thread_id，用于 LangGraph checkpointer 和记忆隔离。

多轮对话

使用 LangGraph 持久化（MemorySaver / Redis/Postgres checkpointer）+ 每次传同一个 thread_id。

二、目录建议
<BASH>
agent_framework/
├── app.py
├── graph/
│   ├── state.py
│   └── orchestrator.py
├── registry/
│   └── agent_registry.py
├── agents/
│   ├── lc_agent.py
│   └── deep_agent.py
├── session/
│   └── session_manager.py
└── schemas/
    └── intent.py
三、关键数据结构
<PYTHON>
# graph/state.py
from typing import TypedDict, Optional, Any, Dict, List
from langchain_core.messages import BaseMessage
class OrchestratorState(TypedDict, total=False):
    user_id: str
    channel: str
    session_id: str
    input_text: str
    # 意图识别结果
    intent: Optional[str]
    confidence: float
    reason: str
    # 路由
    target_agent: Optional[str]
    agent_params: Dict[str, Any]
    # 对话与输出
    messages: List[BaseMessage]
    output_text: str
    error: Optional[str]
四、注册中心 + 装饰器（重点）
<PYTHON>
# registry/agent_registry.py
from typing import Callable, Dict, Any
from dataclasses import dataclass
@dataclass
class AgentSpec:
    name: str
    description: str
    intents: list[str]
    runner: Callable[[dict], dict]  # 输入state，返回 {"output_text": "..."} 等
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentSpec] = {}
        self._intent_to_agent: Dict[str, str] = {}
    def register(self, name: str, description: str, intents: list[str]):
        def decorator(func: Callable[[dict], dict]):
            if name in self._agents:
                raise ValueError(f"Agent '{name}' already registered")
            spec = AgentSpec(name=name, description=description, intents=intents, runner=func)
            self._agents[name] = spec
            for i in intents:
                self._intent_to_agent[i] = name
            return func
        return decorator
    def get_agent(self, name: str) -> AgentSpec | None:
        return self._agents.get(name)
    def find_agent_by_intent(self, intent: str) -> AgentSpec | None:
        n = self._intent_to_agent.get(intent)
        return self._agents.get(n) if n else None
    def list_agents(self):
        return list(self._agents.values())
agent_registry = AgentRegistry()
register_agent = agent_registry.register
五、两个初始子 Agent
这里用统一 runner 接口：输入 state，输出 dict。

1）LangChain create_agent 子 Agent
<PYTHON>
# agents/lc_agent.py
from registry.agent_registry import register_agent
from langchain.agents import create_agent  # LangChain 1.0 风格（示意）
# 具体模型导入按你实际供应商调整
@register_agent(
    name="lc_general_agent",
    description="通用问答/工具调用Agent（LangChain create_agent）",
    intents=["general_qa", "knowledge_search"]
)
def run_lc_agent(state: dict) -> dict:
    user_text = state["input_text"]
    # 示例：伪代码，按你模型替换
    agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[],
        system_prompt="你是一个专业助手。"
    )
    resp = agent.invoke({"messages": [{"role": "user", "content": user_text}]})
    # 兼容提取
    output = resp.get("output_text") or str(resp)
    return {"output_text": output}
2）DeepAgent create_deep_agent 子 Agent
<PYTHON>
# agents/deep_agent.py
from registry.agent_registry import register_agent
# from deepagent import create_deep_agent  # 按实际包路径
@register_agent(
    name="deep_reasoning_agent",
    description="复杂推理与任务分解Agent（DeepAgent）",
    intents=["complex_reasoning", "planning"]
)
def run_deep_agent(state: dict) -> dict:
    user_text = state["input_text"]
    # 示例伪代码
    # agent = create_deep_agent(
    #     model="anthropic:claude-3-7-sonnet",
    #     tools=[],
    #     config={"max_depth": 4}
    # )
    # resp = agent.run(user_text)
    resp = f"[DeepAgent mock] 已处理复杂任务: {user_text}"
    return {"output_text": resp}
六、会话管理（user_id + channel + session_id）
<PYTHON>
# session/session_manager.py
class SessionManager:
    @staticmethod
    def build_thread_id(user_id: str, channel: str, session_id: str) -> str:
        return f"{user_id}::{channel}::{session_id}"
LangGraph 调用时：

<PYTHON>
config = {"configurable": {"thread_id": thread_id}}
graph.invoke(state_input, config=config)
只要同一个三元组，历史上下文就会隔离且可持续多轮。

七、LangGraph Orchestrator 实现
<PYTHON>
# graph/orchestrator.py
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import OrchestratorState
from registry.agent_registry import agent_registry
class AgentOrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.graph = self._build_graph()
    def _build_graph(self):
        graph = StateGraph(OrchestratorState)
        graph.add_node("analyze_intent", self._analyze_intent)
        graph.add_node("route_to_agent", self._route_to_agent)
        graph.add_node("execute_agent", self._execute_agent)
        graph.add_node("fallback", self._fallback)
        graph.add_edge(START, "analyze_intent")
        graph.add_conditional_edges(
            "analyze_intent",
            self._check_intent,
            {
                "identified": "route_to_agent",
                "unclear": "fallback",
            },
        )
        graph.add_edge("route_to_agent", "execute_agent")
        graph.add_edge("execute_agent", END)
        graph.add_edge("fallback", END)
        # PoC用MemorySaver，生产建议Redis/Postgres checkpointer
        return graph.compile(checkpointer=MemorySaver())
    def _analyze_intent(self, state: OrchestratorState):
        text = state["input_text"]
        # 这里建议用结构化输出（Pydantic）做意图分类
        # 示例简化：关键词规则 + LLM兜底
        intent = "general_qa"
        confidence = 0.8
        reason = "默认意图"
        if any(k in text.lower() for k in ["规划", "分解", "复杂", "plan"]):
            intent, confidence, reason = "planning", 0.9, "命中复杂任务关键词"
        return {"intent": intent, "confidence": confidence, "reason": reason}
    def _check_intent(self, state: OrchestratorState) -> Literal["identified", "unclear"]:
        if state.get("intent") and state.get("confidence", 0) >= 0.6:
            return "identified"
        return "unclear"
    def _route_to_agent(self, state: OrchestratorState):
        spec = agent_registry.find_agent_by_intent(state["intent"])
        if not spec:
            return {"target_agent": None, "error": f"no agent for intent={state['intent']}"}
        return {"target_agent": spec.name}
    def _execute_agent(self, state: OrchestratorState):
        target = state.get("target_agent")
        spec = agent_registry.get_agent(target) if target else None
        if not spec:
            return {"output_text": "没有可用的处理Agent，已转人工。", "error": "agent_not_found"}
        try:
            result = spec.runner(state)
            return {"output_text": result.get("output_text", ""), "error": None}
        except Exception as e:
            return {"output_text": "处理失败，请稍后重试。", "error": str(e)}
    def _fallback(self, state: OrchestratorState):
        return {"output_text": "我暂时无法准确识别你的意图，请再具体描述一下。"}
八、主入口调用（多轮）
<PYTHON>
# app.py
from graph.orchestrator import AgentOrchestrator
from session.session_manager import SessionManager
# 确保导入以触发装饰器注册
import agents.lc_agent
import agents.deep_agent
def chat(orchestrator: AgentOrchestrator, user_id: str, channel: str, session_id: str, text: str):
    thread_id = SessionManager.build_thread_id(user_id, channel, session_id)
    state_in = {
        "user_id": user_id,
        "channel": channel,
        "session_id": session_id,
        "input_text": text,
}
    config = {"configurable": {"thread_id": thread_id}}
    out = orchestrator.graph.invoke(state_in, config=config)
    return out.get("output_text")
if __name__ == "__main__":
    orchestrator = AgentOrchestrator(llm=None)  # 注入真实llm
    print(chat(orchestrator, "u1", "wechat", "s001", "帮我回答一下什么是RAG"))
    print(chat(orchestrator, "u1", "wechat", "s001", "再详细一点，并给我一个实施步骤"))
    print(chat(orchestrator, "u1", "wechat", "s001", "帮我规划一个复杂的落地方案"))