"""API v2 routes with D1 storage integration."""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from config.config import load_config_from_env, get_storage_adapter
from api.storage.dao import ArticleDAO
from shared.models import ArticleModel as SharedArticleModel


# ==================== Pydantic Models ====================


class ArticleResponse(BaseModel):
    """Article response model."""

    id: str
    title: str
    content: str
    url: str
    published_at: Optional[str]
    source: str
    categories: List[str]
    tags: List[str]
    summary: Optional[str]
    ingested_at: str


class ArticleListResponse(BaseModel):
    """Article list response."""

    total: int
    articles: List[ArticleResponse]
    page: int
    page_size: int


class SourceStats(BaseModel):
    """Source statistics."""

    source: str
    count: int


class StatsResponse(BaseModel):
    """Statistics response."""

    total_articles: int
    sources: List[SourceStats]
    last_updated: Optional[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    timestamp: str


# ==================== Dependencies ====================


def get_article_dao() -> ArticleDAO:
    """Get ArticleDAO with configured storage."""
    config = load_config_from_env()
    storage = get_storage_adapter(config)
    return ArticleDAO(storage_adapter=storage)


# ==================== Router ====================

router = APIRouter(prefix="/api/v2", tags=["API v2 - D1 Storage"])


@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category (1-8 or new)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    dao: ArticleDAO = Depends(get_article_dao),
):
    """Get articles with pagination, source and category filters."""
    filters = {}
    if source:
        filters["source"] = source
    if category:
        filters["category"] = category

    offset = (page - 1) * page_size

    try:
        articles = dao.fetch_articles(filters=filters, limit=page_size, offset=offset)

        article_responses = []
        for article in articles:
            article_responses.append(
                ArticleResponse(
                    id=article.get("id", ""),
                    title=article.get("title", ""),
                    content=article.get("content", ""),
                    url=article.get("url", ""),
                    published_at=article.get("published_at"),
                    source=article.get("source", ""),
                    categories=article.get("categories", []),
                    tags=article.get("tags", []),
                    summary=article.get("summary"),
                    ingested_at=article.get("ingested_at", ""),
                )
            )

        stats = dao.get_stats()
        total = stats.get("total", len(article_responses))

        return ArticleListResponse(
            total=total, articles=article_responses, page=page, page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(article_id: str, dao: ArticleDAO = Depends(get_article_dao)):
    """Get a single article by ID."""
    try:
        article = dao.fetch_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return ArticleResponse(
            id=article.get("id", ""),
            title=article.get("title", ""),
            content=article.get("content", ""),
            url=article.get("url", ""),
            published_at=article.get("published_at"),
            source=article.get("source", ""),
            categories=article.get("categories", []),
            tags=article.get("tags", []),
            summary=article.get("summary"),
            ingested_at=article.get("ingested_at", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_stats(dao: ArticleDAO = Depends(get_article_dao)):
    """Get database statistics."""
    try:
        stats = dao.get_stats()

        sources = [
            SourceStats(source=source, count=count)
            for source, count in stats.get("sources", {}).items()
        ]

        # Sort by count descending
        sources.sort(key=lambda x: x.count, reverse=True)

        return StatsResponse(
            total_articles=stats.get("total", 0),
            sources=sources,
            last_updated=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/sources", response_model=List[str])
async def get_sources(dao: ArticleDAO = Depends(get_article_dao)):
    """Get list of all sources."""
    try:
        stats = dao.get_stats()
        return list(stats.get("sources", {}).keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    config = load_config_from_env()

    try:
        # Try to connect to database
        storage = get_storage_adapter(config)
        if hasattr(storage, "get_stats"):
            storage.get_stats()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.utcnow().isoformat(),
    )


# ==================== Crawl Logs API ====================


class CrawlLogResponse(BaseModel):
    """Crawl log response model."""

    id: int
    source_name: str
    source_type: str
    articles_count: int
    duration_ms: int
    status: str
    error_message: Optional[str]
    crawled_at: str


class CrawlLogsResponse(BaseModel):
    """Crawl logs list response."""

    total: int
    logs: List[CrawlLogResponse]
    page: int
    page_size: int


class CrawlStatsResponse(BaseModel):
    """Crawl statistics response."""

    total_crawls: int
    status_counts: Dict[str, int]
    total_articles_captured: int
    avg_duration_ms: int


@router.get("/crawl-logs", response_model=CrawlLogsResponse)
async def get_crawl_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    dao: ArticleDAO = Depends(get_article_dao),
):
    """Get crawl logs with pagination."""
    try:
        storage = dao.storage
        if not hasattr(storage, "get_crawl_logs"):
            raise HTTPException(status_code=501, detail="Crawl logs not supported")

        offset = (page - 1) * page_size
        logs = storage.get_crawl_logs(limit=page_size, offset=offset)

        log_responses = []
        for log in logs:
            log_responses.append(
                CrawlLogResponse(
                    id=log.get("id", 0),
                    source_name=log.get("source_name", ""),
                    source_type=log.get("source_type", ""),
                    articles_count=log.get("articles_count", 0),
                    duration_ms=log.get("duration_ms", 0),
                    status=log.get("status", ""),
                    error_message=log.get("error_message"),
                    crawled_at=log.get("crawled_at", ""),
                )
            )

        return CrawlLogsResponse(
            total=len(log_responses),
            logs=log_responses,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/crawl-stats", response_model=CrawlStatsResponse)
async def get_crawl_stats(dao: ArticleDAO = Depends(get_article_dao)):
    """Get crawl statistics."""
    try:
        storage = dao.storage
        if not hasattr(storage, "get_crawl_stats"):
            raise HTTPException(status_code=501, detail="Crawl stats not supported")

        stats = storage.get_crawl_stats()

        return CrawlStatsResponse(
            total_crawls=stats.get("total_crawls", 0),
            status_counts=stats.get("status_counts", {}),
            total_articles_captured=stats.get("total_articles_captured", 0),
            avg_duration_ms=stats.get("avg_duration_ms", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
