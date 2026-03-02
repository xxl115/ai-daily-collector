"""
多方法回退内容提取器

按优先级尝试多种提取方法:
1. Trafilatura (首选) - 对中文网站效果最好
2. Jina Reader API (备用)
3. Newspaper4k (兜底)
"""

import logging
import os
import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def clean_content(text: str) -> str:
    """清理提取内容中的残留噪声"""
    if not text:
        return text

    # 移除常见噪声模式
    noise_patterns = [
        r"您正在使用IE低版浏览器.*?(?:浏览器|体验)",
        r"为了您的.*?账号安全",
        r"未经授权.*?转载",
        r"详情见.*?转载须知",
        r"雷锋网版权",
        r"爱搞机",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 清理多余空白
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


class MultiMethodExtractor:
    """多方法回退内容提取器"""

    # 支持的方法
    METHODS = ["trafilatura", "newspaper", "jina", "beautifulsoup"]

    # 中文科技媒体域名（优先使用特定方法）
    PRIORITY_DOMAINS = {
        "36kr.com": "jina",  # 36kr 反爬强，用 Jina
        "leiphone.com": "trafilatura",  # 雷峰网用 Trafilatura
        "jiqizhixin.com": "trafilatura",  # 机器之心
        "huxiu.com": "trafilatura",  # 虎嗅
        "ithome.com": "trafilatura",  # IT之家
    }

    def __init__(self, use_proxy: bool = False):
        self.use_proxy = use_proxy
        self._trafilatura = None
        self._newspaper = None
        self._jina = None
        self._initialized = False

    def _init_extractors(self):
        """延迟初始化各个提取器"""
        if self._initialized:
            return

        # 1. Trafilatura
        try:
            import trafilatura

            self._trafilatura = trafilatura
            logger.info("MultiMethodExtractor: Trafilatura 可用")
        except ImportError:
            logger.warning("MultiMethodExtractor: Trafilatura 不可用")

        # 2. Newspaper4k
        try:
            from newspaper import Article

            self._newspaper = Article
            logger.info("MultiMethodExtractor: Newspaper4k 可用")
        except ImportError:
            logger.warning("MultiMethodExtractor: Newspaper4k 不可用")

        # 3. Jina Reader
        try:
            from scripts.extractors.jina_extractor import JinaExtractor

            self._jina = JinaExtractor()
            logger.info("MultiMethodExtractor: Jina Reader 可用")
        except Exception:
            logger.warning("MultiMethodExtractor: Jina Reader 不可用")

        self._initialized = True

    def _get_priority_method(self, url: str) -> str:
        """根据域名返回优先使用方法"""
        domain = urlparse(url).netloc
        # 移除 www. 前缀
        if domain.startswith("www."):
            domain = domain[4:]
        return self.PRIORITY_DOMAINS.get(domain, "trafilatura")

    def _extract_trafilatura(self, url: str) -> Optional[str]:
        """方法1: Trafilatura"""
        if not self._trafilatura:
            return None
        try:
            html = self._trafilatura.fetch_url(url)
            if not html:
                return None
            # 注意：output_format 应该是 "txt" 不是 "text"
            text = self._trafilatura.extract(
                html,
                target_language="zh",
                include_comments=False,
                include_tables=False,
                deduplicate=True,
            )
            if text and len(text) > 100:
                logger.info(f"Trafilatura 成功: {url}, {len(text)} chars")
                return text.strip()
        except Exception as e:
            logger.warning(f"Trafilatura 失败: {url}, {e}")
        return None

    def _extract_newspaper(self, url: str) -> Optional[str]:
        """方法2: Newspaper4k"""
        if not self._newspaper:
            return None
        try:
            article = self._newspaper(url)
            article.download()
            article.parse()
            text = article.text
            if text and len(text) > 100:
                logger.info(f"Newspaper4k 成功: {url}, {len(text)} chars")
                return text.strip()
        except Exception as e:
            logger.warning(f"Newspaper4k 失败: {url}, {e}")
        return None

    def _extract_jina(self, url: str) -> Optional[str]:
        """方法3: Jina Reader API"""
        if not self._jina:
            return None
        try:
            return self._jina.extract(url)
        except Exception as e:
            logger.warning(f"Jina Reader 失败: {url}, {e}")
        return None

    def _extract_beautifulsoup(self, url: str) -> Optional[str]:
        """方法4: BeautifulSoup 兜底"""
        try:
            from bs4 import BeautifulSoup
            import trafilatura

            html = trafilatura.fetch_url(url)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")

            # 移除噪声标签
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                tag.decompose()

            # 尝试找到主要内容区域
            content_area = (
                soup.find("article")
                or soup.find("div", class_=lambda x: x and "article" in x.lower())
                or soup.find("div", class_=lambda x: x and "content" in x.lower())
                or soup.find("main")
            )

            if content_area:
                text = content_area.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # 清理多余空白
            import re

            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

            if text and len(text) > 100:
                logger.info(f"BeautifulSoup 成功: {url}, {len(text)} chars")
                return text
        except Exception as e:
            logger.warning(f"BeautifulSoup 失败: {url}, {e}")
        return None

    def extract(self, url: str, methods: List[str] = None) -> Optional[str]:
        """
        提取网页内容

        Args:
            url: 目标 URL
            methods: 指定使用方法列表，默认按优先级尝试所有

        Returns:
            提取的文本，失败返回 None
        """
        self._init_extractors()

        # 确定要尝试的方法顺序
        if methods is None:
            priority = self._get_priority_method(url)
            # 优先方法放前面，其他按默认顺序
            methods = [priority] + [m for m in self.METHODS if m != priority]

        logger.info(f"MultiMethodExtractor 开始提取: {url}, 方法顺序: {methods}")

        for method in methods:
            result = None

            if method == "trafilatura":
                result = self._extract_trafilatura(url)
            elif method == "newspaper":
                result = self._extract_newspaper(url)
            elif method == "jina":
                result = self._extract_jina(url)
            elif method == "beautifulsoup":
                result = self._extract_beautifulsoup(url)

            if result and len(result) > 100:
                # 后处理清理残留噪声
                result = clean_content(result)
                if len(result) > 50:
                    logger.info(f"提取成功: {url}, 方法={method}, 长度={len(result)}")
                    return result

        logger.error(f"所有提取方法均失败: {url}")
        return None

    def extract_with_details(self, url: str) -> Dict[str, Any]:
        """
        提取并返回详细信息（包含方法信息）

        Returns:
            {
                "text": "提取的文本",
                "method": "成功使用的方法",
                "length": 文本长度
            }
        """
        self._init_extractors()

        for method in self.METHODS:
            result = None

            if method == "trafilatura":
                result = self._extract_trafilatura(url)
            elif method == "newspaper":
                result = self._extract_newspaper(url)
            elif method == "jina":
                result = self._extract_jina(url)
            elif method == "beautifulsoup":
                result = self._extract_beautifulsoup(url)

            if result and len(result) > 100:
                return {"text": result, "method": method, "length": len(result)}

        return {"text": None, "method": None, "length": 0}


# 全局实例
_extractor = None


def get_extractor() -> MultiMethodExtractor:
    """获取全局提取器实例"""
    global _extractor
    if _extractor is None:
        _extractor = MultiMethodExtractor()
    return _extractor


def extract(url: str) -> Optional[str]:
    """快捷提取函数"""
    return get_extractor().extract(url)


def extract_many(urls: List[str]) -> Dict[str, Optional[str]]:
    """批量提取"""
    extractor = get_extractor()
    return {url: extractor.extract(url) for url in urls}
