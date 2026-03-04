"""
意图识别功能测试 - 简单演示
直接运行：python tests/test_demo1.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.registry import registry
from agents.intent_agent import IntentAgent


def test_registry():
    """测试注册中心"""
    print("=" * 50)
    print("【测试 1】注册中心 - 已注册的 Agent")
    print("=" * 50)

    agents = registry.get_all_agents()
    for name, meta in agents.items():
        print(f"  - {name}: {meta.description}")
    print()


def test_keyword_match():
    """测试关键词匹配"""
    print("=" * 50)
    print("【测试 2】关键词快速匹配")
    print("=" * 50)

    test_cases = [
        "帮我写个 Python 函数",
        "分析这个数据集",
        "写一篇作文",
        "提取名片上的联系方式",
        "从文本中抽取邮箱和电话",
    ]

    for query in test_cases:
        match = registry.find_best_match(query)
        print(f"  输入：\"{query}\"")
        print(f"  匹配：{match}")
        print()


def test_intent_prompt():
    """测试生成的意图提示"""
    print("=" * 50)
    print("【测试 3】意图识别 System Prompt")
    print("=" * 50)

    prompt = registry.get_intent_prompt()
    print(prompt)
    print()


async def test_intent_agent():
    """测试 IntentAgent 完整流程"""
    print("=" * 50)
    print("【测试 4】IntentAgent 完整意图识别")
    print("=" * 50)

    agent = IntentAgent()

    test_cases = [
        "帮我写一个 Python 函数，计算斐波那契数列",
        "从这段文本中提取联系信息：张三，邮箱 zhangsan@test.com，电话 13800138000",
        "分析一下这个销售数据趋势",
    ]

    for query in test_cases:
        print(f"\n  用户输入：\"{query}\"")
        try:
            # 只测试意图识别，不实际执行子 agent
            # 这里简单演示，实际 act 会调用子 agent
            print(f"  (需要调用 LLM，跳过实际执行)")
        except Exception as e:
            print(f"  错误：{e}")

    print()


if __name__ == "__main__":
    print("\n")
    print("🚀 意图识别功能测试")
    print("=" * 50)
    print()

    # 测试 1: 注册中心
    test_registry()

    # 测试 2: 关键词匹配
    test_keyword_match()

    # 测试 3: 意图提示
    test_intent_prompt()

    # 测试 4: IntentAgent (需要 LLM)
    # asyncio.run(test_intent_agent())

    print("=" * 50)
    print("✅ 测试完成！")
    print("=" * 50)