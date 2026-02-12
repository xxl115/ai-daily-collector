"""Data Access Object for API layer to query articles from storage."""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from shared.models import ArticleModel


class ArticleDAO:
    """DAO for querying articles from storage.

    This is a skeleton implementation that works with LocalDBAdapter.
    In production, this should connect to Cloudflare D1 via d1_client.
    """

    def __init__(self, storage_adapter=None):
        """Initialize DAO with a storage adapter.

        Args:
            storage_adapter: Storage adapter instance (e.g., LocalDBAdapter or D1Client wrapper)
        """
        self.storage = storage_adapter

    def fetch_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ArticleModel]:
        """Fetch articles with optional filtering and pagination.

        Args:
            filters: Optional filters (e.g., {'source': 'rss', 'category': 'tech'})
            limit: Maximum number of articles to return
            offset: Number of articles to skip

        Returns:
            List of ArticleModel instances
        """
        if self.storage is None:
            return []

        filters = filters or {}
        articles = self.storage.fetch_articles(filters)

        # Apply pagination
        start = offset
        end = offset + limit
        return articles[start:end]

    def fetch_article_by_id(self, article_id: str) -> Optional[ArticleModel]:
        """Fetch a single article by ID.

        Args:
            article_id: The unique article identifier

        Returns:
            ArticleModel instance or None if not found
        """
        if self.storage is None:
            return None

        # Query with filter by id
        articles = self.storage.fetch_articles({'id': article_id})
        if articles:
            return articles[0]
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about articles in storage.

        Returns:
            Dictionary with count, sources, etc.
        """
        if self.storage is None:
            return {'total': 0, 'sources': []}

        all_articles = self.storage.fetch_articles({})
        sources = set()
        for article in all_articles:
            source = getattr(article, 'source', None)
            if source:
                sources.add(source)

        return {
            'total': len(all_articles),
            'sources': list(sources)
        }
