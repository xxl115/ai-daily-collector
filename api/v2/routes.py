"""
API v2 路由
适配前端需求的 REST API 端点
"""
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import random

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from .models import (
    ArticleModel,
    ArticleListResponse,
    ArticleListDataResponse,
    SuggestionsDataResponse,
    SuggestionsResponse,
    CategoriesDataResponse,
    SourcesDataResponse,
    StatsDataResponse,
    StatsResponse,
    StatsInfo,
    CategoryInfo,
    SourceInfo,
    SearchSuggestion,
    ArticleCategory,
    TimeFilter,
    SortOption,
)
from .utils import ArticleTransformer, CategoryClassifier, TagExtractor, cache_manager


# ==================== 工具类实例 ====================

article_transformer = ArticleTransformer()
category_classifier = CategoryClassifier()
tag_extractor = TagExtractor()


# ==================== 路由 ====================

router = APIRouter(prefix="/api/v2", tags=["📡 API v2 - 前端适配"])


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def get_articles_dir() -> Path:
    """获取文章目录"""
    return get_project_root() / "ai" / "articles" / "summary"


def load_articles_with_cache(time_range: TimeFilter) -> List[ArticleModel]:
    """
    加载文章（带缓存）

    Args:
        time_range: 时间范围

    Returns:
        文章列表
    """
    cache_key = f"articles_{time_range.value}"

    def fetch_articles() -> List[ArticleModel]:
        articles: List[ArticleModel] = []
        articles_dir = get_articles_dir()

        if time_range in [TimeFilter.week, TimeFilter.month]:
            days = 7 if time_range == TimeFilter.week else 30
            for i in range(days):
                check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                date_dir = articles_dir / check_date

                if date_dir.exists():
                    for filepath in date_dir.glob("*.md"):
                        article = article_transformer.transform_from_file(filepath)
                        if article:
                            articles.append(article)
        else:
            target_date = (datetime.now() - timedelta(days=0)).strftime("%Y-%m-%d")
            date_dir = articles_dir / target_date

            if not date_dir.exists():
                target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                date_dir = articles_dir / target_date

            if date_dir.exists():
                for filepath in date_dir.glob("*.md"):
                    article = article_transformer.transform_from_file(filepath)
                    if article:
                        articles.append(article)

        return articles

    # 使用缓存获取文章
    return cache_manager.get_or_set(cache_key, fetch_articles, get_project_root())


def get_date_range(time_range: TimeFilter) -> tuple[str, str]:
    """
    根据时间范围获取日期区间

    Returns:
        (start_date, end_date)
    """
    today = datetime.now()

    if time_range == TimeFilter.today:
        return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif time_range == TimeFilter.yesterday:
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
    elif time_range == TimeFilter.week:
        week_ago = today - timedelta(days=7)
        return week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif time_range == TimeFilter.month:
        month_ago = today - timedelta(days=30)
        return month_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def filter_articles(
    articles: List[ArticleModel],
    keyword: Optional[str],
    sources: Optional[List[str]],
    tags: Optional[List[str]]
) -> List[ArticleModel]:
    """
    筛选文章

    Args:
        articles: 文章列表
        keyword: 关键词
        sources: 来源列表
        tags: 标签列表

    Returns:
        筛选后的文章列表
    """
    filtered = articles

    # 关键词筛选
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            article for article in filtered
            if keyword_lower in article.title.lower() or
               keyword_lower in article.summary.lower()
        ]

    # 来源筛选
    if sources:
        sources_lower = [s.lower() for s in sources]
        filtered = [
            article for article in filtered
            if article.source.lower() in sources_lower
        ]

    # 标签筛选
    if tags:
        filtered = [
            article for article in filtered
            if any(tag.lower() in [t.lower() for t in article.tags] for tag in tags)
        ]

    return filtered


