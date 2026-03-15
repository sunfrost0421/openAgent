"""Agent 系统应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# 导入 agents 模块以注册 Agent
from src.agents import default_agent, code_agent, plan_agent  # noqa: F401
from src.controller.bot_controller import router
from src.core.session_manager import session_manager


_logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info("Starting Agent System...")
    yield
    _logger.info("Shutting down Agent System...")
    # 清理过期会话
    await session_manager.cleanup_expired()


app = FastAPI(
    title="Agent System",
    description="Multi-Agent routing system based on intent recognition",
    version="0.1.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import asyncio

    # 配置根日志级别，显示应用内部日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 检测是否在调试器中运行（PyCharm 调试模式）
    import sys
    if sys.gettrace() is not None:
        # 调试模式：使用兼容方式启动，避免 loop_factory 参数问题
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
        server = uvicorn.Server(config)

        # 在调试器中需要直接运行 serve 协程
        print("Starting in debug mode...")
        asyncio.run(server.serve())
    else:
        # 正常运行模式
        uvicorn.run(app, host="0.0.0.0", port=8000)
