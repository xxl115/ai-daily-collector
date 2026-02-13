import typing
from typing import Optional

class TrafilaturaExtractor:
    """Trafilatura-based content extractor (主方案)"""

    def __init__(self):
        # 在某些环境中 may not have trafilatura 安装，运行时会回退
        self._module = None
        try:
            import trafilatura as _t
            self._module = _t
        except Exception:
            self._module = None

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
        except Exception:
            return None
