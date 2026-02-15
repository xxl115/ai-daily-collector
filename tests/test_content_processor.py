"""Tests for scripts/content_processor.py"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestContentProcessor:
    """Test ContentProcessor class"""

    def test_init(self):
        """Test ContentProcessor initialization"""
        from scripts.content_processor import ContentProcessor

        processor = ContentProcessor(max_articles=10)

        assert processor.max_articles == 10
        assert processor.extractor is not None
        assert processor.summarizer is not None
        assert processor.classifier is not None

    def test_detect_source(self):
        """Test source detection from URL"""
        from scripts.content_processor import ContentProcessor

        processor = ContentProcessor()

        assert processor._detect_source("https://36kr.com/news") == "36氪"
        assert (
            processor._detect_source("https://news.ycombinator.com/item?id=123")
            == "Hacker News"
        )
        assert processor._detect_source("https://arxiv.org/abs/2301.12345") == "ArXiv"
        assert processor._detect_source("https://unknown-site.com") == "其他"

    def test_init_metrics(self):
        """Test metrics initialization"""
        from scripts.content_processor import ContentProcessor

        processor = ContentProcessor()
        metrics = processor._init_metrics()

        assert metrics["pages_processed"] == 0
        assert metrics["duplicates_skipped"] == 0
        assert isinstance(metrics["category_counts"], dict)
        assert isinstance(metrics["processing_times"], list)

    @patch("scripts.content_processor.TrafilaturaExtractor")
    @patch("scripts.content_processor.JinaExtractor")
    @patch("scripts.content_processor.OllamaSummarizer")
    @patch("scripts.content_processor.BGEClassifier")
    @patch("scripts.content_processor.ReportGenerator")
    def test_process_article_returns_dict(
        self, mock_report, mock_classifier, mock_summarizer, mock_jina, mock_traf
    ):
        """Test process_article returns proper dict structure"""
        from scripts.content_processor import ContentProcessor

        # Setup mocks
        mock_extractor = Mock()
        mock_extractor.extract.return_value = "Sample article content for testing"
        mock_traf.return_value = mock_extractor

        mock_fallback = Mock()
        mock_fallback.extract.return_value = None
        mock_jina.return_value = mock_fallback

        mock_sum = Mock()
        mock_sum.summarize.return_value = "Test summary"
        mock_summarizer.return_value = mock_sum

        mock_clf = Mock()
        mock_clf.classify.return_value = {"category": "new", "tags": ["test"]}
        mock_classifier.return_value = mock_clf

        processor = ContentProcessor()
        processor.extractor = mock_extractor

        result = processor.process_article("https://example.com", "Test Title")

        assert isinstance(result, dict)
        assert "id" in result
        assert "url" in result
        assert "title" in result
        assert "content" in result
        assert "summary" in result
        assert "category" in result
        assert "version" in result
        assert result["version"] == "v1"

    @patch("scripts.content_processor.TrafilaturaExtractor")
    @patch("scripts.content_processor.JinaExtractor")
    @patch("scripts.content_processor.OllamaSummarizer")
    @patch("scripts.content_processor.BGEClassifier")
    @patch("scripts.content_processor.ReportGenerator")
    def test_process_batch_empty(
        self, mock_report, mock_classifier, mock_summarizer, mock_jina, mock_traf
    ):
        """Test process_batch with empty input"""
        from scripts.content_processor import ContentProcessor

        processor = ContentProcessor()
        results = processor.process_batch([])

        assert results == []

    def test_seen_urls_persistence(self):
        """Test seen URLs are loaded and saved"""
        from scripts.content_processor import ContentProcessor

        # Create temp file for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ContentProcessor()
            processor._seen_path = Path(tmpdir) / "test_urls.json"

            # Add URL
            processor._seen_urls.add("https://example.com/1")
            processor._save_seen()

            # Create new processor - should load
            processor2 = ContentProcessor()
            processor2._seen_path = Path(tmpdir) / "test_urls.json"

            assert "https://example.com/1" in processor2._seen_urls


class TestDataContract:
    """Test data contract compliance"""

    def test_article_output_has_required_fields(self):
        """Test output has all required fields per contract"""
        from scripts.content_processor import ContentProcessor

        with patch("scripts.content_processor.TrafilaturaExtractor") as mock_extractor:
            with patch("scripts.content_processor.JinaExtractor"):
                with patch("scripts.content_processor.OllamaSummarizer") as mock_sum:
                    with patch("scripts.content_processor.BGEClassifier") as mock_clf:
                        with patch("scripts.content_processor.ReportGenerator"):
                            # Setup mocks
                            extractor = Mock()
                            extractor.extract.return_value = "Test content"
                            mock_extractor.return_value = extractor

                            summarizer = Mock()
                            summarizer.summarize.return_value = "Summary"
                            mock_sum.return_value = summarizer

                            classifier = Mock()
                            classifier.classify.return_value = {
                                "category": "1",
                                "tags": ["AI"],
                            }
                            mock_clf.return_value = classifier

                            processor = ContentProcessor()
                            result = processor.process_article("https://ex.com", "Test")

                            # Check required fields per ARCHITECTURE_ALL.md
                            required_fields = [
                                "id",
                                "url",
                                "title",
                                "content",
                                "summary",
                                "category",
                                "tags",
                                "source",
                                "extracted_at",
                                "processed_at",
                                "version",
                            ]

                            for field in required_fields:
                                assert field in result, (
                                    f"Missing required field: {field}"
                                )


class TestErrorHandling:
    """Test error handling and fallback"""

    def test_extractor_fallback(self):
        """Test extractor falls back to title on failure"""
        from scripts.content_processor import ContentProcessor

        with patch("scripts.content_processor.TrafilaturaExtractor") as mock_traf:
            with patch("scripts.content_processor.JinaExtractor") as mock_jina:
                with patch("scripts.content_processor.OllamaSummarizer") as mock_sum:
                    with patch("scripts.content_processor.BGEClassifier") as mock_clf:
                        with patch("scripts.content_processor.ReportGenerator"):
                            # Both extractors return None
                            traft = Mock()
                            traft.extract.return_value = None
                            mock_traf.return_value = traft

                            jina = Mock()
                            jina.extract.return_value = None
                            mock_jina.return_value = jina

                            summarizer = Mock()
                            summarizer.summarize.return_value = "summary"
                            mock_sum.return_value = summarizer

                            classifier = Mock()
                            classifier.classify.return_value = {
                                "category": "new",
                                "tags": [],
                            }
                            mock_clf.return_value = classifier

                            processor = ContentProcessor()
                            result = processor.process_article(
                                "https://ex.com", "Fallback Title"
                            )

                            # Should use title as content fallback
                            assert result["content"] == "Fallback Title"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
