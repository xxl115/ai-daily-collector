# AI Daily Collector - FastAPI 接口
# 提供 REST API 访问

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入数据模块
from scripts.generate_daily_report import generate_report, CATEGORIES

app = FastAPI(
    title="AI Daily Collector API",
    description="AI 热点资讯自动采集与分发系统 API",
    version="0.2.0",
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


# ============ 数据模型 ============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
    data_dir: str


class ArticleSummary(BaseModel):
    """文章摘要"""
    title: str
    source: str
    url: str
    summary: str
    category: str


class DailyReport(BaseModel):
    """日报响应"""
    date: str
    focus_article: Optional[ArticleSummary] = None
    categories: Dict[str, List[ArticleSummary]]
    stats: Dict[str, int]


class ArticleListResponse(BaseModel):
    """文章列表响应"""
    date: str
    total: int
    articles: List[Dict]


# ============ API 端点 ============

@app.get("/", response_model=HealthResponse)
async def root():
    """API 根路径 - 健康检查"""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "timestamp": datetime.now().isoformat(),
        "data_dir": os.environ.get("DATA_DIR", "/app/data")
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "ai-daily-collector"}


@app.get("/api/v1/report/today", response_model=DailyReport)
async def get_today_report():
    """获取今日日报"""
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = Path(f"ai/daily/ai-hotspot-{today}.md")
    
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"今日日报未生成: {today}"
        )
    
    # 读取并解析日报
    content = report_path.read_text(encoding='utf-8')
    
    # TODO: 解析 Markdown 返回结构化数据
    return {
        "date": today,
        "focus_article": None,
        "categories": {},
        "stats": {"total": 0}
    }


@app.get("/api/v1/report/{date}", response_model=DailyReport)
async def get_report_by_date(date: str):
    """获取指定日期的日报"""
    # 验证日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式无效，请使用 YYYY-MM-DD"
        )
    
    report_path = Path(f"ai/daily/ai-hotspot-{date}.md")
    
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {date} 的日报"
        )
    
    return {
        "date": date,
        "focus_article": None,
        "categories": {},
        "stats": {"total": 0}
    }


@app.get("/api/v1/articles", response_model=ArticleListResponse)
async def list_articles(
    date: Optional[str] = Query(
        None, 
        description="日期，格式 YYYY-MM-DD，默认今天"
    ),
    category: Optional[str] = Query(
        None, 
        description="分类筛选"
    ),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """获取文章列表"""
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    summary_dir = Path(f"ai/articles/summary/{target_date}")
    
    if not summary_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {target_date} 的文章"
        )
    
    articles = []
    for f in summary_dir.glob("*.md")[:limit]:
        content = f.read_text(encoding='utf-8')
        # 提取基本信息
        import re
        title = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
        source = re.search(r'^source:\s*"(.+)"', content, re.MULTILINE)
        url = re.search(r'original_url:\s*"(.+)"', content, re.MULTILINE)
        
        articles.append({
            "filename": f.name,
            "title": title.group(1) if title else f.name,
            "source": source.group(1) if source else "Unknown",
            "url": url.group(1) if url else ""
        })
    
    return {
        "date": target_date,
        "total": len(articles),
        "articles": articles
    }


@app.get("/api/v1/articles/{date}/{filename}")
async def get_article(date: str, filename: str):
    """获取单篇文章详情"""
    article_path = Path(f"ai/articles/summary/{date}/{filename}")
    
    if not article_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到文章: {date}/{filename}"
        )
    
    return {
        "path": str(article_path),
        "content": article_path.read_text(encoding='utf-8')
    }


@app.get("/api/v1/categories")
async def list_categories():
    """获取分类列表"""
    return {
        "categories": list(CATEGORIES.keys()) + ["其他"],
        "focus_keywords": CATEGORIES.get("大厂人物", {}).get("keywords", [])[:10]
    }


@app.get("/api/v1/stats")
async def get_stats():
    """获取统计信息"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    stats = {
        "today": {
            "date": today,
            "articles": 0,
            "reports": 0
        },
        "yesterday": {
            "date": yesterday,
            "articles": 0,
            "reports": 0
        }
    }
    
    # 统计今日文章
    today_dir = Path(f"ai/articles/summary/{today}")
    if today_dir.exists():
        stats["today"]["articles"] = len(list(today_dir.glob("*.md")))
    
    # 检查日报
    today_report = Path(f"ai/daily/ai-hotspot-{today}.md")
    stats["today"]["reports"] = 1 if today_report.exists() else 0
    
    return stats


# ============ 触发任务 ============

@app.post("/api/v1/trigger/crawl")
async def trigger_crawl():
    """触发文章采集"""
    return {"message": "采集任务已触发，请稍后查看日报"}


@app.post("/api/v1/trigger/report")
async def trigger_report():
    """触发日报生成"""
    return {"message": "日报生成任务已触发"}


# ============ 启动 ============

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
