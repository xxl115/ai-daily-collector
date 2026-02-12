#!/usr/bin/env python3
"""Shared data models (contract) for ingestion and API."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

try:
    from pydantic import BaseModel, Field

    class ArticleModel(BaseModel):
        id: str
        title: str
        content: str
        url: str
        published_at: Optional[datetime] = None
        source: str
        categories: List[str] = []
        tags: List[str] = []
        summary: Optional[str] = None
        raw_markdown: Optional[str] = None
        ingested_at: datetime
except Exception:
    # Fallback minimal dict-based structure if pydantic is unavailable
    class ArticleModel(dict):
        def __init__(self, **kwargs):
            super().__init__(kwargs)
