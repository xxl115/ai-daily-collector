import requests
from typing import Optional


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
            return text[:200]
        except Exception:
            return text[:200]
