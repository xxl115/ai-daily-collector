import requests
import logging
import os
from typing import Optional

from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class JinaExtractor:
    ERROR_KEYWORDS = [
        "error", "failed", "insufficient", "balance", "unauthorized",
        "forbidden", "rate limit", "quota", "exceeded", "payment"
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY", "")
        self.proxy_url = os.environ.get("JINA_PROXY_URL", "").rstrip("/") or ""
        mode = "proxy" if self.proxy_url else "direct"
        logger.info(f"JinaExtractor 初始化: mode={mode}")

    def _get_endpoint(self, url: str) -> str:
        if self.proxy_url:
            from urllib.parse import quote
            return f"{self.proxy_url}/extract?url={quote(url)}"
        return f"https://r.jina.ai/{url}"

    def _get_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _is_error_response(self, data: dict) -> bool:
        if "code" in data:
            code = data["code"]
            if isinstance(code, int):
                return code >= 400
            if isinstance(code, str) and code.lower() != "success":
                return True

        if "error" in data and data["error"]:
            return True

        if "name" in data and data["name"]:
            name = str(data["name"]).lower()
            if any(kw in name for kw in self.ERROR_KEYWORDS):
                return True

        if "status" in data:
            status = data["status"]
            if isinstance(status, int):
                return status >= 400

        return False

    def _extract_error_message(self, data: dict) -> str:
        for key in ["message", "detail", "readableMessage", "name"]:
            if key in data:
                return str(data[key])
        return str(data)

    def extract(self, url: str) -> Optional[str]:
        try:
            timeout = int(os.environ.get("JINA_TIMEOUT", "15"))
            endpoint = self._get_endpoint(url)
            headers = self._get_headers()

            response = requests.get(endpoint, headers=headers, timeout=timeout)

            if response.status_code != 200:
                logger.warning(f"Jina API 返回非 200: url={url}, status={response.status_code}")
                return None

            content_type = response.headers.get("content-type", "")
            text = ""

            if "application/json" in content_type:
                try:
                    data = response.json()

                    if self._is_error_response(data):
                        error_msg = self._extract_error_message(data)
                        logger.error(f"Jina API 返回错误: url={url}, error={error_msg}")
                        return None

                    if "data" in data:
                        data_val = data["data"]
                        if isinstance(data_val, dict):
                            text = data_val.get("content", "") or data_val.get("markdown", "")
                        elif isinstance(data_val, str):
                            text = data_val

                    if not text:
                        logger.warning(f"Jina 响应无有效内容: url={url}")
                        return None

                except Exception as e:
                    logger.warning(f"Jina JSON 解析失败: url={url}, error={e}")
                    text = response.text
            else:
                text = response.text

            if text and len(text) < 500:
                text_lower = text.lower()
                if any(kw in text_lower for kw in self.ERROR_KEYWORDS):
                    logger.warning(f"Jina 返回内容包含错误: url={url}")
                    return None

            if text and len(text) > 100:
                logger.info(f"Jina 提取成功: url={url}, length={len(text)}")
                return text.strip()

            logger.warning(f"Jina 返回内容过短: url={url}")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"Jina 超时: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Jina 请求失败: {url}, error={e}")
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败: {url}, error={e}")
            return None
