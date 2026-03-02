"""Crawl4AI 提取器 - 批量并发方案"""

import asyncio
import atexit
import logging
import os
import signal
import sys
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


def clean_content(text: str) -> str:
    """
    清理提取内容中的噪声（导航、登录、页脚等）

    使用策略：
    1. 移除固定噪声模式（导航、登录、页脚等）
    2. 移除短链接行
    3. 尝试识别并提取文章主体
    """
    import re

    if not text:
        return text

    # 1. 移除大块噪声模式
    noise_blocks = [
        # 登录/用户中心区域
        r"\[?\]\(https://36kr\.com/usercenter[^\)]*\)",
        r"账号设置.*?退出登录",
        r"登录\s*搜索",
        # 导航菜单（连续多行分类链接）
        r"(\* \[?[^\]]*\]?\(https?://[^\)]+\)\s*){3,}",
        # logo 图片链接
        r"!\[.*?\]\(https?://img\.36krcdn\.com[^\)]+\)",
        # 版权/备案信息
        r"京ICP证\d+号.*?",
        r"京ICP备\d+号.*?",
        r"京公网安备\d+号",
        r"36氪APP.*?看到未来",
        r"鲸准.*?领跑行业",
        # 雷锋网噪声
        r"您正在使用IE低版浏览器.*?(?:浏览器|体验)",
        r"为了您的.*?账号安全",
        # 爱搞机
        r"爱搞机",
        r"雷锋网",
        # 常见噪声
        r"相关推荐.*?热门文章",
        r"更多精彩.*?",
    ]

    for pattern in noise_blocks:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # 2. 移除单行噪声
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过纯图片行
        if re.match(r"^!\[.*?\]\(.+\)$", stripped):
            continue
        # 跳过只有图片链接的行（很短）
        if len(stripped) < 15 and (
            "36kr" in stripped or "leiphone" in stripped or "krcdn" in stripped
        ):
            continue
        # 跳过非常短的行
        if len(stripped) < 5:
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 3. 移除多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text

    # 移除常见的导航/菜单噪声
    noise_patterns = [
        # 登录/注册提示
        r"您正在使用IE低版浏览器.*?建议使用.*?浏览器",
        r"为了您的.*?账号安全.*?更好的产品体验",
        r"立即登录|免费注册|登录注册",
        r"\[!\[\]\(https?://[^\]]+\)\]\([^)]+\)",  # 图片链接（通常是logo）
        # 导航栏
        r"\* \[.*?\]\(https?://[^)]+\)\s*\* \[",  # 导航链接
        # 版权/页脚
        r"版权所有.*?\d{4}",
        r"copyright.*?\d{4}",
        r"沪ICP备\d+号",
        r"京ICP备\d+号",
        # 社交分享
        r"分享到.*?微博.*?微信",
        r"扫码.*?关注",
        # 相关推荐（通常在文章底部）
        r"相关推荐.*?热门文章",
        r"更多.*?阅读",
        r"上一篇.*?下一篇",
        # 广告
        r"广告",
        r" Sponsored ",
        # 常见噪声词
        r"爱搞机",
        r"雷峰网",
        r"机器之心",
        r"36kr",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # 移除空行和多余空白
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # 移除单行噪声（如短链接列表）
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # 跳过太短的行（通常是按钮/链接）
        if len(line.strip()) < 10:
            continue
        # 跳过纯链接行
        if re.match(r"^!?\[.*?\]\(https?://", line):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 移除首尾空白
    text = text.strip()

    return text


# 全局爬虫实例（类级别复用）
_crawler = None
_crawler_config = None
_event_loop = None


def _get_event_loop():
    """获取或创建事件循环，避免重复创建"""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop


async def _close_crawler_async():
    """异步关闭爬虫"""
    global _crawler
    if _crawler is not None:
        try:
            await _crawler.close()
        except Exception:
            pass
        _crawler = None


def _cleanup():
    """清理资源"""
    global _event_loop, _crawler

    # 先尝试关闭爬虫
    if _crawler is not None and _event_loop is not None and not _event_loop.is_closed():
        try:
            _event_loop.run_until_complete(_close_crawler_async())
        except Exception:
            pass

    # 再关闭事件循环
    if _event_loop is not None and not _event_loop.is_closed():
        _event_loop.close()

    _event_loop = None
    _crawler = None


def _signal_handler(signum, frame):
    """信号处理"""
    _cleanup()
    sys.exit(0)


atexit.register(_cleanup)
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


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
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

        # 不使用内容过滤器，依赖后处理清理噪声
        md_generator = DefaultMarkdownGenerator()

        # 浏览器配置：使用内置浏览器模式，复用浏览器实例
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            browser_mode="builtin",
        )

        # 爬取配置：使用 LXML 解析 + 内容过滤
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scraping_strategy=LXMLWebScrapingStrategy(),
            page_timeout=20000,
            word_count_threshold=80,
            markdown_generator=md_generator,
        )

        # 调度器：适中并发，避免被封
        dispatcher = MemoryAdaptiveDispatcher(
            max_session_permit=10,
            rate_limiter=RateLimiter(base_delay=(1.0, 2.0), max_delay=10.0, max_retries=2),
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
            loop = _get_event_loop()
            result = loop.run_until_complete(self._extract_async(url))
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
            loop = _get_event_loop()
            results = loop.run_until_complete(
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

            if result.success:
                # 优先使用过滤后的内容
                text = None
                if hasattr(result, "fit_markdown") and result.fit_markdown:
                    text = result.fit_markdown.strip()
                elif hasattr(result, "markdown") and result.markdown:
                    text = result.markdown.strip()

                if text and len(text) > 100:
                    # 后处理清理噪声
                    text = clean_content(text)
                    if len(text) > 50:  # 清理后仍需保留足够内容
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

            if result.success:
                # 优先使用过滤后的内容
                text = None
                if hasattr(result, "fit_markdown") and result.fit_markdown:
                    text = result.fit_markdown.strip()
                elif hasattr(result, "markdown") and result.markdown:
                    text = result.markdown.strip()

                if text and len(text) > 100:
                    # 后处理清理噪声
                    text = clean_content(text)
                    if len(text) > 50:
                        results_dict[url] = text
                        logger.debug(f"OK: {url}")
                    else:
                        results_dict[url] = None
                        logger.warning(f"清理后内容过短: {url}")
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
