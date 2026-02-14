import requests
import logging
from typing import Optional

from utils.retry import retry_with_fixed_interval

logger = logging.getLogger(__name__)


class OllamaSummarizer:
    """Ollama LLM 摘要生成器"""

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.model = "qwen2.5:1.5b"
        self.prompt_template = """请用50字以内概括以下内容，突出核心信息：

{}

要求：
1. 用中文输出
2. 简洁明了
3. 直接输出摘要，不要前缀

摘要："""

    @retry_with_fixed_interval(
        max_retries=2,
        interval=3.0,
        exceptions=(requests.RequestException, TimeoutError, ConnectionError),
        on_retry=lambda e, n: logger.warning(f"Ollama 重试 {n}: {e}")
    )
    def summarize(self, text: str) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self.prompt_template.format(text[:2000]),
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 100
                    }
                },
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            logger.warning(f"Ollama 返回状态码 {response.status_code}")
            return text[:200]
        except Exception as e:
            logger.error(f"Ollama 摘要生成失败: {e}")
            return text[:200]
