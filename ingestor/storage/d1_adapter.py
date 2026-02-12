"""Cloudflare D1 storage adapter for production use."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import json
import urllib.request
import urllib.error
from datetime import datetime

from shared.models import ArticleModel
from ingestor.storage.db import StorageAdapter


class D1StorageAdapter(StorageAdapter):
    """Production storage adapter using Cloudflare D1.
    
    This adapter connects to Cloudflare D1 via the REST API
    and provides full CRUD operations for articles.
    """
    
    def __init__(
        self,
        account_id: str,
        database_id: str,
        api_token: str,
        base_url: str = "https://api.cloudflare.com/client/v4"
    ):
        """Initialize D1 storage adapter.
        
        Args:
            account_id: Cloudflare account ID
            database_id: D1 database ID
            api_token: Cloudflare API token with D1 read/write permissions
            base_url: Cloudflare API base URL
        """
        self.account_id = account_id
        self.database_id = database_id
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self._api_base = f"{self.base_url}/accounts/{self.account_id}/d1/database/{self.database_id}"
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    def _execute_sql(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute SQL query via D1 API.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self._api_base}/query"
        
        payload = {
            "sql": sql,
            "params": params or []
        }
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                
            if not result.get("success", False):
                errors = result.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
                raise Exception(f"D1 API error: {error_msg}")
                
            return result
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"D1 HTTP error {e.code}: {error_body}")
    
    def ensure_schema(self) -> None:
        """Create articles table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT NOT NULL,
            published_at TEXT,
            source TEXT NOT NULL,
            categories TEXT,
            tags TEXT,
            summary TEXT,
            raw_markdown TEXT,
            ingested_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create index for common queries
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
        """
        
        create_index_date_sql = """
        CREATE INDEX IF NOT EXISTS idx_articles_ingested_at ON articles(ingested_at);
        """
        
        self._execute_sql(create_table_sql)
        self._execute_sql(create_index_sql)
        self._execute_sql(create_index_date_sql)
    
    def _article_to_row(self, article: ArticleModel) -> tuple:
        """Convert ArticleModel to database row.
        
        Args:
            article: ArticleModel instance
            
        Returns:
            Tuple of values for INSERT/UPDATE
        """
        # Handle both dict-like and object-like access
        if isinstance(article, dict):
            get = article.get
        else:
            get = lambda key, default=None: getattr(article, key, default)
        
        categories = get("categories", [])
        tags = get("tags", [])
        
        # Convert lists to JSON strings
        categories_json = json.dumps(categories) if categories else "[]"
        tags_json = json.dumps(tags) if tags else "[]"
        
        published_at = get("published_at")
        if isinstance(published_at, datetime):
            published_at = published_at.isoformat()
        
        ingested_at = get("ingested_at")
        if isinstance(ingested_at, datetime):
            ingested_at = ingested_at.isoformat()
        
        return (
            get("id"),
            get("title"),
            get("content", ""),
            get("url"),
            published_at,
            get("source"),
            categories_json,
            tags_json,
            get("summary"),
            get("raw_markdown"),
            ingested_at or datetime.utcnow().isoformat()
        )
    
    def _row_to_article(self, row: Dict[str, Any]) -> ArticleModel:
        """Convert database row to ArticleModel.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            ArticleModel instance
        """
        # Parse JSON fields
        categories = json.loads(row.get("categories", "[]"))
        tags = json.loads(row.get("tags", "[]"))
        
        return ArticleModel(
            id=row["id"],
            title=row["title"],
            content=row.get("content", ""),
            url=row["url"],
            published_at=row.get("published_at"),
            source=row["source"],
            categories=categories,
            tags=tags,
            summary=row.get("summary"),
            raw_markdown=row.get("raw_markdown"),
            ingested_at=row["ingested_at"]
        )
    
    def write_article(self, article: ArticleModel) -> None:
        """Insert a new article.
        
        Args:
            article: Article to insert
        """
        sql = """
        INSERT INTO articles (
            id, title, content, url, published_at, source,
            categories, tags, summary, raw_markdown, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        row = self._article_to_row(article)
        self._execute_sql(sql, list(row))
    
    def upsert_article(self, article: ArticleModel) -> None:
        """Insert or update an article.
        
        Uses INSERT OR REPLACE for SQLite compatibility.
        
        Args:
            article: Article to upsert
        """
        sql = """
        INSERT OR REPLACE INTO articles (
            id, title, content, url, published_at, source,
            categories, tags, summary, raw_markdown, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        row = self._article_to_row(article)
        self._execute_sql(sql, list(row))
    
    def fetch_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ArticleModel]:
        """Fetch articles with optional filtering.
        
        Args:
            filters: Optional filters (source, id, etc.)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of ArticleModel instances
        """
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
        
        # Add ordering and pagination
        sql += " ORDER BY ingested_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        result = self._execute_sql(sql, params)
        
        # Parse results
        articles = []
        rows = result.get("result", [])
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    articles.append(self._row_to_article(row))
        
        return articles
    
    def get_article_by_id(self, article_id: str) -> Optional[ArticleModel]:
        """Get a single article by ID.
        
        Args:
            article_id: Article ID
            
        Returns:
            ArticleModel or None
        """
        sql = "SELECT * FROM articles WHERE id = ? LIMIT 1"
        result = self._execute_sql(sql, [article_id])
        
        rows = result.get("result", [])
        if rows and isinstance(rows, list) and len(rows) > 0:
            return self._row_to_article(rows[0])
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with total count and source breakdown
        """
        # Total count
        count_result = self._execute_sql("SELECT COUNT(*) as total FROM articles")
        total = 0
        if count_result.get("result"):
            total = count_result["result"][0].get("total", 0)
        
        # Source breakdown
        sources_result = self._execute_sql(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source"
        )
        sources = {}
        if sources_result.get("result"):
            for row in sources_result["result"]:
                sources[row["source"]] = row["count"]
        
        return {
            "total": total,
            "sources": sources
        }
    
    def delete_old_articles(self, days: int = 30) -> int:
        """Delete articles older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted rows
        """
        sql = "DELETE FROM articles WHERE ingested_at < datetime('now', '-' || ? || ' days')"
        result = self._execute_sql(sql, [days])
        
        # Try to get affected rows from meta
        meta = result.get("meta", {})
        return meta.get("changes", 0)
