"""Daily hotspots routes for frontend integration."""

from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from config.config import load_config_from_env, get_storage_adapter
from api.storage.dao import ArticleDAO


# ==================== Pydantic Models ====================


class HotspotResponse(BaseModel):
    """Hotspot response model."""

    id: str
    title: str
    url: str
    summary: str | None = None
    published_at: str | None = None
    source: str
    categories: List[str]
    tags: List[str]
    relevance_score: float = 0.0


class DailyHotspotsResponse(BaseModel):
    """Daily hotspots response."""

    date: str
    hotspots: List[HotspotResponse]
    total: int
    updated_at: str


# ==================== Router ====================

router = APIRouter(prefix="/api/v2/daily", tags=["Daily Hotspots"])


def get_article_dao() -> ArticleDAO:
    """Get ArticleDAO with configured storage."""
    config = load_config_from_env()
    storage = get_storage_adapter(config)
    return ArticleDAO(storage_adapter=storage)


@router.get("/latest", response_model=DailyHotspotsResponse)
async def get_latest_hotspots(
    limit: int = Query(20, ge=1, le=100, description="Number of hotspots to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    dao: ArticleDAO = Depends(get_article_dao),
):
    """
    Get the latest AI hotspots from the past N hours.

    Returns articles sorted by relevance and recency.
    """
    try:
        # Calculate the cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Fetch recent articles
        articles = dao.fetch_articles(filters={}, limit=limit * 2, offset=0)

        # Filter and transform articles
        hotspots = []
        for article in articles:
            # Try to parse published_at if available
            pub_at_str = article.get("published_at")
            if pub_at_str:
                try:
                    pub_at = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00"))
                    if pub_at < cutoff_time:
                        continue
                except:
                    pass

            # Calculate relevance score (simple algorithm)
            score = 0.0
            title = article.get("title", "").lower()
            summary = (article.get("summary") or "").lower()
            content = (article.get("content") or "").lower()

            # Keywords that indicate high relevance
            high_value_keywords = [
                "gpt", "openai", "claude", "anthropic", "gemini", "llama",
                "发布", "推出", "launch", "release", "模型", "model",
                "突破", "breakthrough", "融资", "funding", "收购", "acquisition"
            ]
            for keyword in high_value_keywords:
                if keyword in title:
                    score += 2.0
                elif keyword in summary:
                    score += 1.0
                elif keyword in content:
                    score += 0.5

            # Recent articles get higher scores
            if article.get("ingested_at"):
                try:
                    ingested_at = datetime.fromisoformat(article["ingested_at"].replace("Z", "+00:00"))
                    hours_old = (datetime.utcnow() - ingested_at).total_seconds() / 3600
                    score += max(0, 10 - hours_old * 0.1)
                except:
                    pass

            hotspots.append(
                HotspotResponse(
                    id=article.get("id", ""),
                    title=article.get("title", ""),
                    url=article.get("url", ""),
                    summary=article.get("summary") or article.get("content", "")[:500],
                    published_at=article.get("published_at"),
                    source=article.get("source", ""),
                    categories=article.get("categories", []),
                    tags=article.get("tags", []),
                    relevance_score=round(score, 2),
                )
            )

        # Sort by relevance score and limit
        hotspots.sort(key=lambda h: h.relevance_score, reverse=True)
        hotspots = hotspots[:limit]

        return DailyHotspotsResponse(
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            hotspots=hotspots,
            total=len(hotspots),
            updated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hotspots: {str(e)}")


@router.get("/hotspots", response_model=DailyHotspotsResponse)
async def get_hotspots(
    limit: int = Query(20, ge=1, le=100, description="Number of hotspots"),
    dao: ArticleDAO = Depends(get_article_dao),
):
    """
    Alias for /latest endpoint.

    Returns today's AI hotspots.
    """
    return await get_latest_hotspots(limit=limit, hours=24, dao=dao)
