import requests
import logging
import os
from typing import Optional

from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class JinaExtractor:
    """Jina Reader 提取器（使用 r.jina.ai API，可选代理）"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY", "")
        # 支持自定义代理 URL（用于 Cloudflare Workers 等）
        self.proxy_url = os.environ.get("JINA_PROXY_URL", "").rstrip("/")

    def _get_endpoint(self, url: str) -> str:
        """获取提取端点"""
        if self.proxy_url:
            from urllib.parse import quote

            return f"{self.proxy_url}/extract?url={quote(url)}"
        return f"https://r.jina.ai/{url}"

    def _get_headers(self) -> dict:
        """获取请求头"""
        if self.proxy_url:
            # 代理模式不需要额外 header
            return {"Accept": "application/json"}

        # 直接访问 r.jina.ai
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def extract(self, url: str) -> Optional[str]:
        try:
            timeout = int(os.environ.get("JINA_TIMEOUT", "15"))
            endpoint = self._get_endpoint(url)
            headers = self._get_headers()

            response = requests.get(endpoint, headers=headers, timeout=timeout)

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                text = ""
                if "application/json" in content_type:
                    try:
                        data = response.json()
                        if "data" in data and isinstance(data["data"], dict):
                            text = data["data"].get("content", "") or data["data"].get(
                                "markdown", ""
                            )
                        elif "data" in data and isinstance(data["data"], str):
                            text = data["data"]
                        else:
                            text = str(data)
                    except Exception:
                        text = response.text
                else:
                    text = response.text

                if text and len(text) > 100:
                    return text.strip()
                logger.warning(f"Jina 返回内容过短 ({len(text)}): {url}")
            else:
                logger.warning(
                    f"Jina API 返回 {response.status_code}: {response.text[:200]}"
                )

            return None
        except requests.exceptions.Timeout:
            logger.error(f"Jina 超时 {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Jina 请求失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败 {url}: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Jina 超时 {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Jina 请求失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败 {url}: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Jina 超时 {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Jina 请求失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Jina 提取失败 {url}: {e}")
            return None
