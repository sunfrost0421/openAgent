#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上下文压缩机制演示脚本

展示 LangChain SummarizationMiddleware 和 Session 级压缩的工作过程
"""

import asyncio
import sys

# 设置标准输出编码为 utf-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.core.session.models import Session, Turn
from src.core.session.manager import SessionManager
from src.core.session.store import MemorySessionStore
from src.config import Config
from langchain_core.messages.utils import count_tokens_approximately


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def print_message(msg, prefix="  "):
    """打印单条消息"""
    msg_type = type(msg).__name__
    content = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
    print(f"{prefix}[{msg_type}] {content}")


async def demo_session_level_compression():
    """演示 Session 级压缩（基于轮次）"""
    print_separator("演示 1: Session 级压缩（基于轮次）")

    config = Config.get()
    print(f"配置：CONTEXT_KEEP_TURNS = {config.CONTEXT_KEEP_TURNS}")
    print(f"      CONTEXT_MAX_TOKENS = {config.CONTEXT_MAX_TOKENS}")

    # 创建会话管理器
    store = MemorySessionStore()
    session_manager = SessionManager(store=store)
    session = await session_manager.get_or_create_session("demo_user", "demo_channel")

    # 模拟 6 轮对话
    num_turns = 6
    print(f"\n模拟 {num_turns} 轮对话...\n")

    for i in range(num_turns):
        messages = [
            HumanMessage(content=f"这是第 {i+1} 轮的用户问题，问题内容是：{'ABC' * 10}"),
            AIMessage(content=f"这是第 {i+1} 轮的 AI 回复，回复内容是：{'XYZ' * 10}")
        ]

        await session_manager.add_turn(
            session=session,
            agent_name="code_agent",
            user_message=f"Question {i+1}",
            messages=messages,
            final_reply=f"Answer {i+1}"
        )

        # 打印当前状态
        compressed_count = sum(1 for t in session.turns if t.is_compressed)
        print(f"第 {i+1} 轮后:")
        print(f"  - 总轮次：{len(session.turns)}")
        print(f"  - 已压缩：{compressed_count}")
        print(f"  - 未压缩：{len(session.turns) - compressed_count}")

        # 打印每个轮次的状态
        for j, turn in enumerate(session.turns):
            status = "已压缩" if turn.is_compressed else "未压缩"
            msg_count = len(turn.messages)
            print(f"    Turn {j+1}: [{status}] 消息数={msg_count}")
        print()

    # 获取上下文消息
    print_separator("获取上下文消息")
    context_messages = session.get_context_messages(
        keep_turns=config.CONTEXT_KEEP_TURNS,
        max_tokens=config.CONTEXT_MAX_TOKENS
    )

    print(f"上下文消息总数：{len(context_messages)}")
    print("\n消息详情:")
    for i, msg in enumerate(context_messages):
        print_message(msg, f"  [{i+1}] ")

    # token 统计
    total_tokens = count_tokens_approximately(context_messages)
    print(f"\n总 token 数：{total_tokens}")


async def demo_agent_level_compression():
    """演示 Agent 级压缩（SummarizationMiddleware）"""
    print_separator("演示 2: Agent 级压缩（SummarizationMiddleware）")

    from langchain.agents import create_agent
    from langchain.agents.middleware import SummarizationMiddleware
    from src.infra.llm import create_llm

    config = Config.get()

    print(f"配置：CONTEXT_MAX_TOKENS = {config.CONTEXT_MAX_TOKENS}")
    print(f"      CONTEXT_KEEP_RECENT_MESSAGES = {config.CONTEXT_KEEP_RECENT_MESSAGES}")

    # 创建带压缩中间件的 agent
    llm = create_llm()

    print("\n创建 SummarizationMiddleware...")
    middleware = SummarizationMiddleware(
        model=llm,
        trigger=("tokens", config.CONTEXT_MAX_TOKENS),
        keep=("messages", config.CONTEXT_KEEP_RECENT_MESSAGES)
    )

    print(f"  - 触发条件：tokens > {config.CONTEXT_MAX_TOKENS}")
    print(f"  - 保留消息：{config.CONTEXT_KEEP_RECENT_MESSAGES} 条")

    # 模拟大量消息
    print(f"\n模拟大量消息输入...")

    # 创建 20 条消息（模拟多轮工具调用）
    messages = []
    for i in range(20):
        messages.append(HumanMessage(content=f"工具调用请求 {i+1}: 读取文件 path/to/file_{i}.py"))
        messages.append(AIMessage(content=f"工具调用响应 {i+1}: 文件内容已读取"))

    initial_tokens = count_tokens_approximately(messages)
    print(f"初始消息数：{len(messages)}")
    print(f"初始 token 数：{initial_tokens}")

    # 说明
    print(f"\n说明：SummarizationMiddleware 会在 agent.ainvoke() 内部自动触发压缩")
    print(f"当 token 数超过 {config.CONTEXT_MAX_TOKENS} 时，自动调用 LLM 生成摘要")
    print(f"并保留最近 {config.CONTEXT_KEEP_RECENT_MESSAGES} 条原始消息")

    # 注意：这里不实际执行 ainvoke，因为需要真实的工具和环境
    # 只展示配置和原理
    print("\n[演示完成] 实际压缩在 agent.ainvoke() 内部自动执行")


async def demo_token_threshold():
    """演示 token 阈值触发"""
    print_separator("演示 3: Token 阈值触发机制")

    config = Config.get()

    # 创建不同大小的消息列表
    test_cases = [
        ("小消息", 2, "Hi"),
        ("中等消息", 10, "这是一个正常的对话内容"),
        ("大消息", 50, "这是一段很长的消息" * 10),
    ]

    print(f"Token 阈值：{config.CONTEXT_MAX_TOKENS}\n")

    for name, count, content in test_cases:
        messages = [
            HumanMessage(content=content),
            AIMessage(content=content)
        ] * count

        tokens = count_tokens_approximately(messages)
        would_compress = tokens > config.CONTEXT_MAX_TOKENS

        status_str = "[!] 会触发压缩" if would_compress else "[OK] 无需压缩"
        print(f"{name}:")
        print(f"  消息数：{len(messages)}")
        print(f"  Token 数：{tokens}")
        print(f"  状态：{status_str}")
        print()


async def demo_full_workflow():
    """演示完整工作流程"""
    print_separator("演示 4: 完整工作流程")

    print("""
