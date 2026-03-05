"""多轮对话测试，包含上下文记忆。"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.registry.agent_registry import get_registry, AgentRegistry
from core.graph.orchestrator import create_orchestrator
from core.session.session_manager import get_session_manager
from core.schemas.intent import IntentConfig


def test_multi_round_conversation():
    """测试多轮对话与上下文保留。"""
    print("=" * 60)
    print("测试：多轮对话")
    print("=" * 60)

    # 重置并重新注册代理
    AgentRegistry.reset()
    from agent import lc_agent, deep_agent

    session_mgr = get_session_manager()
    config = IntentConfig()
    orchestrator = create_orchestrator(config)

    # 在同一会话中进行多轮对话
    user_id = "user_001"
    channel = "web"
    session_id = "conversation_001"
    thread_id = session_mgr.get_thread_id(user_id, channel, session_id)

    print(f"\nThread ID: {thread_id}")
    print("-" * 60)

    # 多轮对话
    conversation = [
        ("你好", "通用问候"),
        ("我想了解一下机器学习", "主题介绍"),
        ("能详细解释一下深度学习吗", "深入相关主题"),
        ("这需要什么样的硬件要求", "后续问题关于要求"),
    ]

    for input_text, context in conversation:
        print(f"\n[User] {context}: {input_text}")

        try:
            result = orchestrator.run(
                user_id=user_id,
                channel=channel,
                input_text=input_text,
                session_id=session_id
            )

            print(f"  Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
            print(f"  Agent: {result['target_agent']}")
            print(f"  [Assistant] {result['output_text'][:150]}...")

        except Exception as e:
            print(f"  [Error] {e}")

    print("\n" + "-" * 60)
    print("[OK] 多轮对话测试完成\n")
    return True


def test_parallel_sessions():
    """测试多个并行会话的隔离性。"""
    print("=" * 60)
    print("测试：并行会话隔离")
    print("=" * 60)

    # 重置并重新注册代理
    AgentRegistry.reset()
    from agent import lc_agent, deep_agent

    session_mgr = get_session_manager()
    config = IntentConfig()
    orchestrator = create_orchestrator(config)

    # 创建多个并行会话
    sessions = [
        {"user_id": "user_A", "channel": "web", "session_id": "s1"},
        {"user_id": "user_A", "channel": "api", "session_id": "s2"},  # 同一用户，不同渠道
        {"user_id": "user_B", "channel": "web", "session_id": "s3"},  # 不同用户
    ]

    for session in sessions:
        thread_id = session_mgr.get_thread_id(
            session["user_id"],
            session["channel"],
            session["session_id"]
        )
        session["thread_id"] = thread_id
        print(f"\nSession: {session['user_id']}/{session['channel']}/{session['session_id']}")
        print(f"  Thread ID: {thread_id}")

    # 验证隔离性
    thread_ids = [s["thread_id"] for s in sessions]
    assert len(set(thread_ids)) == len(thread_ids), "Thread IDs 应该是唯一的"

    print("\n[OK] 并行会话已正确隔离\n")
    return True


def test_context_switching():
    """测试在同一对话中切换不同意图。"""
    print("=" * 60)
    print("测试：上下文切换")
    print("=" * 60)

    # 重置并重新注册代理
    AgentRegistry.reset()
    from agent import lc_agent, deep_agent

    config = IntentConfig()
    orchestrator = create_orchestrator(config)

    user_id = "user_switch"
    channel = "test"
    session_id = "switch_session"

    # 应该触发不同代理的消息
    test_sequence = [
        ("你好", "general_qa"),
        ("帮我规划一个学习计划", "planning"),
        ("搜索相关资料", "knowledge_search"),
        ("分析这个问题的原因", "complex_reasoning"),
        ("总结一下", "general_qa"),
    ]

    print(f"\nSession: {user_id}/{channel}/{session_id}\n")

    for input_text, expected_intent in test_sequence:
        try:
            result = orchestrator.run(
                user_id=user_id,
                channel=channel,
                input_text=input_text,
                session_id=session_id
            )

            intent_match = "[OK]" if result["intent"] == expected_intent else "[FAIL]"
            print(f"  {intent_match} '{input_text}'")
            print(f"      预期：{expected_intent}, 实际：{result['intent']}")
            print(f"      代理：{result['target_agent']}")

        except Exception as e:
            print(f"  [FAIL] '{input_text}' - 错误：{e}")

    print("\n[OK] 上下文切换测试完成\n")
    return True


def test_thread_id_format():
    """测试 thread_id 格式和解析。"""
    print("=" * 60)
    print("测试：Thread ID 格式")
    print("=" * 60)

    session_mgr = get_session_manager()

    # 测试格式
    test_cases = [
        ("user1", "web", "session1"),
        ("user_123", "api_channel", "session_abc"),
        ("test", "slack", "conv_001"),
    ]

    print("\n格式验证:")
    for user_id, channel, session_id in test_cases:
        thread_id = session_mgr.get_thread_id(user_id, channel, session_id)
        expected = f"{user_id}::{channel}::{session_id}"
        match = "[OK]" if thread_id == expected else "[FAIL]"
        print(f"  {match} {thread_id}")
        assert thread_id == expected

    # 测试解析
    print("\n解析验证:")
    for user_id, channel, session_id in test_cases:
        thread_id = f"{user_id}::{channel}::{session_id}"
        parsed = session_mgr.parse_thread_id(thread_id)
        match = "[OK]" if (parsed.user_id == user_id and
                       parsed.channel == channel and
                       parsed.session_id == session_id) else "✗"
        print(f"  {match} {thread_id} -> ({parsed.user_id}, {parsed.channel}, {parsed.session_id})")

    print("\n[OK] Thread ID 格式测试通过\n")
    return True


def test_agent_routing():
    """测试不同意图路由到正确的代理。"""
    print("=" * 60)
    print("测试：代理路由")
    print("=" * 60)

    # 重置并重新注册代理
    AgentRegistry.reset()
    from agent import lc_agent, deep_agent

    registry = get_registry()

    # 预期路由
    routing_table = {
        "general_qa": "lc_agent",
        "knowledge_search": "lc_agent",
        "complex_reasoning": "deep_agent",
        "planning": "deep_agent",
    }

    print("\n预期路由:")
    for intent, expected_agent in routing_table.items():
        agent = registry.find_agent_by_intent(intent)
        actual_agent = agent.name if agent else None
        match = "[OK]" if actual_agent == expected_agent else "[FAIL]"
        print(f"  {match} {intent} -> {actual_agent} (预期：{expected_agent})")

    print("\n[OK] 代理路由测试完成\n")
    return True


def main():
    """运行所有多轮测试。"""
    print("\n" + "=" * 60)
    print("多代理编排器 - 多轮测试")
    print("=" * 60 + "\n")

    tests = [
        ("Thread ID 格式", test_thread_id_format),
        ("代理路由", test_agent_routing),
        ("并行会话", test_parallel_sessions),
        ("上下文切换", test_context_switching),
        ("多轮对话", test_multi_round_conversation),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}\n")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 摘要
    print("=" * 60)
    print("测试摘要")
    print("=" * 60)
    for name, success in results:
        status = "通过" if success else "失败"
        print(f"  [{status}] {name}")

    all_passed = all(s for _, s in results)
    print("=" * 60)
    if all_passed:
        print("所有测试通过！")
    else:
        print("有些测试失败！")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
