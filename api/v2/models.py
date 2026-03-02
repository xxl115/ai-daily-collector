"""
API v2 数据模型
适配前端 Article 类型定义
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 枚举类型 ====================


class ArticleCategory(str, Enum):
    """文章分类"""

    hot = "hot"  # 🔥 热门
    deep = "deep"  # 📰 深度
    new = "new"  # 🆕 新品
    breaking = "breaking"  # ⚡ 突发


class ArticleSource(str, Enum):
    """文章来源"""

    openai = "openai"
    google = "google"
    anthropic = "anthropic"
    mit = "mit"
    wired = "wired"
    verge = "verge"
    techcrunch = "techcrunch"
    product_hunt = "product-hunt"
    arxiv = "arxiv"


class TimeFilter(str, Enum):
    """时间筛选"""

    today = "today"
    yesterday = "yesterday"
    week = "week"
    month = "month"


class SortOption(str, Enum):
    """排序方式"""

    hot = "hot"  # 热度优先（viewCount 降序）
    newest = "newest"  # 最新发布（publishedAt 降序）
    relevant = "relevant"  # 相关性（匹配度）
    comments = "comments"  # 评论最多（commentCount 降序）


# ==================== 请求模型 ====================


class ArticleListRequest(BaseModel):
    """文章列表请求"""

    keyword: Optional[str] = Field(None, description="关键词搜索")
    timeRange: TimeFilter = Field(default=TimeFilter.today, description="时间范围")
    sources: Optional[List[str]] = Field(None, description="来源列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    sortBy: SortOption = Field(default=SortOption.hot, description="排序方式")
    page: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页数量")


# ==================== 响应模型 ====================


class ArticleModel(BaseModel):
    """文章数据模型（匹配前端 Article 类型）"""

    id: str = Field(..., description="文章唯一标识")
    title: str = Field(..., description="文章标题")
    summary: str = Field(..., description="中文总结")
    category: ArticleCategory = Field(..., description="文章分类")
    source: str = Field(..., description="来源（可以是自定义字符串）")
    publishedAt: str = Field(..., description="发布时间（ISO 8601）")
    viewCount: int = Field(default=0, ge=0, description="浏览数")
    commentCount: int = Field(default=0, ge=0, description="评论数")
    tags: List[str] = Field(default_factory=list, description="标签数组")
    url: Optional[str] = Field(None, description="原文链接")
    thumbnail: Optional[str] = Field(None, description="缩略图 URL（可选）")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "arxiv-a1b2c3d4",
                "title": "ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval",
                "summary": "本文提出ShotFinder，一种基于网络搜索的想象驱动开放域视频片段检索方法...",
                "category": "hot",
                "source": "arxiv",
                "publishedAt": "2026-02-10T14:30:00Z",
                "viewCount": 2340,
                "commentCount": 45,
                "tags": ["LLM", "视频", "研究"],
                "url": "http://arxiv.org/abs/260123456",
            }
        }


class ArticleListResponse(BaseModel):
    """文章列表响应"""

    date: str = Field(..., description="查询日期")
    timeRange: str = Field(..., description="时间范围")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    articles: List[ArticleModel] = Field(..., description="文章列表")


class SearchSuggestion(BaseModel):
    """搜索建议项"""

    text: str = Field(..., description="建议文本")
    icon: str = Field(..., description="图标 emoji")


class SuggestionsResponse(BaseModel):
    """搜索建议响应"""

    trending: List[SearchSuggestion] = Field(default_factory=list, description="热门搜索")
    recent: List[SearchSuggestion] = Field(default_factory=list, description="最近搜索")


class CategoryInfo(BaseModel):
    """分类信息"""

    id: ArticleCategory = Field(..., description="分类 ID")
    name: str = Field(..., description="分类名称")
    emoji: str = Field(..., description="图标 emoji")
    description: str = Field(..., description="描述")


class SourceInfo(BaseModel):
    """来源信息"""

    id: str = Field(..., description="来源 ID")
    name: str = Field(..., description="来源名称")
    count: int = Field(default=0, ge=0, description="文章数量")


class StatsInfo(BaseModel):
    """统计信息"""

    date: str = Field(..., description="日期")
    articles: int = Field(..., description="文章数量")
    views: Optional[int] = Field(None, description="浏览数")
    comments: Optional[int] = Field(None, description="评论数")


class StatsResponse(BaseModel):
    """统计响应"""

    today: StatsInfo = Field(..., description="今日统计")
    total: StatsInfo = Field(..., description="总计统计")


class BaseResponse(BaseModel):
    """基础响应"""

    success: bool = Field(default=True, description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")

    model_config = {"populate_by_name": True}


class ArticleListDataResponse(BaseResponse):
    """文章列表数据响应"""

    data: ArticleListResponse


class SuggestionsDataResponse(BaseResponse):
    """搜索建议数据响应"""

    data: SuggestionsResponse


class CategoriesDataResponse(BaseResponse):
    """分类列表数据响应"""

    data: List[CategoryInfo]


class SourcesDataResponse(BaseResponse):
    """来源列表数据响应"""

    data: List[SourceInfo]


class StatsDataResponse(BaseResponse):
    """统计数据响应"""

    data: StatsResponse
