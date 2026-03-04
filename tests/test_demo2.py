# -*- coding: utf-8 -*-
"""
完整调用链测试 - 意图识别 + 子 Agent 执行
测试从 IntentAgent 到 ContactExtractorAgent 的完整流程
直接运行：python tests/test_demo2.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.registry import registry
from agents.intent_agent import IntentAgent
from agents.contact_agent import ContactExtractorAgent


def test_registered_agents():
    """测试 1: 查看所有已注册的 Agent"""
    print("=" * 60)
    print("【测试 1】已注册的 Agent 列表")
    print("=" * 60)

    agents = registry.get_all_agents()
    for name, meta in agents.items():
        print(f"  [*] {name}")
        print(f"    分类：{meta.category}")
        print(f"    描述：{meta.description}")
        print(f"    关键词：{', '.join(meta.keywords)}")
        print()


def test_keyword_matching():
    """测试 2: 关键词匹配 - 测试 contact_extractor 的匹配"""
    print("=" * 60)
    print("【测试 2】关键词匹配 - 信息提取相关")
    print("=" * 60)

    test_cases = [
        # 应该匹配 contact_extractor
        ("从文本中提取联系方式", "contact_extractor"),
        ("帮我提取名片上的信息", "contact_extractor"),
        ("抽取这段文本中的邮箱和电话", "contact_extractor"),
        ("整理一下这些联系信息", "contact_extractor"),
        # 应该匹配其他 agent
        ("写一个 Python 函数", "coding_assistant"),
        ("分析销售数据", "analysis_agent"),
    ]

    for query, expected in test_cases:
        match = registry.find_best_match(query)
        status = "OK" if match == expected else "FAIL"
        print(f"  [{status}] 输入：\"{query}\"")
        print(f"    期望：{expected} | 匹配：{match}")
        print()


def test_intent_prompt():
    """测试 3: 查看意图识别的 System Prompt"""
    print("=" * 60)
    print("【测试 3】意图识别 System Prompt")
    print("=" * 60)

    prompt = registry.get_intent_prompt()
    print(prompt)
    print()


async def test_contact_extractor_directly():
    """测试 4: 直接调用 ContactExtractorAgent"""
    print("=" * 60)
    print("【测试 4】直接调用 ContactExtractorAgent")
    print("=" * 60)

    agent = ContactExtractorAgent()

    test_input = """
    张三，清华大学计算机系教授
    邮箱：zhangsan@tsinghua.edu.cn
    电话：+86-138-0013-8000
    地址：北京市海淀区双清路 30 号
    研究方向：人工智能、机器学习
    """

    print(f"输入文本：\n{test_input}")
    print()

    try:
        response = await agent.act(test_input)
        print(f"提取结果：\n{response}")
    except Exception as e:
        print(f"错误：{e}")
    print()


async def test_full_chain():
    """测试 5: 完整调用链 - IntentAgent -> ContactExtractorAgent"""
    print("=" * 60)
    print("【测试 5】完整调用链测试 - IntentAgent 路由到 ContactExtractorAgent")
    print("=" * 60)

    # 创建 IntentAgent 实例
    intent_agent = IntentAgent()

    # 测试用例 - 应该触发信息提取
    test_cases = [
        "从这段文本中提取联系信息：李四，阿里云高级工程师，邮箱 lisi@alibabacloud.com，电话 139-1234-5678",
        "帮我抽取名片数据：王五，CEO，某科技公司，电话 010-88888888，邮箱 wangwu@tech.com",
        "整理这些联系人：张三 (zhang@test.com, 138-0000-0001), 李四 (li@test.com, 138-0000-0002)",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"用户输入：\"{query}\"")
        print()

        try:
            # 执行完整调用链
            response = await intent_agent.act(query)
            print(f"响应结果：\n{response}")
        except Exception as e:
            print(f"错误：{type(e).__name__}: {e}")
        print()


async def test_chain_with_fallback():
    """测试 6: 测试意图不清晰时的 fallback"""
    print("=" * 60)
    print("【测试 6】Fallback 测试 - 意图不清晰")
    print("=" * 60)

    intent_agent = IntentAgent()

    test_cases = [
        "你好",
        "今天天气怎么样",
        "随便聊聊",
    ]

    for query in test_cases:
        print(f"\n输入：\"{query}\"")
        try:
            response = await intent_agent.act(query)
            print(f"响应：{response}")
        except Exception as e:
            print(f"错误：{e}")
    print()


async def main():
    """主测试流程"""
    # print("\n")
    # print(">> 完整调用链测试 - 意图识别 -> 信息提取")
    # print("=" * 60)
    # print()
    #
    # # 同步测试
    # test_registered_agents()
    # test_keyword_matching()
    # test_intent_prompt()
    #
    # # 异步测试
    # print("\n>>> 开始异步测试（需要 LLM 调用）\n")
    #
    # # 测试 4: 直接调用 ContactExtractorAgent
    # await test_contact_extractor_directly()

    # 测试 5: 完整调用链
    await test_full_chain()

    # # 测试 6: Fallback 测试
    # await test_chain_with_fallback()

    print("=" * 60)
    print("OK 完整调用链测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())