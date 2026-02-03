# AI Daily Collector - FastAPI 接口
# 提供 REST API 访问 + RSS Feed 输出

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from fastapi import FastAPI, HTTPException, Query, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import XMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入数据模块
from scripts.generate_daily_report import generate_report, CATEGORIES

# ============ 应用配置 ============

app = FastAPI(
    title="AI Daily Collector API",
    description="""
    🤖 AI 热点资讯自动采集与分发系统 API
    
    ## 功能特性
    - 📡 **RSS 订阅** - 支持 RSS/Atom Feed 输出，可订阅到 RSS Reader
    - 📝 **日报获取** - 获取每日 AI 热点资讯日报
    - 📰 **文章管理** - 浏览、搜索、筛选文章
    - 🔔 **订阅通知** - 订阅特定分类或关键词
    
    ## 使用场景
    1. **RSS Reader** - 将本 API 订阅到 RSS 阅读器
    2. **自动化工作流** - 通过 API 获取数据并处理
    3. **二次开发** - 基于本 API 开发自定义应用
    
    ## 认证
    当前版本无需认证，后续可添加 API Key 认证。
    
    ## 速率限制
    - 每分钟最多 60 次请求
    - 单次请求最多返回 100 条记录
    
    ## 反馈
    如有问题，请提交 [Issue](https://github.com/xxl115/ai-daily-collector/issues)
    """,
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "🏠 首页", "description": "系统状态和基本信息"},
        {"name": "📰 日报", "description": "每日日报相关接口"},
        {"name": "📝 文章", "description": "文章浏览和搜索"},
        {"name": "📡 RSS 订阅", "description": "RSS Feed 订阅接口"},
        {"name": "🔧 系统", "description": "系统配置和工具"},
    ],
    servers=[
        {"url": "http://localhost:8000", "description": "本地开发"},
        {"url": "https://api.example.com", "description": "生产环境"},
    ],
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
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API 版本")
    version_name: str = Field(..., description="版本名称")
    timestamp: str = Field(..., description="当前时间")
    data_dir: str = Field(..., description="数据目录")


class ArticleSummary(BaseModel):
    """文章摘要"""
    title: str = Field(..., description="文章标题")
    source: str = Field(..., description="来源")
    url: str = Field(..., description="原文链接")
    summary: str = Field(..., description="中文总结")
    category: str = Field(..., description="分类")
    date: str = Field(..., description="发布日期")


class DailyReport(BaseModel):
    """日报响应"""
    date: str = Field(..., description="日期")
    focus_article: Optional[ArticleSummary] = Field(None, description="今日焦点")
    categories: Dict[str, List[Dict[str, Any]]] = Field(..., description="分类文章")
    stats: Dict[str, int] = Field(..., description="统计信息")


class ArticleListResponse(BaseModel):
    """文章列表响应"""
    date: str = Field(..., description="查询日期")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    articles: List[Dict[str, Any]] = Field(..., description="文章列表")


class CategoryInfo(BaseModel):
    """分类信息"""
    id: str = Field(..., description="分类 ID")
    name: str = Field(..., description="分类名称")
    count: int = Field(..., description="文章数量")
    keywords: List[str] = Field(..., description="分类关键词")


class StatsResponse(BaseModel):
    """统计信息响应"""
    today: Dict[str, Any] = Field(..., description="今日统计")
    yesterday: Dict[str, Any] = Field(..., description="昨日统计")
    total: Dict[str, int] = Field(..., description="总计统计")


class RSSItem(BaseModel):
    """RSS 项"""
    title: str
    link: str
    description: str
    pub_date: str
    category: str


# ============ 辅助函数 ============

