import pytest
from datetime import datetime


def test_article_model_import():
    try:
        from shared.models import ArticleModel
    except Exception as e:
        raise AssertionError(f"Failed to import ArticleModel: {e}")
    assert ArticleModel is not None


def test_article_model_creation():
    from shared.models import ArticleModel

    now = datetime.utcnow()
    article = ArticleModel(
        id="test-123",
        title="Test Article",
        content="Test content",
        url="https://example.com/article",
        published_at=now,
        source="test",
        categories=["tech"],
        tags=["ai"],
        summary="Test summary",
        raw_markdown="# Test",
        ingested_at=now
    )

    assert article["id"] == "test-123"
    assert article["title"] == "Test Article"
    assert article["source"] == "test"


def test_rss_scraper_import():
    try:
        from ingestor.scrapers.rss_scraper import fetch_rss
    except Exception as e:
        raise AssertionError(f"Failed to import fetch_rss: {e}")
    assert callable(fetch_rss)


def test_article_transformer_import():
    try:
        from ingestor.transformers.article_transformer import transform
    except Exception as e:
        raise AssertionError(f"Failed to import transform: {e}")
    assert callable(transform)


def test_storage_adapter_import():
    try:
        from ingestor.storage.db import LocalDBAdapter
    except Exception as e:
        raise AssertionError(f"Failed to import LocalDBAdapter: {e}")

    adapter = LocalDBAdapter()
    assert adapter is not None


def test_local_db_adapter_basic():
    from ingestor.storage.db import LocalDBAdapter
    from shared.models import ArticleModel
    from datetime import datetime

    adapter = LocalDBAdapter()
    now = datetime.utcnow()

    article = ArticleModel(
        id="test-456",
        title="Test Article 2",
        content="Content",
        url="https://example.com/2",
        source="test",
        ingested_at=now
    )

    adapter.upsert_article(article)
    results = adapter.fetch_articles({})

    assert len(results) == 1
    assert results[0]["id"] == "test-456"


def test_api_dao_import():
    try:
        from api.storage.dao import ArticleDAO
    except Exception as e:
        raise AssertionError(f"Failed to import ArticleDAO: {e}")

    dao = ArticleDAO()
    assert dao is not None


def test_d1_client_import():
    try:
        from ingestor.storage.d1_client import D1Client
    except Exception as e:
        raise AssertionError(f"Failed to import D1Client: {e}")

    client = D1Client("account", "db", "token")
    assert client is not None
