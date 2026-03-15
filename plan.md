我打算开发一个Agent系统，基于意图识别可以路由到多个子Agent完成特定的任务
技术栈选择langchain1.0以后的技术，语言选择python，数据库选择mysql。
我的目录结构如下：
```
src
|- controller (基于fastapi实现)
|---|- __init__.py
|---|- bot_controller.py (机器人入口)
|---|- web_controller.py (web入口)
|- orchestration (编排器，用于编排主流程，基于langgraph实现)
|---|- __init__.py
|---|- master_workflow.py (主流程：意图识别 -> 路由器 -> 执行器)
|---|- base_executor.py (执行器基类，Agent继承该类，实现执行器的run方法，即可接入主流程)
|---|- registry.py (注册器，使用装饰器注册Agent，定义一些元数据，比如Agent的名字，描述，意图识别用到的关键词，快捷命令@ 等)
|- agents (具体Agent，基于langchain或langgraph实现，都是langchain家族的技术)
|---|- __init__.py
|---|- default_agent.py (默认的Agent，意图不清晰的请求默认进入该Agent处理)
|---|- code_agent.py (Code Agent，用于处理代码请求)
|---|- plan_agent.py (Plan Agent，用于管理用户的计划)
|- core
|---|- __init__.py
|---|- intent.py (意图识别类，被主流程的意图识别节点调用，按照策略识别意图)
|---|- session_manager.py (会话管理器，用于管理会话，保存会话信息，提供会话上下文给执行器)
|- infra
|---|- __init__.py
|---|- database.py
|---|- llm.py
```

你需要关注的设计有：
1. 会话管理：
   - 由于机器人是一个多用户多会话的场景，需要有一个会话管理器，用于管理会话，保存会话信息，提供会话上下文给执行器。
   - 会话隔离：controller传入时包含user_id以及channel_id，这两个参数组成一个会话ID，用于会话隔离。
   - 会话消息：复用langchain的message，用于保存会话消息。
   - 单轮会话：用户输入的信息进入子Agent后，可能涉及多次工具调用，结束这些信息需要整合为一个轮次的消息，并用会话管理器保存起来，以便后续使用。
     - 一个轮次的消息包含：轮次Id, 当前Agent，消息列表，最终回复。
     - 单轮次的消息可能也会触发上下文压缩，这里可以使用langchain提供的一些中间件实现。
   - 用户的多轮会话时，需要跨Agent传入历史信息，这里涉及到一些上下文压缩策略，比如3轮对话之前的轮次信息，我只传递最终回复，近三轮的会传递轮次细节信息。
   - 会话信息存储：初步实现第一版可以先基于内存实现，后续可以扩展到数据库中。
2. 意图识别：
   - 你需要实现一个意图识别类，分级识别意图，这个我暂时没有太好的思路。
3. config：我已经提供了模型，你需要至少配置这些内容：
   - OPENAI_API_KEY: Optional[str] = "sk-sp-b6c188b0bd9d478ca5fba8b8b34cc5f1"
   - OPENAI_BASE_URL: Optional[str] = "https://coding.dashscope.aliyuncs.com/v1"
   - DEFAULT_MODEL: str = "qwen3.5-plus"
   - INTENT_MODEL: str = "qwen3.5-plus"