def sort_articles(
    articles: List[ArticleModel],
    sort_by: SortOption
) -> List[ArticleModel]:
    """
    排序文章

    Args:
        articles: 文章列表
        sort_by: 排序方式

    Returns:
        排序后的文章列表
    """
    if sort_by == SortOption.hot:
        return sorted(articles, key=lambda a: a.viewCount, reverse=True)
    elif sort_by == SortOption.newest:
        return sorted(articles, key=lambda a: a.publishedAt, reverse=True)
    elif sort_by == SortOption.comments:
        return sorted(articles, key=lambda a: a.commentCount, reverse=True)
    else:  # relevant - 默认按浏览数
        return sorted(articles, key=lambda a: a.viewCount, reverse=True)


def paginate_articles(
    articles: List[ArticleModel],
    page: int,
    page_size: int
) -> ArticleListResponse:
    """
    分页文章

    Args:
        articles: 文章列表
        page: 页码
        page_size: 每页数量

    Returns:
        分页响应
    """
    total = len(articles)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = articles[start:end]

    return ArticleListResponse(
        date=datetime.now().strftime("%Y-%m-%d"),
        timeRange="today",
        total=total,
        page=page,
        pageSize=page_size,
        articles=paginated
    )


# ==================== 端点 ====================

@router.get("/articles", response_model=ArticleListDataResponse)
async def get_articles_v2(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    timeRange: TimeFilter = Query(TimeFilter.today, description="时间范围"),
    sources: Optional[List[str]] = Query(None, description="来源列表"),
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    sortBy: SortOption = Query(SortOption.hot, description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    📝 获取文章列表（API v2）

    支持完整的前端筛选和排序功能。

    **参数说明**:
    - `keyword`: 关键词搜索，匹配标题和摘要
    - `timeRange`: 时间范围，today/yesterday/week/month
    - `sources`: 来源列表，如 openai,google,anthropic
    - `tags`: 标签列表，如 LLM,GPT-4,AI绘画
    - `sortBy`: 排序方式，hot/newest/relevant/comments
    - `page`: 页码，从 1 开始
    - `pageSize`: 每页数量，最大 100

    **返回数据**:
    - 完整的 Article 对象，包含 id, category, tags, viewCount 等
    """
    # 收集文章文件
    articles: List[ArticleModel] = []
    articles_dir = get_articles_dir()

    if timeRange in [TimeFilter.week, TimeFilter.month]:
        # 多日期聚合
        days = 7 if timeRange == TimeFilter.week else 30
        for i in range(days):
            check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            date_dir = articles_dir / check_date

            if date_dir.exists():
                for filepath in date_dir.glob("*.md"):
                    article = article_transformer.transform_from_file(filepath)
                    if article:
                        articles.append(article)
    else:
        # 单日期 - 从今天开始尝试，最多回溯 7 天
        found_data = False
        for days_back in range(7):
            target_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            date_dir = articles_dir / target_date

            if date_dir.exists():
                for filepath in date_dir.glob("*.md"):
                    article = article_transformer.transform_from_file(filepath)
                    if article:
                        articles.append(article)
                found_data = True
                break

        if not found_data:
            # 如果没有找到任何数据，尝试加载所有可用数据
            for date_dir in sorted(articles_dir.iterdir(), reverse=True):
                if date_dir.is_dir():
                    for filepath in date_dir.glob("*.md"):
                        article = article_transformer.transform_from_file(filepath)
                        if article:
                            articles.append(article)

    # 筛选
    filtered_articles = filter_articles(articles, keyword, sources, tags)

    # 排序
    sorted_articles = sort_articles(filtered_articles, sortBy)

    # 分页
    result = paginate_articles(sorted_articles, page, pageSize)
    result.timeRange = timeRange.value
    result.date = datetime.now().strftime("%Y-%m-%d")

    return ArticleListDataResponse(success=True, data=result)


@router.get("/suggestions", response_model=SuggestionsDataResponse)
async def get_suggestions(
    q: Optional[str] = Query(None, description="查询词")
):
    """
    🔍 获取搜索建议

    返回热门搜索和最近搜索的建议。
    """
    # 热门搜索（预定义）
    trending = [
        SearchSuggestion(text="GPT-4", icon="🤖"),
        SearchSuggestion(text="Claude", icon="🧠"),
        SearchSuggestion(text="AI绘画", icon="🎨"),
        SearchSuggestion(text="多模态模型", icon="👁️"),
        SearchSuggestion(text="Agent工作流", icon="🤝"),
        SearchSuggestion(text="开源项目", icon="🔓"),
    ]

    # 最近搜索（模拟）
    recent = [
        SearchSuggestion(text="Cursor IDE", icon="⌨️"),
        SearchSuggestion(text="Gemini Ultra", icon="🔍"),
    ]

    # 如果有查询词，搜索匹配的标签
    if q:
        matching_tags = tag_extractor.search_tags(q, limit=5)
        if matching_tags:
            trending = [
                SearchSuggestion(text=tag['name'], icon=tag['emoji'])
                for tag in matching_tags
            ]

    return SuggestionsDataResponse(
        success=True,
        data=SuggestionsResponse(trending=trending, recent=recent)
    )


@router.get("/categories", response_model=CategoriesDataResponse)
async def get_categories():
    """
    📋 获取分类列表

    返回所有可用的文章分类。
    """
    categories = [
        CategoryInfo(
            id=ArticleCategory.hot,
            name="热门",
            emoji="🔥",
            description="高热度内容"
        ),
        CategoryInfo(
            id=ArticleCategory.deep,
            name="深度",
            emoji="📰",
            description="深度研究内容"
        ),
        CategoryInfo(
            id=ArticleCategory.new,
            name="新品",
            emoji="🆕",
            description="最新发布内容"
        ),
        CategoryInfo(
            id=ArticleCategory.breaking,
            name="突发",
            emoji="⚡",
            description="突发新闻"
        ),
    ]

    return CategoriesDataResponse(success=True, data=categories)


@router.get("/sources", response_model=SourcesDataResponse)
async def get_sources():
    """
    📋 获取来源列表

    返回所有数据来源及其文章数量。
    """
    # 收集实际来源
    sources = {}
    articles_dir = get_articles_dir()

    # 检查所有可用的数据目录
    for date_dir in sorted(articles_dir.iterdir(), reverse=True):
        if date_dir.is_dir():
            for filepath in date_dir.glob("*.md"):
                article = article_transformer.transform_from_file(filepath)
                if article:
                    source = article.source
                    if source not in sources:
                        sources[source] = {
                            'id': source,
                            'name': source.replace('-', ' ').title(),
                            'count': 0
                        }
                    sources[source]['count'] += 1

    # 转换为列表并排序
    sources_list = [
        SourceInfo(**info)
        for info in sorted(sources.values(), key=lambda x: -x['count'])
    ]

    return SourcesDataResponse(success=True, data=sources_list)


@router.get("/stats", response_model=StatsDataResponse)
async def get_stats():
    """
    📊 获取统计信息

    返回今日和总计的统计信息。
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # 收集文章数据
    total_articles = 0
    today_articles = 0
    total_sources = set()

    articles_dir = get_articles_dir()

    # 检查所有可用的数据目录
    for date_dir in sorted(articles_dir.iterdir(), reverse=True):
        if date_dir.is_dir():
            for filepath in date_dir.glob("*.md"):
                article = article_transformer.transform_from_file(filepath)
                if article:
                    total_articles += 1
                    total_sources.add(article.source)

                    if article.publishedAt.startswith(today):
                        today_articles += 1

    # 生成统计数据
    today_stats = StatsInfo(
        date=today,
        articles=today_articles,
        views=today_articles * random.randint(100, 300),
        comments=today_articles * random.randint(5, 20)
    )

    total_stats = StatsInfo(
        date=today,
        articles=total_articles,
        views=total_articles * random.randint(150, 400),
        comments=total_articles * random.randint(10, 50)
    )

    return StatsDataResponse(
        success=True,
        data=StatsResponse(today=today_stats, total=total_stats)
    )


@router.get("/health")
async def health_check():
    """
    ❤️ 健康检查
    """
    return {
        "status": "ok",
        "service": "ai-daily-collector-api-v2",
        "version": "2.0.0"
    }
