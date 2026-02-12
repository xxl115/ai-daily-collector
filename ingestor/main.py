#!/usr/bin/env python3
"""Production-ready ingestion pipeline with D1 support."""
from __future__ import annotations

import argparse
import time
from typing import List, Dict, Any
from datetime import datetime

try:
    import yaml
except Exception:
    yaml = None

from ingestor.scrapers import (
    fetch_rss, fetch_newsnow, fetch_hackernews,
    fetch_devto, fetch_v2ex, fetch_reddit, fetch_arxiv
)
from ingestor.transformers.article_transformer import transform
from shared.models import ArticleModel
from config.config import load_config_from_env, get_storage_adapter
from utils.logging_config import (
    setup_logging,
    log_ingestion_start,
    log_ingestion_complete,
    log_ingestion_error
)


def _load_sources_config(path: str) -> List[Dict[str, Any]]:
    """Load sources configuration from YAML file."""
    if yaml is None:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            return config.get("sources", [])
    except FileNotFoundError:
        return []


def _fetch_from_source(src: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch articles from a single source based on its type."""
    source_type = src.get("type", "rss")
    filters = src.get("filters", {})
    
    if source_type == "rss":
        url = src.get("url")
        if url:
            return fetch_rss(url)
    
    elif source_type == "newsnow":
        return fetch_newsnow(
            platform_id=src.get("platform_id", "toutiao"),
            keyword=filters.get("keyword", ""),
            hours=filters.get("hours", 24),
            max_articles=filters.get("max_articles", 20)
        )
    
    elif source_type == "hackernews":
        return fetch_hackernews(
            keyword=filters.get("keyword", ""),
            hours=filters.get("hours", 24),
            max_articles=filters.get("max_articles", 30)
        )
    
    elif source_type == "devto":
        return fetch_devto("AI", filters.get("max_articles", 15))
    
    elif source_type == "v2ex":
        return fetch_v2ex(
            keyword=filters.get("keyword", ""),
            max_articles=filters.get("max_articles", 20)
        )
    
    elif source_type == "reddit":
        return fetch_reddit(
            subreddit=src.get("subreddit", "MachineLearning"),
            keyword=filters.get("keyword", ""),
            max_articles=filters.get("max_articles", 15)
        )
    
    elif source_type == "arxiv":
        return fetch_arxiv("cat:cs.AI", filters.get("max_articles", 15))
    
    elif source_type in ("ai_blogs", "tech_media", "podcast", "producthunt"):
        url = src.get("url")
        if url:
            return fetch_rss(url)
    
    elif source_type == "youtube":
        channel_id = src.get("channel_id")
        if channel_id:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            return fetch_rss(url)
    
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ingest",
        description="Production ingestion pipeline with D1 support"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/sources.yaml",
        help="Path to sources config YAML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without persisting data"
    )
    parser.add_argument(
        "--source-type",
        type=str,
        help="Only process specific source type"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Optional log file path"
    )
    args = parser.parse_args()

    app_config = load_config_from_env()
    
    logger = setup_logging(
        level=app_config.log_level,
        format_type=app_config.log_format,
        log_file=args.log_file
    )
    
    logger.info(
        "Ingestion pipeline started",
        extra={
            "environment": app_config.environment,
            "database_provider": app_config.database.provider,
            "config_file": args.config
        }
    )

    sources = _load_sources_config(args.config)
    
    if not sources:
        logger.error("No sources configured")
        return 1

    if args.source_type:
        sources = [s for s in sources if s.get("type") == args.source_type]
        logger.info(
            f"Filtered to {len(sources)} sources of type: {args.source_type}",
            extra={"source_type": args.source_type, "count": len(sources)}
        )

    try:
        storage = get_storage_adapter(app_config)
        if hasattr(storage, 'ensure_schema'):
            storage.ensure_schema()
        logger.info(f"Storage initialized: {app_config.database.provider}")
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        return 1

    articles_written = 0
    source_stats: Dict[str, int] = {}
    failed_sources: List[str] = []
    
    ingestion_start_time = time.time()

    for src in sources:
        if not src.get("enabled", True):
            continue
        
        source_name = src.get("name", "unknown")
        source_type = src.get("type", "unknown")
        
        source_start_time = time.time()
        log_ingestion_start(logger, source_name)
        
        try:
            items = _fetch_from_source(src)
            
            count = 0
            for it in items:
                try:
                    article = transform(it)
                    article_obj = (
                        article if isinstance(article, ArticleModel)
                        else ArticleModel(**article)
                    )
                    
                    if not args.dry_run:
                        storage.upsert_article(article_obj)
                        articles_written += 1
                        count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process article: {e}")
                    continue
            
            source_duration = (time.time() - source_start_time) * 1000
            source_stats[source_name] = count
            
            log_ingestion_complete(logger, source_name, count, source_duration)
            
        except Exception as e:
            failed_sources.append(source_name)
            log_ingestion_error(logger, source_name, e)
            continue

    total_duration = (time.time() - ingestion_start_time) * 1000
    
    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info(f"Total duration: {total_duration:.2f}ms")
    logger.info(f"Total articles written: {articles_written}")
    logger.info(f"Successful sources: {len(source_stats) - len(failed_sources)}")
    logger.info(f"Failed sources: {len(failed_sources)}")
    
    if failed_sources:
        logger.warning(f"Failed sources: {', '.join(failed_sources)}")
    
    for name, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  - {name}: {count} articles")
    
    return 0 if not failed_sources else 1


if __name__ == "__main__":
    raise SystemExit(main())
