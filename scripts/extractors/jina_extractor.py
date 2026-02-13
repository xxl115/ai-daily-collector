import requests
from typing import Optional


class JinaExtractor:
    """Jina Reader 降级提取器（通过 r.jina.ai 提取文本）"""

    def extract(self, url: str) -> Optional[str]:
        try:
            response = requests.get(
                f'https://r.jina.ai/{url}',
                timeout=30
            )
            if response.status_code == 200:
                text = response.text
                if len(text) > 100:
                    return text.strip()
            return None
        except Exception:
            return None
