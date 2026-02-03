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

from .youtube import (
    YouTubeFetcher,
    youtube_fetcher,
    fetch_youtube_trending,
    fetch_youtube_search,
    fetch_youtube_ai_trending,
    fetch_youtube_hotspots,
    get_ai_channels,
    AI_CHANNELS,
)

from .podcasts import (
    PodcastFetcher,
    SpotifyFetcher,
    podcast_fetcher,
    spotify_fetcher,
    fetch_podcasts,
    fetch_ai_podcasts,
    fetch_podcast_hotspots,
    get_supported_podcasts,
    PODCASTS,
)

from .qbitai import (
    QbitaiFetcher,
    qbitai_fetcher,
    fetch_qbitai,
    fetch_qbitai_hotspots,
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
    
    # YouTube
    'YouTubeFetcher',
    'youtube_fetcher',
    'fetch_youtube_trending',
    'fetch_youtube_search',
    'fetch_youtube_ai_trending',
    'fetch_youtube_hotspots',
    'get_ai_channels',
    'AI_CHANNELS',
    
    # Podcasts
    'PodcastFetcher',
    'SpotifyFetcher',
    'podcast_fetcher',
    'spotify_fetcher',
    'fetch_podcasts',
    'fetch_ai_podcasts',
    'fetch_podcast_hotspots',
    'get_supported_podcasts',
    'PODCASTS',

    # Qbitai
    'QbitaiFetcher',
    'qbitai_fetcher',
    'fetch_qbitai',
    'fetch_qbitai_hotspots',
]


# 数据源统计
SOURCE_STATS = {
    "total_sources": (
        len(NEWSNOW_PLATFORMS) +  # NewsNow
        1 +  # V2EX
        len(DEFAULT_SUBREDDITS) +  # Reddit
        len(AI_BLOGS) +  # AI Blogs
        len(TECH_MEDIA) +  # Tech Media
        1 +  # YouTube (Trending)
        len(AI_CHANNELS) +  # YouTube Channels
        len(PODCASTS) +  # Podcasts
        1  # Qbitai
    ),
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
        "youtube": {
            "name": "YouTube",
            "count": 1 + len(AI_CHANNELS),
            "type": "html",
        },
        "podcasts": {
            "name": "播客",
            "count": len(PODCASTS),
            "type": "rss",
        },
        "qbitai": {
            "name": "量子位",
            "count": 1,
            "type": "api",
        },
    }
}


# ============================================================================
# 统一调度接口 - 根据 sources.yaml 配置调用对应的 fetcher
# ============================================================================

def fetch_by_config(source_config: dict) -> list:
    """
    根据 sources.yaml 中的配置调用对应的 fetcher

    Args:
        source_config: 单个数据源的配置字典，格式如下：
            {
                "name": "36氪",
                "type": "tech_media",
                "media_id": "36kr",
                "url": "https://36kr.com/feed/",
                "enabled": true,
                "language": "zh",
                "filters": {"max_articles": 30, ...}
            }

    Returns:
        采集到的文章列表
    """
    from utils.logger import get_logger
    logger = get_logger(__name__)

    source_type = source_config.get("type")
    filters = source_config.get("filters", {})
    limit = filters.get("max_articles", 20)

    try:
        if source_type == "tech_media":
            # 科技媒体（包括中文和英文）
            media_id = source_config.get("media_id")
            if media_id and media_id in TECH_MEDIA:
                # 优先尝试 RSS
                items = tech_media_fetcher.fetch_rss(media_id)
                if not items:
                    # 降级到 HTML 抓取
                    items = tech_media_fetcher.fetch_html(media_id)
                return items[:limit] if items else []
            else:
                logger.warning(f"未知的 media_id: {media_id}")
                return []

        elif source_type == "api":
            # API 类型（如量子位）
            keyword = filters.get("keyword", "AI")
            return fetch_qbitai(limit=limit, keyword=keyword)

        elif source_type == "v2ex":
            # V2EX
            return fetch_v2ex_hotspots(limit=limit)

        elif source_type == "newsnow":
            # NewsNow 中文热点
            platforms = source_config.get("platforms")
            return fetch_newsnow_hotspots(platforms=platforms, limit=limit)

        elif source_type == "reddit":
            # Reddit
            subreddits = source_config.get("subreddits")
            return fetch_reddit_hotspots(subreddits=subreddits, limit=limit)

        elif source_type == "ai_blogs":
            # AI 官方博客
            blog_ids = source_config.get("blog_ids")
            return fetch_ai_blog_hotspots(blog_ids=blog_ids, limit=limit)

        elif source_type == "hackernews":
            # Hacker News (使用 Firebase API)
            return _fetch_hacker_news(limit=limit, keyword_filter=filters.get("keyword", ""))

        else:
            logger.warning(f"未知的数据源类型: {source_type}")
            return []

    except Exception as e:
        logger.error(f"采集 {source_config.get('name', 'Unknown')} 失败: {e}")
        return []


def _fetch_hacker_news(limit: int = 30, keyword_filter: str = "") -> list:
    """
    抓取 Hacker News AI 相关文章

    使用 Hacker News Firebase API
    """
    import requests
    from datetime import datetime

    items = []
    try:
        # 获取 top stories
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        if resp.ok:
            ids = resp.json()[:50]  # 获取更多以便过滤
            keywords = [kw.strip().lower() for kw in keyword_filter.split("|") if kw.strip()]

            for story_id in ids:
                try:
                    story_resp = requests.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                        timeout=5
                    )
                    if story_resp.ok:
                        story = story_resp.json()
                        title = story.get("title", "")

                        # 关键词过滤
                        if keywords:
                            title_lower = title.lower()
                            if not any(kw in title_lower for kw in keywords):
                                continue

                        items.append({
                            "title": title,
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            "summary": "",
                            "source": "Hacker News",
                            "source_id": "hackernews",
                            "published_at": "",
                            "timestamp": datetime.fromtimestamp(story.get("time", 0)).isoformat() if story.get("time") else datetime.now().isoformat(),
                            "hot_score": story.get("score", 0),
                        })

                        if len(items) >= limit:
                            break
                except:
                    pass

    except Exception as e:
        logger.error(f"Hacker News 抓取失败: {e}")

    return items

