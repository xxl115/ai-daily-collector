#!/usr/bin/env python3
"""
Unified storage adapter interface (skeleton).
The goal is to abstract away the persistence layer so we can swap D1 with
local SQLite/PostgreSQL during tests or early-stage development.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

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
    def fetch_articles(self, filters: dict) -> List[ArticleModel]:
        pass


class LocalDBAdapter(StorageAdapter):
    """Simple in-memory DB adapter as a Local fallback for tests.

    This is intentionally lightweight and feature-lens to allow tests and
    local development without requiring a real database. It stores articles
    in a dictionary keyed by article id.
    """
    def __init__(self, connection_string: str | None = None):
        self.conn = connection_string
        self._store: dict[str, ArticleModel] = {}

    def ensure_schema(self) -> None:
        # No-op for in-memory store
        pass

    def write_article(self, article: ArticleModel) -> None:
        # Basic write; if article without id, convert to string key
        key = getattr(article, "id", None) or str(len(self._store) + 1)
        self._store[str(key)] = article

    def upsert_article(self, article: ArticleModel) -> None:
        key = getattr(article, "id", None) or str(len(self._store) + 1)
        self._store[str(key)] = article

    def fetch_articles(self, filters: dict) -> List[ArticleModel]:
        # Very lightweight filtering by simple keys
        results = list(self._store.values())
        if not filters:
            return results
        # Simple filter examples: by source, by id
        source = filters.get("source")
        if source:
            results = [a for a in results if getattr(a, "source", None) == source]
        return results
