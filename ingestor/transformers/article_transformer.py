#!/usr/bin/env python3
"""
Article transformer skeleton.
Converts raw item dicts into ArticleModel-compatible dicts.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

try:
    from shared.models import ArticleModel
except Exception:
    class ArticleModel(dict):
        def __init__(self, **kwargs):
            super().__init__(kwargs)

def transform(raw_item: Dict[str, Any]) -> ArticleModel:
    now = datetime.utcnow()
    return ArticleModel(
        id=str(raw_item.get("id") or now.timestamp()),
        title=raw_item.get("title", ""),
        content=raw_item.get("content", ""),
        url=raw_item.get("url", ""),
        published_at=raw_item.get("published_at"),
        source=raw_item.get("source", ""),
        categories=[],
        tags=[],
        summary=raw_item.get("summary"),
        raw_markdown=raw_item.get("markdown"),
        ingested_at=now,
    )
