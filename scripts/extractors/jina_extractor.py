import requests
import logging
import os
from typing import Optional

from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class JinaExtractor:
    """Jina Reader 提取器（使用 api.jina.ai v2 API）"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY", "")
        self.api_endpoint = "https://api.jina.ai/v1/extract"

    @retry_with_exponential_backoff(
        max_retries=1,
        initial_delay=1.0,
        exceptions=(requests.RequestException, TimeoutError),
        on_retry=lambda e, n: logger.warning(f"Jina 提取重试 {n}: {e}"),
    )
    def extract(self, url: str) -> Optional[str]:
        try:
            timeout = int(os.environ.get("JINA_TIMEOUT", "15"))
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {"url": url}
            response = requests.post(
                self.api_endpoint, json=payload, headers=headers, timeout=timeout
            )
            if response.status_code == 200:
                data = response.json()
                text = data.get("content", "")
                if text and len(text) > 100:
                    return text.strip()
            else:
                logger.warning(
                    f"Jina API 返回 {response.status_code}: {response.text[:200]}"
                )
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败 {url}: {e}")
            return None
