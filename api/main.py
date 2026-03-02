"""AI Daily Collector - FastAPI API (Database Version)"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入 API v2 路由
from api.v2 import v2_router, daily_router
from api.mcp import router as mcp_router

# ==================== 限流中间件 ====================


class RateLimiter:
    """简单的内存限流器"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - 60

        with self.lock:
            # 清理过期请求
            self.requests[client_id] = [t for t in self.requests[client_id] if t > window_start]

            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False

            self.requests[client_id].append(now)
            return True

    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        window_start = now - 60
        with self.lock:
            current = len([t for t in self.requests[client_id] if t > window_start])
            return max(0, self.requests_per_minute - current)


# 全局限流器
rate_limiter = RateLimiter(requests_per_minute=60)


async def rate_limit_middleware(request: Request, call_next):
    """API 限流中间件"""
    # 跳过健康检查和文档路由
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    client_id = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    response = await call_next(request)
    remaining = rate_limiter.get_remaining(client_id)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    return response


app = FastAPI(
    title="AI Daily Collector API",
    description="AI Daily Collector REST API - 使用 D1 数据库存储",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 注册限流中间件
app.middleware("http")(rate_limit_middleware)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API v2 路由
app.include_router(v2_router)

# 注册 Daily 路由
app.include_router(daily_router)

# 注册 MCP 路由
app.include_router(mcp_router)


class HealthResponse(BaseModel):
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API 版本")
    timestamp: str = Field(..., description="当前时间")


@app.get("/", response_model=HealthResponse)
async def root():
    """API 根路径 - 健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "ai-daily-collector"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
