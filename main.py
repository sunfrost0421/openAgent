"""Agent 系统应用入口"""

import logging
import os
import sys
from contextlib import asynccontextmanager

# 将项目根目录添加到 Python 路径，支持 src 目录结构
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI

# 导入 features 模块以注册 Agent
from src.features.code import code_agent  # noqa: F401
from src.features.plan import plan_agent
from src.features.default import default_agent
from src.features.diff_analysis import diff_agent  # noqa: F401
from src.core.orchestration.registry import agent_registry
from src.core.orchestration.intent import intent_recognizer
from src.controller.bot_controller import router
from src.controller.web_controller import router as web_router
from src.core.session.manager import session_manager
from src.infra.database import db_manager
from src.config import Config


_logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info("Starting Agent System...")

    # 初始化数据库（如果使用 MySQL）
    config = Config.get()
    if config.USE_MYSQL:
        _logger.info(f"Connecting to MySQL at {config.MYSQL_HOST}:{config.MYSQL_PORT}")
        await db_manager.init()
        _logger.info("Database initialized")
    else:
        _logger.info("Using in-memory session storage")

    # 显式注册所有 Agent 到意图识别器
    for name, metadata in agent_registry.get_all_metadata().items():
        intent_recognizer.register_agent(metadata)
        _logger.info(f"Registered agent with intent_recognizer: {name}")

    yield

    _logger.info("Shutting down Agent System...")
    # 清理过期会话
    await session_manager.cleanup_expired()
    # 关闭数据库连接
    if config.USE_MYSQL:
        await db_manager.close()


app = FastAPI(
    title="Agent System",
    description="Multi-Agent routing system based on intent recognition",
    version="0.1.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(router, prefix="/api/v1")
app.include_router(web_router, prefix="/api/v1/web")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import asyncio
    import os

    # 配置根日志级别，显示应用内部日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 始终使用调试兼容的启动方式
    # 通过环境变量区分模式（可选）
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    if debug_mode:
        # 显式调试模式：使用 Server.serve() 直接启动
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
        server = uvicorn.Server(config)
        print("Starting in explicit debug mode...")
        asyncio.run(server.serve())
    else:
        # 默认模式：使用 uvicorn.run()
        # 如果在 PyCharm 中遇到问题，设置 DEBUG_MODE=true 环境变量
        try:
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except TypeError as e:
            if "loop_factory" in str(e):
                print("Detected loop_factory compatibility issue, switching to debug mode...")
                config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
                server = uvicorn.Server(config)
                asyncio.run(server.serve())
            else:
                raise
