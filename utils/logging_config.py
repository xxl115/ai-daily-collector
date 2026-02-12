"""Structured logging configuration."""
from __future__ import annotations

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra fields if present
        if hasattr(record, "source"):
            log_data["source"] = record.source
        if hasattr(record, "articles_count"):
            log_data["articles_count"] = record.articles_count
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Text log formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] {record.levelname}: {record.getMessage()}"


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: str | None = None
) -> logging.Logger:
    """Setup structured logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format_type: Log format type ("json" or "text")
        log_file: Optional file path for logging
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger("ai_daily_collector")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Choose formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_ingestion_start(logger: logging.Logger, source_name: str) -> None:
    """Log ingestion start event."""
    extra = {"source": source_name}
    logger.info(f"Starting ingestion from {source_name}", extra=extra)


def log_ingestion_complete(
    logger: logging.Logger,
    source_name: str,
    articles_count: int,
    duration_ms: float
) -> None:
    """Log ingestion completion event."""
    extra = {
        "source": source_name,
        "articles_count": articles_count,
        "duration_ms": duration_ms
    }
    logger.info(
        f"Completed ingestion from {source_name}: {articles_count} articles in {duration_ms:.2f}ms",
        extra=extra
    )


def log_ingestion_error(
    logger: logging.Logger,
    source_name: str,
    error: Exception
) -> None:
    """Log ingestion error event."""
    extra = {
        "source": source_name,
        "error_type": type(error).__name__
    }
    logger.error(
        f"Error ingesting from {source_name}: {error}",
        extra=extra,
        exc_info=True
    )


def log_storage_operation(
    logger: logging.Logger,
    operation: str,
    articles_count: int,
    duration_ms: float
) -> None:
    """Log storage operation event."""
    extra = {
        "operation": operation,
        "articles_count": articles_count,
        "duration_ms": duration_ms
    }
    logger.info(
        f"Storage {operation}: {articles_count} articles in {duration_ms:.2f}ms",
        extra=extra
    )