工作流程图:

用户请求
   │
   ▼
┌─────────────────────────────────┐
│  MasterWorkflow.execute()       │
└─────────────────────────────────┘
   │
   ├─→ 1. 获取会话 (SessionManager)
   │      └─→ get_or_create_session()
   │
   ├─→ 2. 意图识别 (IntentRecognizer)
   │      └─→ recognize(message)
   │
   ├─→ 3. 执行 Agent
   │      ├─→ CodeAgent.__init__()
   │      │    └─→ 配置 SummarizationMiddleware
   │      │
   │      ├─→ CodeAgent.run()
   │      │    ├─→ get_context_messages()
   │      │    │    └─→ Session 级压缩
   │      │    │
   │      │    └─→ agent.ainvoke()
   │      │         └─→ SummarizationMiddleware
   │      │              └─→ Agent 级压缩
   │      │
   │      └─→ 返回 messages
   │
   └─→ 4. 保存会话 (add_turn)
           └─→ 压缩旧轮次

    """)

    # 实际执行一个简化流程
    print("\n执行简化流程演示...\n")

    store = MemorySessionStore()
    session_manager = SessionManager(store=store)
    session = await session_manager.get_or_create_session("workflow_demo", "channel_1")

    # 第 1 轮
    print("第 1 轮对话:")
    messages1 = [
        HumanMessage(content="帮我写一个 Python 函数"),
        AIMessage(content="好的，请问需要什么功能的函数？")
    ]
    await session_manager.add_turn(
        session=session,
        agent_name="code_agent",
        user_message="帮我写一个 Python 函数",
        messages=messages1,
        final_reply="好的，请问需要什么功能的函数？"
    )
    print(f"  轮次：{len(session.turns)}, 已压缩：{sum(1 for t in session.turns if t.is_compressed)}")

    # 第 2 轮
    print("第 2 轮对话:")
    messages2 = [
        HumanMessage(content="计算两个数的和"),
        AIMessage(content="def add(a, b): return a + b")
    ]
    await session_manager.add_turn(
        session=session,
        agent_name="code_agent",
        user_message="计算两个数的和",
        messages=messages2,
        final_reply="def add(a, b): return a + b"
    )
    print(f"  轮次：{len(session.turns)}, 已压缩：{sum(1 for t in session.turns if t.is_compressed)}")

    # 第 3 轮
    print("第 3 轮对话:")
    messages3 = [
        HumanMessage(content="添加类型注解"),
        AIMessage(content="def add(a: int, b: int) -> int: return a + b")
    ]
    await session_manager.add_turn(
        session=session,
        agent_name="code_agent",
        user_message="添加类型注解",
        messages=messages3,
        final_reply="def add(a: int, b: int) -> int: return a + b"
    )
    print(f"  轮次：{len(session.turns)}, 已压缩：{sum(1 for t in session.turns if t.is_compressed)}")

    # 第 4 轮 - 触发压缩
    print("第 4 轮对话 (触发压缩):")
    messages4 = [
        HumanMessage(content="再添加文档字符串"),
        AIMessage(content='def add(a: int, b: int) -> int:\n    """计算两数之和"""')
    ]
    await session_manager.add_turn(
        session=session,
        agent_name="code_agent",
        user_message="再添加文档字符串",
        messages=messages4,
        final_reply='def add(a: int, b: int) -> int:\n    """计算两数之和"""'
    )
    compressed_count = sum(1 for t in session.turns if t.is_compressed)
    print(f"  轮次：{len(session.turns)}, 已压缩：{compressed_count}")

    print("\n最终状态:")
    for i, turn in enumerate(session.turns):
        status = "已压缩" if turn.is_compressed else "未压缩"
        print(f"  Turn {i+1}: [{status}] final_reply='{turn.final_reply[:30]}...'")


async def main():
    """主函数"""
    print("""
+-----------------------------------------------------------+
|                                                           |
|        上下文压缩机制演示 (Context Compression Demo)      |
|                                                           |
|  双层压缩策略：                                           |
|  1. Agent 级：SummarizationMiddleware (基于 token)        |
|  2. Session 级：轮次压缩 (基于轮次数量)                   |
|                                                           |
+-----------------------------------------------------------+
    """)

    await demo_session_level_compression()
    await demo_agent_level_compression()
    await demo_token_threshold()
    await demo_full_workflow()

    print_separator("演示完成")
    print("\n关键要点:")
    print("  1. Session 级压缩在每次 add_turn() 后自动触发")
    print("  2. Agent 级压缩在 agent.ainvoke() 内部自动触发")
    print("  3. 两层压缩独立工作，互不干扰")
    print("  4. 压缩目标是控制 token 数量，防止超出模型上下文窗口")
    print()


if __name__ == "__main__":
    asyncio.run(main())