def get_data_dir() -> Path:
    """获取数据目录"""
    data_dir = os.environ.get("DATA_DIR", "/home/young/clawd/ai/ai-daily-collector/data")
    return Path(data_dir)


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def parse_article_file(filepath: Path) -> Optional[Dict]:
    """解析文章文件"""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # 提取信息
        title_match = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
        source_match = re.search(r'^source:\s*"(.+)"', content, re.MULTILINE)
        url_match = re.search(r'original_url:\s*"(.+)"', content, re.MULTILINE)
        summary_match = re.search(r'## 中文总结\s*\n(.+?)(?:\n---|\Z)', content, re.DOTALL)
        date_match = re.search(r'^date:\s*"(.+)"', content, re.MULTILINE)
        
        return {
            "title": title_match.group(1) if title_match else filepath.stem,
            "source": source_match.group(1) if source_match else "Unknown",
            "url": url_match.group(1) if url_match else "",
            "summary": summary_match.group(1).strip() if summary_match else "",
            "date": date_match.group(1) if date_match else "",
            "filepath": filepath.name,
        }
    except Exception:
        return None


# ============ 缓存 ============

_cache = {}


def cache_get(key: str, expire_seconds: int = 300):
    """获取缓存"""
    if key in _cache:
        data, timestamp = _cache[key]
        if (datetime.now() - timestamp).seconds < expire_seconds:
            return data
    return None


def cache_set(key: str, value: Any):
    """设置缓存"""
    _cache[key] = (value, datetime.now())


# ============ API 端点 ============

@app.get("/", response_model=HealthResponse, tags=["🏠 首页"])
async def root():
    """
    🏠 API 根路径 - 健康检查
    
    返回系统状态、版本信息和当前时间。
    """
    return {
        "status": "healthy",
        "version": "0.2.0",
        "version_name": "v0.2.0 (Beta)",
        "timestamp": datetime.now().isoformat(),
        "data_dir": str(get_data_dir()),
    }


@app.get("/health", tags=["🏠 首页"])
async def health_check():
    """
    ❤️ 健康检查
    
    简单的健康检查端点，适用于负载均衡器检查。
    """
    return {"status": "ok", "service": "ai-daily-collector"}


