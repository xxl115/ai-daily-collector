"""审计日志模块 - 记录系统操作审计日志"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """审计级别"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEvent:
    """审计事件"""

    def __init__(
        self,
        event_type: str,
        action: str,
        resource: str,
        user: str = "system",
        metadata: dict | None = None,
    ):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.action = action
        self.resource = resource
        self.user = user
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "action": self.action,
            "resource": self.resource,
            "user": self.user,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._file = None

    def _get_log_file(self):
        if self._file is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            log_path = self.log_dir / f"audit_{date_str}.jsonl"
            self._file = open(log_path, "a", encoding="utf-8")
        return self._file

    def log(self, event: AuditEvent):
        try:
            file = self._get_log_file()
            file.write(event.to_json() + "\n")
            file.flush()
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")

    def log_event(
        self,
        event_type: str,
        action: str,
        resource: str,
        user: str = "system",
        **metadata,
    ):
        event = AuditEvent(
            event_type=event_type,
            action=action,
            resource=resource,
            user=user,
            metadata=metadata,
        )
        self.log(event)

    def close(self):
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# 便捷函数
def audit_log(event_type: str, action: str, resource: str, **kwargs):
    get_audit_logger().log_event(event_type, action, resource, **kwargs)


# 预定义审计事件
def audit_article_created(article_id: str, url: str, source: str):
    audit_log(
        event_type="article",
        action="created",
        resource=article_id,
        url=url,
        source=source,
    )


def audit_article_failed(url: str, error: str):
    audit_log(
        event_type="article",
        action="failed",
        resource=url,
        error=error,
    )


def audit_extraction(url: str, success: bool, duration: float):
    audit_log(
        event_type="extraction",
        action="extract" if success else "extract_failed",
        resource=url,
        duration_seconds=duration,
    )


def audit_summarization(article_id: str, success: bool, duration: float):
    audit_log(
        event_type="summarization",
        action="summarize" if success else "summarize_failed",
        resource=article_id,
        duration_seconds=duration,
    )


def audit_classification(article_id: str, category: str):
    audit_log(
        event_type="classification",
        action="classified",
        resource=article_id,
        category=category,
    )


def audit_api_request(endpoint: str, method: str, status_code: int):
    audit_log(
        event_type="api",
        action="request",
        resource=f"{method} {endpoint}",
        status_code=status_code,
    )
