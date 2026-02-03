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
]
