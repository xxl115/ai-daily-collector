# AI Daily Collector - 工具模块

from .logger import setup_logger, get_logger, LoggerMixin, logger
from .metrics import (
    MetricsCollector,
    metrics,
    CollectorMetrics,
    track_duration
)
from .helpers import (
    clean_filename,
    slugify,
    extract_domain,
    truncate_text,
    parse_date_string,
    format_duration,
    Timer,
    retry,
    read_json,
    write_json,
    format_file_size,
)
from .rss import (
    RSSGenerator,
    AtomGenerator,
    generate_rss_from_articles,
    generate_atom_from_articles,
)
from .notification import (
    PushPlatform,
    PushMessage,
    FeishuPusher,
    DingTalkPusher,
    WeWorkPusher,
    TelegramPusher,
    NotificationManager,
    notification_manager,
    send_daily_report,
)
from .filter import (
    WordGroup,
    KeywordFilter,
    keyword_filter,
    filter_articles,
    sort_by_hotness,
)
from .cache import (
    Cache,
    cache,
    cached,
    MemoryCache,
    DiskCache,
    RedisCache,
)
from .rate_limit import (
    RateLimiter,
    limiter,
    rate_limit,
    rate_limit_api,
    rate_limit_crawler,
    rate_limit_webhook,
    RateLimitConfig,
    RateLimitExceeded,
)
from .errors import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    BaseError,
    NetworkError,
    ParseError,
    AuthenticationError,
    RateLimitError,
    DataError,
    ConfigurationError,
    FallbackManager,
    fallback_manager,
    retry,
    with_fallback,
    fallback_return_default,
    fallback_return_empty,
    fallback_cache_last_success,
)
from .notion import (
    NotionClient,
    NotionSyncManager,
    NotionSyncStatus,
    notion_sync_manager,
    sync_to_notion,
    get_notion_status,
)

__all__ = [
    # Logger
    'setup_logger',
    'get_logger',
    'LoggerMixin',
    'logger',

    # Metrics
    'MetricsCollector',
    'metrics',
    'CollectorMetrics',
    'track_duration',

    # Helpers
    'clean_filename',
    'slugify',
    'extract_domain',
    'truncate_text',
    'parse_date_string',
    'format_duration',
    'Timer',
    'retry',
    'read_json',
    'write_json',
    'format_file_size',

    # RSS
    'RSSGenerator',
    'AtomGenerator',
    'generate_rss_from_articles',
    'generate_atom_from_articles',

    # Notification
    'PushPlatform',
    'PushMessage',
    'FeishuPusher',
    'DingTalkPusher',
    'WeWorkPusher',
    'TelegramPusher',
    'NotificationManager',
    'notification_manager',
    'send_daily_report',

    # Notion
    'NotionClient',
    'NotionSyncManager',
    'NotionSyncStatus',
    'notion_sync_manager',
    'sync_to_notion',
    'get_notion_status',

    # Filter
    'WordGroup',
    'KeywordFilter',
    'keyword_filter',
    'filter_articles',
    'sort_by_hotness',

    # Cache
    'Cache',
    'cache',
    'cached',
    'MemoryCache',
    'DiskCache',
    'RedisCache',

    # Rate Limit
    'RateLimiter',
    'limiter',
    'rate_limit',
    'rate_limit_api',
    'rate_limit_crawler',
    'rate_limit_webhook',
    'RateLimitConfig',
    'RateLimitExceeded',

    # Errors
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'BaseError',
    'NetworkError',
    'ParseError',
    'AuthenticationError',
    'RateLimitError',
    'DataError',
    'ConfigurationError',
    'FallbackManager',
    'fallback_manager',
    'retry',
    'with_fallback',
    'fallback_return_default',
    'fallback_return_empty',
    'fallback_cache_last_success',
]
