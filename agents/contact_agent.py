"""
个人信息抽取 Agent - 从文本中提取联系信息
"""

import json
from http.client import responses
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from core.base_agent import BaseAgent
from core.registry import registry


class ContactInfo(BaseModel):
    """联系信息结构化输出"""
    name: str = Field(description="姓名")
    email: Optional[str] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="电话")
    company: Optional[str] = Field(default=None, description="公司/组织")
    position: Optional[str] = Field(default=None, description="职位")
    address: Optional[str] = Field(default=None, description="地址")
    website: Optional[str] = Field(default=None, description="网站/主页")
    additional_info: Optional[str] = Field(default=None, description="其他补充信息")


@registry.register(
    name="contact_extractor",
    description="个人信息抽取助手，从文本中提取姓名、邮箱、电话等联系信息",
    category="extraction",
    keywords=[
        "联系信息",
        "个人信息",
        "抽取",
        "提取",
        "姓名",
        "邮箱",
        "电话",
        "名片",
        "联系方式",
        "结构化",
    ],
)
class ContactExtractorAgent(BaseAgent):
    """个人信息抽取 Agent"""

    def get_system_prompt(self) -> str:
        return """你是一位专业的信息抽取助手。你的职责是从用户提供的文本中提取联系信息。

提取字段包括：
- name: 姓名（必填）
- email: 邮箱
- phone: 电话
- company: 公司/组织
- position: 职位
- address: 地址
- website: 网站/主页
- additional_info: 其他补充信息

规则：
1. 只提取文本中明确提及的信息，不要臆造
2. 如果某个字段无法提取，返回 null
3. 保持信息原样，不要修改格式
4. 输出为清晰的 JSON 格式
"""

    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理个人信息抽取请求"""
        from langchain_core.messages import HumanMessage, SystemMessage

        # 使用支持结构化输出的方式调用
        if self.llm is None:
            from config import settings
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                model=settings.DEFAULT_MODEL,
                base_url=settings.OPENAI_BASE_URL,
                api_key=settings.OPENAI_API_KEY,
            )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(
                content=f"请从以下文本中提取联系信息，输出 JSON 格式：\n\n{user_input}"
            ),
        ]

        from langchain.agents import create_agent
        agent = create_agent(
            model=self.llm,
            response_format=ContactInfo  # 自动使用 ProviderStrategy
        )

        response = await agent.ainvoke({
            "messages": messages
        })

        # 调用 LLM
        result = response["structured_response"]

        return result