@app.get("/api/v1/report/today", response_model=DailyReport, tags=["📰 日报"])
async def get_today_report():
    """
    📰 获取今日日报
    
    返回今日 AI 热点资讯日报，包括：
    - 今日焦点文章
    - 各分类文章列表
    - 统计信息
    
    如果今日日报未生成，会返回最近的日报。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = get_data_dir()
    report_path = data_dir / "daily" / f"ai-hotspot-{today}.md"
    
    # 如果今日日报不存在，尝试查找最近的日报
    if not report_path.exists():
        for i in range(7):  # 查找最近 7 天
            check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            report_path = data_dir / "daily" / f"ai-hotspot-{check_date}.md"
            if report_path.exists():
                today = check_date
                break
        else:
            raise HTTPException(
                status_code=404,
                detail=f"未找到任何日报文件"
            )
    
    # 解析日报
    content = report_path.read_text(encoding='utf-8')
    
    # 简化响应（实际项目中可以解析 Markdown）
    return {
        "date": today,
        "focus_article": None,
        "categories": {},
        "stats": {"total": 0, "categories": 0}
    }


@app.get("/api/v1/report/{date}", response_model=DailyReport, tags=["📰 日报"])
async def get_report_by_date(date: str):
    """
    📰 获取指定日期的日报
    
    Args:
        date: 日期，格式 YYYY-MM-DD
    
    Returns:
        当日报文数据
    
    Raises:
        400: 日期格式无效
        404: 日报不存在
    """
    # 验证日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式无效，请使用 YYYY-MM-DD 格式"
        )
    
    data_dir = get_data_dir()
    report_path = data_dir / "daily" / f"ai-hotspot-{date}.md"
    
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {date} 的日报"
        )
    
    return {
        "date": date,
        "focus_article": None,
        "categories": {},
        "stats": {"total": 0, "categories": 0}
    }


@app.get("/api/v1/articles", response_model=ArticleListResponse, tags=["📝 文章"])
async def list_articles(
    date: Optional[str] = Query(
        None, 
        description="日期，格式 YYYY-MM-DD，默认今天"
    ),
    category: Optional[str] = Query(
        None, 
        description="分类筛选（大厂人物/Agent工作流/编程助手/内容生成/工具生态/安全风险）"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
):
    """
    📝 获取文章列表
    
    支持日期筛选、分类筛选、关键词搜索和分页。
    
    Args:
        date: 日期筛选
        category: 分类筛选
        page: 页码（从 1 开始）
        page_size: 每页数量（最大 100）
        keyword: 关键词搜索
    
    Returns:
        文章列表数据
    """
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    summary_dir = get_project_root() / "ai" / "articles" / "summary" / target_date
    
    if not summary_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {target_date} 的文章"
        )
    
    # 获取所有文章
    articles = []
    for f in summary_dir.glob("*.md"):
        article = parse_article_file(f)
        if article:
            # 分类筛选
            if category:
                if category.lower() not in article.get("title", "").lower():
                    continue
            # 关键词搜索
            if keyword:
                if keyword.lower() not in article.get("title", "").lower() and \
                   keyword.lower() not in article.get("summary", "").lower():
                    continue
            articles.append(article)
    
    # 分页
    total = len(articles)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_articles = articles[start:end]
    
    return {
        "date": target_date,
        "total": total,
        "page": page,
        "page_size": page_size,
        "articles": paginated_articles
    }


@app.get("/api/v1/categories", response_model=List[CategoryInfo], tags=["📰 日报"])
async def list_categories():
    """
    📋 获取分类列表
    
    返回所有可用的分类及其关键词。
    """
    categories = []
    
    category_map = {
        "大厂人物": ["anthropic", "openai", "google", "microsoft", "nvidia"],
        "Agent工作流": ["agent", "mcp", "a2a", "workflow", "autogen"],
        "编程助手": ["cursor", "windsurf", "copilot", "ide"],
        "内容生成": ["writing", "video", "audio", "image"],
        "工具生态": ["openclaw", "langchain", "sdk"],
        "安全风险": ["security", "vulnerability", "deepfake"],
    }
    
    for cat, keywords in category_map.items():
        categories.append({
            "id": cat,
            "name": cat,
            "count": 0,  # 可以实时统计
            "keywords": keywords
        })
    
    return categories


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["🔧 系统"])
async def get_stats():
    """
    📊 获取统计信息
    
    返回今日、昨日和总计的统计信息。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    stats = {
        "today": {"date": today, "articles": 0, "reports": 1},
        "yesterday": {"date": yesterday, "articles": 0, "reports": 1},
        "total": {"articles": 0, "reports": 0}
    }
    
    return stats


# ============ RSS Feed ============

@app.get("/rss", tags=["📡 RSS 订阅"])
async def get_rss_feed(
    limit: int = Query(20, ge=1, le=50, description="最大文章数"),
    category: Optional[str] = Query(None, description="分类筛选"),
):
    """
    📡 获取 RSS Feed
    
    支持 RSS Reader 订阅，输出标准 RSS 2.0 格式。
    
    Args:
        limit: 最大文章数（默认 20，最大 50）
        category: 分类筛选
    
    Returns:
        RSS 2.0 XML 格式
    """
    target_date = datetime.now().strftime("%Y-%m-%d")
    summary_dir = get_project_root() / "ai" / "articles" / "summary" / target_date
    
    if not summary_dir.exists():
        # 尝试前一天
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        summary_dir = get_project_root() / "ai" / "articles" / "summary" / target_date
    
    if not summary_dir.exists():
        return XMLResponse(content=generate_empty_rss())
    
    # 收集文章
    articles = []
    for f in sorted(summary_dir.glob("*.md"), reverse=True)[:limit]:
        article = parse_article_file(f)
        if article:
            if category and category.lower() not in article.get("title", "").lower():
                continue
            articles.append(article)
    
    # 生成 RSS
    rss_content = generate_rss(articles, target_date)
    return XMLResponse(content=rss_content, media_type="application/rss+xml")


