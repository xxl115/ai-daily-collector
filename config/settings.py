# AI Daily Collector - 统一配置
# 支持环境变量覆盖

from pathlib import Path
from typing import Optional
import os

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))


# API 配置
class APIConfig:
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 8000))
    debug = os.environ.get("API_DEBUG", "false").lower() == "true"
    cors_origins = os.environ.get("API_CORS_ORIGINS", "*").split(",")


# 智谱 AI 配置
class ZhipuConfig:
    api_key = os.environ.get("ZAI_API_KEY", "")
    api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    model = os.environ.get("ZAI_MODEL", "glm-4")
    max_tokens = int(os.environ.get("ZAI_MAX_TOKENS", 500))
    temperature = float(os.environ.get("ZAI_TEMPERATURE", 0.7))


# Notion 配置
class NotionConfig:
    api_key = os.environ.get("NOTION_API_KEY", "")
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID", "")


# GitHub 配置
class GitHubConfig:
    repo_url = os.environ.get("GITHUB_REPO_URL", "https://github.com/xxl115/ai-daily-collector")
    commit_message = os.environ.get("GITHUB_COMMIT_MSG", "📅 Daily update {date}")


# 采集配置
class CrawlerConfig:
    articles_hours_back = int(os.environ.get("ARTICLES_HOURS_BACK", 24))
    filter_ai_only = os.environ.get("FILTER_AI_ONLY", "true").lower() == "true"
    max_articles_per_source = int(os.environ.get("MAX_ARTICLES", 30))
    request_timeout = int(os.environ.get("REQUEST_TIMEOUT", 30))
    retry_times = int(os.environ.get("RETRY_TIMES", 3))


# 日报配置
class ReportConfig:
    focus_article_limit = 1
    category_article_limit = 5
    summary_length = {"focus": 150, "normal": 100}


# 日志配置
class LogConfig:
    level = os.environ.get("LOG_LEVEL", "INFO")
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path = DATA_DIR / "logs" / "app.log"


# 导出配置实例
config = type(
    "Config",
    (),
    {
        "api": APIConfig,
        "zhipu": ZhipuConfig,
        "notion": NotionConfig,
        "github": GitHubConfig,
        "crawler": CrawlerConfig,
        "report": ReportConfig,
        "log": LogConfig,
        "data_dir": DATA_DIR,
        "project_root": PROJECT_ROOT,
    },
)()


def get_source_config(name: str) -> Optional[dict]:
    """获取指定 RSS 源配置"""
    import yaml

    config_path = PROJECT_ROOT / "config" / "sources.yaml"

    if not config_path.exists():
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    for source in config_data.get("sources", []):
        if source.get("name") == name:
            return source

    return None
