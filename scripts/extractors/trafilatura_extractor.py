import typing
import logging
from typing import Optional

from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class TrafilaturaExtractor:
    """Trafilatura-based content extractor (主方案)"""

    def __init__(self):
        self._module = None
        try:
            import trafilatura as _t
            self._module = _t
        except Exception:
            self._module = None

    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,
        exceptions=(TimeoutError, ConnectionError, OSError),
        on_retry=lambda e, n: logger.warning(f"提取重试 {n}: {e}")
    )
    def extract(self, url: str) -> Optional[str]:
        if not self._module:
            return None
        try:
            html = self._module.fetch_url(url)
            if not html:
                return None
            text = self._module.extract(
                html,
                target_language='zh',
                include_comments=False,
                include_tables=False,
                deduplicate=True
            )
            if text and len(text) > 100:
                return text.strip()
            return None
        except Exception as e:
            logger.error(f"提取失败 {url}: {e}")
            return None