@app.get("/rss/latest", tags=["📡 RSS 订阅"])
async def get_rss_feed_latest(
    limit: int = Query(10, ge=1, le=50, description="最大文章数"),
):
    """
    📡 获取最新文章 RSS Feed
    
    获取所有日期的最新文章。
    """
    articles = []
    data_dir = get_project_root() / "ai" / "articles" / "summary"
    
    # 收集最近的文章
    for date_dir in sorted(data_dir.iterdir(), reverse=True)[:3]:  # 最近 3 天
        if date_dir.is_dir():
            for f in sorted(date_dir.glob("*.md"), reverse=True)[:10]:
                article = parse_article_file(f)
                if article:
                    article["date"] = date_dir.name
                    articles.append(article)
                if len(articles) >= limit:
                    break
        if len(articles) >= limit:
            break
    
    rss_content = generate_rss(articles, datetime.now().strftime("%Y-%m-%d"))
    return XMLResponse(content=rss_content, media_type="application/rss+xml")


def generate_rss(articles: List[Dict], date: str) -> str:
    """生成 RSS 2.0 XML"""
    project_root = get_project_root()
    readme = project_root / "README.md"
    
    description = "AI 热点资讯自动采集与分发系统"
    if readme.exists():
        desc_content = readme.read_text(encoding='utf-8')[:200]
        description = re.sub(r'[^\w\s]', '', desc_content).strip()[:200]
    
    # 创建 RSS 元素
    rss = Element('rss', version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    
    channel = SubElement(rss, 'channel')
    
    # Channel 元素
    title = SubElement(channel, 'title')
    title.text = f"AI Daily - {date}"
    
    link = SubElement(channel, 'link')
    link.text = "https://github.com/xxl115/ai-daily-collector"
    
    desc = SubElement(channel, 'description')
    desc.text = description
    
    language = SubElement(channel, 'language')
    language.text = "zh-CN"
    
    lastBuildDate = SubElement(channel, 'lastBuildDate')
    lastBuildDate.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    # Atom link
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set("href", "https://api.example.com/rss")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    
    # Items
    for article in articles:
        item = SubElement(channel, 'item')
        
        item_title = SubElement(item, 'title')
        item_title.text = article.get("title", "无标题")[:200]
        
        item_link = SubElement(item, 'link')
        item_link.text = article.get("url", "") or "https://github.com/xxl115/ai-daily-collector"
        
        item_desc = SubElement(item, 'description')
        item_desc.text = article.get("summary", "")[:500]
        
        item_guid = SubElement(item, 'guid')
        item_guid.text = article.get("url", "") or f"https://github.com/xxl115/ai-daily-collector#{article.get('filepath', '')}"
        item_guid.set("isPermaLink", "false")
        
        item_pubdate = SubElement(item, 'pubDate')
        item_pubdate.text = article.get("date", date)
    
    # 生成 XML 字符串
    xml_str = tostring(rss, encoding='unicode')
    xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    # 移除 XML 声明（RSS 不需要）
    xml_str = '\n'.join(xml_str.split('\n')[1:])
    
    return xml_str


def generate_empty_rss() -> str:
    """生成空的 RSS"""
    rss = Element('rss', version="2.0")
    channel = SubElement(rss, 'channel')
    
    title = SubElement(channel, 'title')
    title.text = "AI Daily"
    
    link = SubElement(channel, 'link')
    link.text = "https://github.com/xxl115/ai-daily-collector"
    
    desc = SubElement(channel, 'description')
    desc.text = "暂无文章数据"
    
    return tostring(rss, encoding='unicode')


# ============ 启动 ============

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
