"""Tests for utils/audit.py"""

import pytest
import json
import tempfile
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.audit import (
    AuditLogger,
    AuditEvent,
    AuditLevel,
    audit_log,
    audit_article_created,
    audit_extraction,
)


class TestAuditEvent:
    """Test AuditEvent class"""

    def test_create_event(self):
        """Test creating an audit event"""
        event = AuditEvent(
            event_type="test",
            action="created",
            resource="resource-123",
            user="test-user",
            metadata={"key": "value"},
        )

        assert event.event_type == "test"
        assert event.action == "created"
        assert event.resource == "resource-123"
        assert event.user == "test-user"
        assert event.metadata["key"] == "value"

    def test_to_dict(self):
        """Test converting event to dictionary"""
        event = AuditEvent(event_type="article", action="created", resource="abc-123")

        d = event.to_dict()
        assert d["event_type"] == "article"
        assert d["action"] == "created"
        assert d["resource"] == "abc-123"
        assert "timestamp" in d

    def test_to_json(self):
        """Test converting event to JSON"""
        event = AuditEvent(event_type="test", action="action", resource="res")

        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "test"


class TestAuditLogger:
    """Test AuditLogger class"""

    def test_log_to_file(self):
        """Test logging events to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            event = AuditEvent(event_type="test", action="created", resource="res-1")
            logger.log(event)

            # Check file was created
            files = list(Path(tmpdir).glob("audit_*.jsonl"))
            assert len(files) == 1

            # Check content
            content = files[0].read_text()
            assert "test" in content
            assert "created" in content

            logger.close()

    def test_log_event_method(self):
        """Test log_event convenience method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log_event(
                event_type="article",
                action="created",
                resource="article-123",
                url="https://example.com",
                source="test",
            )

            files = list(Path(tmpdir).glob("audit_*.jsonl"))
            content = files[0].read_text()
            assert "article" in content
            assert "article-123" in content

            logger.close()

    def test_context_manager(self):
        """Test using logger as context manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with AuditLogger(log_dir=tmpdir) as logger:
                logger.log_event("test", "action", "res")

            files = list(Path(tmpdir).glob("audit_*.jsonl"))
            assert len(files) == 1


class TestAuditPresetFunctions:
    """Test preset audit functions"""

    def test_audit_article_created(self):
        """Test audit_article_created function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from utils.audit import get_audit_logger

            logger = AuditLogger(log_dir=tmpdir)

            # Monkey patch for test
            import utils.audit

            original_logger = utils.audit._audit_logger
            utils.audit._audit_logger = logger

            try:
                audit_article_created("art-123", "https://ex.com", "TestSource")

                files = list(Path(tmpdir).glob("audit_*.jsonl"))
                content = files[0].read_text()
                assert "art-123" in content
                assert "TestSource" in content
            finally:
                utils.audit._audit_logger = original_logger
                logger.close()

    def test_audit_extraction(self):
        """Test audit_extraction function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from utils.audit import get_audit_logger

            logger = AuditLogger(log_dir=tmpdir)

            import utils.audit

            original_logger = utils.audit._audit_logger
            utils.audit._audit_logger = logger

            try:
                audit_extraction("https://ex.com", True, 1.5)

                files = list(Path(tmpdir).glob("audit_*.jsonl"))
                content = files[0].read_text()
                assert "extraction" in content
                assert "1.5" in content
            finally:
                utils.audit._audit_logger = original_logger
                logger.close()


class TestAuditEventTypes:
    """Test different audit event types"""

    def test_audit_levels(self):
        """Test audit level enum"""
        assert AuditLevel.INFO.value == "INFO"
        assert AuditLevel.WARNING.value == "WARNING"
        assert AuditLevel.ERROR.value == "ERROR"
        assert AuditLevel.CRITICAL.value == "CRITICAL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
