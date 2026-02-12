#!/usr/bin/env python3
"""
Unified storage adapter interface.
Supports both D1 (production) and SQLite (local development).
"""
from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.models import ArticleModel


class StorageAdapter(ABC):
    @abstractmethod
    def ensure_schema(self) -> None:
        pass

    @abstractmethod
    def write_article(self, article: ArticleModel) -> None:
        pass

    @abstractmethod
    def upsert_article(self, article: ArticleModel) -> None:
        pass

    @abstractmethod
    def fetch_articles(self, filters: dict, limit: int = 50, offset: int = 0) -> List[ArticleModel]:
        pass


class LocalDBAdapter(StorageAdapter):
    """SQLite-based local storage adapter for development.
    
    Stores articles in a local SQLite file for persistence across restarts.
    """
    
    def __init__(self, connection_string: str | None = None):
        # Default to data/local.db if no connection string provided
        if connection_string:
            self.db_path = connection_string
        else:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "local.db")
        
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT NOT NULL,
                    published_at TEXT,
                    source TEXT,
                    categories TEXT,
                    tags TEXT,
                    summary TEXT,
                    raw_markdown TEXT,
                    ingested_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_source 
                ON articles(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_ingested_at 
                ON articles(ingested_at DESC)
            """)
            conn.commit()
    
    def ensure_schema(self) -> None:
        """Ensure database schema exists (called during initialization)."""
        self._init_db()
    
    def _article_to_row(self, article: ArticleModel) -> tuple:
        """Convert ArticleModel to database row."""
        return (
            article.id,
            article.title,
            article.content,
            article.url,
            article.published_at.isoformat() if article.published_at else None,
            article.source,
            json.dumps(article.categories) if article.categories else "[]",
            json.dumps(article.tags) if article.tags else "[]",
            article.summary,
            getattr(article, 'raw_markdown', None),
            article.ingested_at.isoformat() if article.ingested_at else datetime.now().isoformat(),
        )
    
    def _row_to_article(self, row: sqlite3.Row) -> ArticleModel:
        """Convert database row to ArticleModel."""
        return ArticleModel(
            id=row["id"],
            title=row["title"],
            content=row["content"] or "",
            url=row["url"],
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
            source=row["source"] or "",
            categories=json.loads(row["categories"]) if row["categories"] else [],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            summary=row["summary"],
            raw_markdown=row["raw_markdown"],
            ingested_at=datetime.fromisoformat(row["ingested_at"]) if row["ingested_at"] else datetime.now(),
        )
    
    def write_article(self, article: ArticleModel) -> None:
        """Write a new article to the database."""
        with self._get_connection() as conn:
            row = self._article_to_row(article)
            conn.execute("""
                INSERT INTO articles (
                    id, title, content, url, published_at, source,
                    categories, tags, summary, raw_markdown, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            conn.commit()
    
    def upsert_article(self, article: ArticleModel) -> None:
        """Insert or update an article."""
        with self._get_connection() as conn:
            row = self._article_to_row(article)
            conn.execute("""
                INSERT OR REPLACE INTO articles (
                    id, title, content, url, published_at, source,
                    categories, tags, summary, raw_markdown, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            conn.commit()
    
    def fetch_articles(self, filters: dict, limit: int = 50, offset: int = 0) -> List[ArticleModel]:
        """Fetch articles with optional filtering and pagination."""
        filters = filters or {}
        
        sql = "SELECT * FROM articles WHERE 1=1"
        params: List[Any] = []
        
        # Add filters
        if "source" in filters:
            sql += " AND source = ?"
            params.append(filters["source"])
        
        if "id" in filters:
            sql += " AND id = ?"
            params.append(filters["id"])
        
        # Order by ingestion time, newest first
        sql += " ORDER BY ingested_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_article(row) for row in rows]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            # Total count
            cursor = conn.execute("SELECT COUNT(*) as total FROM articles")
            total = cursor.fetchone()["total"]
            
            # Sources
            cursor = conn.execute(
                "SELECT source, COUNT(*) as count FROM articles GROUP BY source"
            )
            sources = {row["source"]: row["count"] for row in cursor.fetchall()}
            
            return {
                "total": total,
                "sources": sources,
            }
