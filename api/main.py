"""AI Daily Collector - FastAPI API (Database Version)"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入 API v2 路由
from api.v2 import v2_router

app = FastAPI(
    title="AI Daily Collector API",
    description="AI Daily Collector REST API - 使用 D1 数据库存储",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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
