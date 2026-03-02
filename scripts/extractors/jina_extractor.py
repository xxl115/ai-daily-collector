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

        # 记录初始化信息
        mode = "proxy" if self.proxy_url else "direct"
        logger.info(f"JinaExtractor 初始化: mode={mode}, proxy_url={self.proxy_url[:50] if self.proxy_url else 'none'}...")

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

            logger.info(f"Jina 请求: url={url}, endpoint={endpoint[:80]}..., timeout={timeout}")

            response = requests.get(endpoint, headers=headers, timeout=timeout)

            logger.info(f"Jina 响应: url={url}, status={response.status_code}, content_type={response.headers.get('content-type', 'none')}")

            # 记录响应体前 200 字符，方便排查问题
            response_preview = response.text[:200]
            logger.info(f"Jina 响应体预览: url={url}, body={response_preview}")

            # 检查 HTTP 状态码，非 200 时返回 None
            if response.status_code != 200:
                logger.warning(
                    f"Jina API 返回非 200 状态码: url={url}, status={response.status_code}, body={response.text[:200]}"
                )
                return None

            content_type = response.headers.get("content-type", "")
            text = ""
            if "application/json" in content_type:
                try:
                    data = response.json()
                    logger.debug(f"Jina JSON 响应: url={url}, keys={list(data.keys())}")

                    # 检查 API 错误响应（code 字段）
                    if "code" in data and data["code"] != "Success":
                        error_detail = data.get("detail", data.get("message", "Unknown error"))
                        logger.error(f"Jina API 返回错误: url={url}, code={data['code']}, detail={error_detail}")
                        return None

                    if "data" in data and isinstance(data["data"], dict):
                        text = data["data"].get("content", "") or data["data"].get(
                            "markdown", ""
                        )
                    elif "data" in data and isinstance(data["data"], str):
                            text = data["data"]
                    else:
                        # 没有预期的 data 字段，记录警告并返回 None
                        logger.warning(f"Jina 响应格式异常: url={url}, response={data}")
                        return None
                except Exception as e:
                    logger.warning(f"Jina JSON 解析失败: url={url}, error={e}")
                    text = response.text
            else:
                text = response.text

            if text and len(text) > 100:
                logger.info(f"Jina 提取成功: url={url}, content_length={len(text)}")
                return text.strip()
            logger.warning(f"Jina 返回内容过短 ({len(text)}): {url}")
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
