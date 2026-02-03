# AI Daily Collector - 数据抓取模块

from .base import (
    FetcherStatus,
    FetcherType,
    FetcherConfig,
    FetchResult,
    BaseFetcher,
    FetcherRegistry,
    registry,
    fetcher,
)

from .newsnow import (
    NewsNowFetcher,
    NewsNowManager,
    newsnow_manager,
    fetch_newsnow_hotspots,
    SUPPORTED_PLATFORMS as NEWSNOW_PLATFORMS,
)

from .v2ex import (
    V2EXFetcher,
    V2EXManager,
    v2ex_manager,
    fetch_v2ex_hotspots,
)

from .reddit import (
    RedditFetcher,
    RedditManager,
    reddit_manager,
    fetch_reddit_hotspots,
    DEFAULT_SUBREDDITS,
)

from .ai_blogs import (
    AIBlogFetcher,
    ai_blog_fetcher,
    fetch_ai_blogs,
    fetch_ai_blog_hotspots,
    get_supported_blogs,
    BLOGS as AI_BLOGS,
)

from .tech_media import (
    TechMediaFetcher,
    tech_media_fetcher,
    fetch_tech_media,
    fetch_tech_media_hotspots,
    get_supported_media,
    MEDIA as TECH_MEDIA,
)

__all__ = [
    # Base
    'FetcherStatus',
    'FetcherType',
    'FetcherConfig',
    'FetchResult',
    'BaseFetcher',
    'FetcherRegistry',
    'registry',
    'fetcher',
    
    # NewsNow
    'NewsNowFetcher',
    'NewsNowManager',
    'newsnow_manager',
    'fetch_newsnow_hotspots',
    'NEWSNOW_PLATFORMS',
    
    # V2EX
    'V2EXFetcher',
    'V2EXManager',
    'v2ex_manager',
    'fetch_v2ex_hotspots',
    
    # Reddit
    'RedditFetcher',
    'RedditManager',
    'reddit_manager',
    'fetch_reddit_hotspots',
    'DEFAULT_SUBREDDITS',
    
    # AI Blogs
    'AIBlogFetcher',
    'ai_blog_fetcher',
    'fetch_ai_blogs',
    'fetch_ai_blog_hotspots',
    'get_supported_blogs',
    'AI_BLOGS',
    
    # Tech Media
    'TechMediaFetcher',
    'tech_media_fetcher',
    'fetch_tech_media',
    'fetch_tech_media_hotspots',
    'get_supported_media',
    'TECH_MEDIA',
]


# 数据源统计
SOURCE_STATS = {
    "total_sources": len(NEWSNOW_PLATFORMS) + 1 + 1 + len(DEFAULT_SUBREDDITS) + len(AI_BLOGS) + len(TECH_MEDIA),
    "by_category": {
        "newsnow": {
            "name": "NewsNow 中文热点",
            "count": len(NEWSNOW_PLATFORMS),
            "type": "api",
        },
        "v2ex": {
            "name": "V2EX",
            "count": 1,
            "type": "api",
        },
        "reddit": {
            "name": "Reddit",
            "count": len(DEFAULT_SUBREDDITS),
            "type": "api",
        },
        "ai_blogs": {
            "name": "AI 官方博客",
            "count": len(AI_BLOGS),
            "type": "rss/html",
        },
        "tech_media": {
            "name": "科技媒体",
            "count": len(TECH_MEDIA),
            "type": "rss/html",
        },
    }
}
