"""Crawl4AI 提取器 - 批量并发方案"""

import asyncio
import logging
import os
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# 全局爬虫实例（类级别复用）
_crawler = None
_crawler_config = None


def _init_crawler():
    """初始化 Crawl4AI 爬虫（只执行一次）"""
    global _crawler, _crawler_config

    if _crawler is not None:
        return _crawler

    try:
        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            MemoryAdaptiveDispatcher,
            RateLimiter,
            CacheMode,
        )
        from crawl4ai import LXMLWebScrapingStrategy

        # 浏览器配置：使用内置浏览器模式，复用浏览器实例
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            browser_mode="builtin",
        )

        # 爬取配置：使用 LXML 解析，速度提升 20x
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scraping_strategy=LXMLWebScrapingStrategy(),
            page_timeout=20000,
            word_count_threshold=80,
        )

        # 调度器：适中并发，避免被封
        dispatcher = MemoryAdaptiveDispatcher(
            max_session_permit=10,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 2.0), max_delay=10.0, max_retries=2
            ),
            memory_threshold_percent=80.0,
        )

        _crawler_config = {
            "browser": browser_config,
            "crawl": crawl_config,
            "dispatcher": dispatcher,
        }

        _crawler = AsyncWebCrawler()
        logger.info("Crawl4AI 爬虫初始化完成（并发=10, 延迟=1-2s）")
        return _crawler

    except Exception as e:
        logger.error(f"Crawl4AI 初始化失败: {e}")
        return None


class Crawl4AIExtractor:
    """Crawl4AI 提取器 - 支持批量并发"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._crawler = None

    def extract(self, url: str) -> Optional[str]:
        """单 URL 提取（同步接口，保持兼容）"""
        try:
            result = asyncio.run(self._extract_async(url))
            return result
        except Exception as e:
            logger.error(f"Crawl4AI 提取失败 {url}: {e}")
            return None

    def extract_many(
        self, urls: List[str], callback=None, progress_interval: int = 10
    ) -> Dict[str, Optional[str]]:
        """
        批量提取 URLs

        Args:
            urls: URL 列表
            callback: 进度回调函数 callback(completed, total)
            progress_interval: 进度报告间隔

        Returns:
            {url: content} 字典，失败为 None
        """
        if not urls:
            return {}

        try:
            results = asyncio.run(
                self._extract_many_async(urls, callback, progress_interval)
            )
            return results
        except Exception as e:
            logger.error(f"Crawl4AI 批量提取失败: {e}")
            return {url: None for url in urls}

    async def _extract_async(self, url: str) -> Optional[str]:
        """异步单 URL 提取"""
        try:
            crawler = _init_crawler()
            if crawler is None:
                return None

            config = _crawler_config
            result = await crawler.arun(url, config=config["crawl"])

            if result.success and result.markdown:
                text = result.markdown.strip()
                if len(text) > 100:
                    logger.info(f"Crawl4AI 成功: {url}, {len(text)} chars")
                    return text

            error_msg = result.error if hasattr(result, "error") else "Unknown"
            logger.warning(f"Crawl4AI 返回为空: {url} - {error_msg}")
            return None

        except Exception as e:
            logger.error(f"Crawl4AI 异常: {url} - {e}")
            return None

    async def _extract_many_async(
        self, urls: List[str], callback=None, progress_interval: int = 10
    ) -> Dict[str, Optional[str]]:
        """异步批量提取"""
        crawler = _init_crawler()
        if crawler is None:
            return {url: None for url in urls}

        config = _crawler_config
        results_dict = {}
        completed = 0
        total = len(urls)

        logger.info(f"Crawl4AI 开始批量抓取: {total} URLs, 并发={self.max_concurrent}")

        result_container = await crawler.arun_many(
            urls=urls, config=config["crawl"], dispatcher=config["dispatcher"]
        )

        if isinstance(result_container, list):
            results_list = result_container
        else:
            results_list = []
            async for res in result_container:
                results_list.append(res)

        for result in results_list:
            url = result.url
            completed += 1

            if result.success and result.markdown:
                text = result.markdown.strip()
                if len(text) > 100:
                    results_dict[url] = text
                    logger.debug(f"OK: {url}")
                else:
                    results_dict[url] = None
                    logger.warning(f"内容过短: {url}")
            else:
                results_dict[url] = None
                error = result.error if hasattr(result, "error") else "Unknown"
                logger.debug(f"Failed: {url} - {error}")

            if callback and completed % progress_interval == 0:
                callback(completed, total)

        if callback:
            callback(total, total)

        success_count = sum(1 for v in results_dict.values() if v)
        logger.info(f"Crawl4AI 批量完成: {success_count}/{total} 成功")

        return results_dict


def extract(url: str) -> Optional[str]:
    """单 URL 提取"""
    extractor = Crawl4AIExtractor()
    return extractor.extract(url)


def extract_many(urls: List[str]) -> Dict[str, Optional[str]]:
    """批量提取"""
    extractor = Crawl4AIExtractor()
    return extractor.extract_many(urls)
