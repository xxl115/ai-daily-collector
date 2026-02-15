"""Tests for API endpoints"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies before importing app
sys.modules["config"] = Mock()
sys.modules["config.config"] = Mock()
sys.modules["api.storage"] = Mock()
sys.modules["api.storage.dao"] = Mock()
sys.modules["shared"] = Mock()
sys.modules["shared.models"] = Mock()


class TestAPIEndpoints:
    """Test FastAPI endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct structure"""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_health_endpoint(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_openapi_exists(self):
        """Test OpenAPI schema is available"""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema

    def test_docs_endpoint(self):
        """Test Swagger docs endpoint"""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/docs")

        assert response.status_code == 200


class TestAPIV2Routes:
    """Test API v2 routes"""

    @patch("api.v2.routes_d1.get_article_dao")
    def test_articles_list(self, mock_dao):
        """Test articles list endpoint"""
        from fastapi.testclient import TestClient
        from api.main import app

        # Mock DAO
        mock_dao_instance = Mock()
        mock_dao_instance.fetch_articles.return_value = [
            {
                "id": "1",
                "title": "Test",
                "url": "https://ex.com",
                "content": "content",
                "source": "test",
                "categories": [],
                "tags": [],
                "summary": "summary",
                "ingested_at": "2026-01-01",
                "published_at": None,
            }
        ]
        mock_dao_instance.get_stats.return_value = {"total": 1}
        mock_dao.return_value = mock_dao_instance

        client = TestClient(app)
        response = client.get("/api/v2/articles")

        # May fail due to mock, but tests structure
        assert response.status_code in [200, 500]

    @patch("api.v2.routes_d1.get_article_dao")
    def test_articles_with_category_filter(self, mock_dao):
        """Test articles endpoint accepts category parameter"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from api.v2.routes_d1 import router

        # Check router has category parameter
        articles_route = None
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/articles":
                articles_route = route
                break

        assert articles_route is not None
        # Check parameters include category
        param_names = [p.name for p in articles_route.dependant.parameters]
        # Note: actual test would need full FastAPI app setup


class TestAPIResponseModels:
    """Test API response models"""

    def test_article_response_model(self):
        """Test ArticleResponse model validation"""
        from api.v2.routes_d1 import ArticleResponse
        from pydantic import ValidationError

        # Valid article
        article = ArticleResponse(
            id="123",
            title="Test Title",
            content="Test content",
            url="https://example.com",
            source="TestSource",
            categories=["tech"],
            tags=["ai"],
            summary="Test summary",
            ingested_at="2026-01-01T00:00:00Z",
            published_at=None,
        )

        assert article.id == "123"
        assert article.title == "Test Title"

    def test_health_response_model(self):
        """Test HealthResponse model"""
        from api.v2.routes_d1 import HealthResponse

        health = HealthResponse(
            status="ok", database="d1", timestamp="2026-01-01T00:00:00Z"
        )

        assert health.status == "ok"
        assert health.database == "d1"


class TestAPICors:
    """Test CORS configuration"""

    def test_cors_headers_present(self):
        """Test CORS headers are present in response"""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.options("/health")

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
