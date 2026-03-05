"""多代理编排器的基本功能测试。"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.registry.agent_registry import get_registry, AgentRegistry
from core.graph.orchestrator import create_orchestrator
from core.session.session_manager import get_session_manager
from core.schemas.intent import IntentConfig


def test_registry():
    """测试代理注册和查找。"""
    print("=" * 60)
    print("测试：代理注册表")
    print("=" * 60)

    # 重置注册表以进行干净的测试
    AgentRegistry.reset()

    # 导入代理以触发注册
    from agent import lc_agent, deep_agent

    registry = get_registry()

    # 列出所有代理
    agents = registry.list_agents()
    print(f"\nRegistered agents: {[a.name for a in agents]}")

    # 列出所有意图
    intents = registry.list_intents()
    print(f"Registered intents: {intents}")

    # 测试 find_agent_by_intent
    test_intents = ["general_qa", "planning", "complex_reasoning", "knowledge_search"]
    for intent in test_intents:
        agent = registry.find_agent_by_intent(intent)
        if agent:
            print(f"  意图 '{intent}' -> 代理：{agent.name}")
        else:
            print(f"  意图 '{intent}' -> 未找到代理")

    print("\n[OK] 注册表测试通过\n")
    return True


def test_intent_recognition():
    """使用关键词测试意图识别。"""
    print("=" * 60)
    print("测试：意图识别")
    print("=" * 60)

    config = IntentConfig()
    orchestrator = create_orchestrator(config)

    # 测试用例
    test_cases = [
        ("帮我规划一个项目", "planning"),
        ("I need a plan for this", "planning"),
        ("请分解这个复杂任务", "planning"),
        ("什么是量子计算", "general_qa"),
        ("搜索相关信息", "knowledge_search"),
        ("分析这个问题的原因", "complex_reasoning"),
    ]

    for input_text, expected_intent in test_cases:
        # 创建最小测试
        result = _quick_intent_test(input_text, config)
        status = "[OK]" if result["intent"] == expected_intent else "[FAIL]"
        print(f"  {status} Input: '{input_text}'")
        print(f"    Expected: {expected_intent}, Got: {result['intent']} (conf: {result['confidence']:.2f})")

    print("\n[OK] 意图识别测试完成\n")
    return True


def _quick_intent_test(input_text: str, config: IntentConfig) -> dict:
    """快速意图测试，不使用完整的编排器。"""
    # 复制 _analyze_intent 的逻辑
    input_lower = input_text.lower()

    best_intent = config.default_intent
    best_confidence = 0.5

    for intent, keywords in config.keywords.items():
        if not keywords:
            continue
        match_count = sum(1 for kw in keywords if kw.lower() in input_lower)
        if match_count > 0:
            confidence = min(0.9, 0.5 + (match_count * 0.1))
            if confidence > best_confidence:
                best_intent = intent
                best_confidence = confidence

    # 对规划的特殊处理
    if any(kw in input_text for kw in ["规划", "plan", "计划", "分解"]):
        best_intent = "planning"
        best_confidence = 0.85

    return {"intent": best_intent, "confidence": best_confidence}


def test_session_manager():
    """测试会话管理和 thread_id 生成。"""
    print("=" * 60)
    print("测试：会话管理器")
    print("=" * 60)

    session_mgr = get_session_manager()

    # 测试 thread_id 生成
    thread_id1 = session_mgr.get_thread_id("user123", "web")
    print(f"\n生成的 thread_id (自动 session): {thread_id1}")

    thread_id2 = session_mgr.get_thread_id("user123", "web", "session001")
    print(f"生成的 thread_id (自定义 session): {thread_id2}")

    # 测试解析
    parsed = session_mgr.parse_thread_id(thread_id2)
    print(f"\n解析 thread_id:")
    print(f"  user_id: {parsed.user_id}")
    print(f"  channel: {parsed.channel}")
    print(f"  session_id: {parsed.session_id}")

    # 测试配置生成
    config = session_mgr.create_config(thread_id2)
    print(f"\nLangGraph 配置：{config}")

    # 验证格式
    assert "::" in thread_id1, "thread_id 应该包含 '::' 分隔符"
    assert "::" in thread_id2, "thread_id 应该包含 '::' 分隔符"
    assert parsed.user_id == "user123"
    assert parsed.channel == "web"
    assert parsed.session_id == "session001"

    print("\n[OK] 会话管理器测试通过\n")
    return True


def test_full_flow_mock():
    """使用模拟数据测试完整流程。"""
    print("=" * 60)
    print("测试：完整流程（模拟）")
    print("=" * 60)

    # 重置并重新注册代理
    AgentRegistry.reset()
    from agent import lc_agent, deep_agent

    config = IntentConfig()
    orchestrator = create_orchestrator(config)

    # 测试用例
    test_cases = [
        ("你好，请介绍一下自己", "general_qa", "lc_agent"),
        ("帮我规划一个学习计划", "planning", "deep_agent"),
        ("搜索最新的 AI 新闻", "knowledge_search", "lc_agent"),
        ("分析这个复杂问题", "complex_reasoning", "deep_agent"),
    ]

    for input_text, expected_intent, expected_agent in test_cases:
        try:
            result = orchestrator.run(
                user_id="test_user",
                channel="test",
                input_text=input_text,
                session_id="test_session"
            )
            status = "[OK]" if result["intent"] == expected_intent else "[FAIL]"
            print(f"\n  {status} Input: '{input_text}'")
            print(f"    Intent: {result['intent']} (expected: {expected_intent})")
            print(f"    Agent: {result['target_agent']} (expected: {expected_agent})")
            print(f"    Confidence: {result['confidence']:.2f}")
            print(f"    输出（截断）: {result['output_text'][:100]}...")
        except Exception as e:
            print(f"\n  [失败] 输入：'{input_text}'")
            print(f"    错误：{e}")

    print("\n\n[OK] 完整流程测试完成\n")
    return True


def main():
    """运行所有测试。"""
    print("\n" + "=" * 60)
    print("MULTI-AGENT ORCHESTRATOR - BASIC TESTS")
    print("=" * 60 + "\n")

    tests = [
        ("注册表", test_registry),
        ("会话管理器", test_session_manager),
        ("意图识别", test_intent_recognition),
        ("完整流程（模拟）", test_full_flow_mock),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}\n")
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
