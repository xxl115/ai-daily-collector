import requests
import logging
import os
from typing import Optional

from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class JinaExtractor:
    """Jina Reader 降级提取器（通过 r.jina.ai 提取文本）"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY", "")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,
        exceptions=(requests.RequestException, TimeoutError),
        on_retry=lambda e, n: logger.warning(f"Jina 提取重试 {n}: {e}"),
    )
    def extract(self, url: str) -> Optional[str]:
        try:
            response = requests.get(
                f"https://r.jina.ai/{url}", headers=self.headers, timeout=30
            )
            if response.status_code == 200:
                text = response.text
                if len(text) > 100:
                    return text.strip()
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败 {url}: {e}")
            return None
