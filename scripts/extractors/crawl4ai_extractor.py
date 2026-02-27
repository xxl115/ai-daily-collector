"""Crawl4AI 提取器（降级方案）"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局爬虫实例，避免重复初始化
_crawler = None


def _get_crawler():
    """获取或初始化 Crawl4AI 爬虫"""
    global _crawler
    if _crawler is None:
        try:
            from crawl4ai import AsyncWebCrawler

            _crawler = AsyncWebCrawler()
        except Exception as e:
            logger.error(f"Crawl4AI 初始化失败: {e}")
            return None
    return _crawler


class Crawl4AIExtractor:
    """Crawl4AI 提取器（通过 crawl4ai 提取文本）"""

    def extract(self, url: str) -> Optional[str]:
        """提取网页内容

        Args:
            url: 目标URL

        Returns:
            提取的文本内容，失败返回 None
        """
        try:
            # 同步调用异步函数
            result = asyncio.run(self._extract_async(url))
            return result
        except Exception as e:
            logger.error(f"Crawl4AI 提取失败 {url}: {e}")
            return None

    async def _extract_async(self, url: str) -> Optional[str]:
        """异步提取网页内容"""
        try:
            crawler = _get_crawler()
            if crawler is None:
                return None

            result = await crawler.arun(url)

            if result.success and result.markdown:
                text = result.markdown.strip()
                if len(text) > 100:
                    logger.info(f"Crawl4AI 成功提取 {url}, 长度: {len(text)}")
                    return text

            # 记录失败原因
            error_msg = result.error if hasattr(result, "error") else "Unknown error"
            logger.warning(f"Crawl4AI 返回为空 {url}: {error_msg}")
            return None

        except Exception as e:
            logger.error(f"Crawl4AI 异步提取异常 {url}: {e}")
            return None
