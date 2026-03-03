"""并发竞速提取器 - 同时运行多个提取器，返回最先成功的结果"""

import concurrent.futures
import logging
import os
import threading
from typing import Optional, List, Callable

import requests

logger = logging.getLogger(__name__)


def extract_from_google_cache(url: str, timeout: float = 10.0) -> Optional[str]:
    """
    从 Google Cache 提取内容
    """
    try:
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        proxies = {}
        proxy = (
            os.environ.get("JINA_PROXY_URL")
            or os.environ.get("http_proxy")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("socks_proxy")
            or os.environ.get("SOCKS_PROXY")
        )
        if proxy:
            proxies = {"http": proxy, "https": proxy}

        response = requests.get(
            cache_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            proxies=proxies if proxies else None,
        )

        if response.status_code == 200 and len(response.text) > 500:
            text = response.text
            import re

            match = re.search(r"<pre[^>]*>(.*?)</pre>", text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                content = (
                    content.replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&amp;", "&")
                )
                if len(content) > 200:
                    logger.info(f"Google Cache 提取成功: {url}")
                    return content.strip()

            match = re.search(
                r'<div[^>]*class="[^"]*rich-content[^"]*"[^>]*>(.*?)</div>',
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if match:
                content = match.group(1)
                content = re.sub(r"<[^>]+>", "", content)
                content = (
                    content.replace("&nbsp;", " ")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&amp;", "&")
                )
                if len(content) > 200:
                    logger.info(f"Google Cache 提取成功: {url}")
                    return content.strip()

            logger.warning(f"Google Cache 内容过短: {url}")
            return None

        logger.warning(f"Google Cache 返回 {response.status_code}: {url}")
        return None

    except Exception as e:
        logger.debug(f"Google Cache 提取失败: {url} - {e}")
        return None


def extract_from_wayback(url: str, timeout: float = 10.0) -> Optional[str]:
    """
    从 Wayback Machine 提取内容
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        proxies = {}
        proxy = (
            os.environ.get("JINA_PROXY_URL")
            or os.environ.get("http_proxy")
            or os.environ.get("HTTP_PROXY")
        )
        if proxy:
            proxies = {"http": proxy, "https": proxy}

        # 先获取最近的 snapshot
        api_url = f"https://archive.org/wayback/available?url={url}"
        response = requests.get(
            api_url,
            headers=headers,
            timeout=timeout,
            proxies=proxies if proxies else None,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("archived_snapshots", {}).get("closest"):
                snapshot_url = data["archived_snapshots"]["closest"]["url"]
                # 获取 snapshot 内容
                snap_response = requests.get(
                    snapshot_url,
                    headers=headers,
                    timeout=timeout,
                    proxies=proxies if proxies else None,
                )
                if snap_response.status_code == 200 and len(snap_response.text) > 500:
                    text = snap_response.text
                    import re

                    # 尝试提取 article 或 main 内容
                    match = re.search(
                        r"<article[^>]*>(.*?)</article>",
                        text,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if not match:
                        match = re.search(
                            r"<main[^>]*>(.*?)</main>", text, re.DOTALL | re.IGNORECASE
                        )
                    if not match:
                        match = re.search(
                            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                            text,
                            re.DOTALL | re.IGNORECASE,
                        )

                    if match:
                        content = match.group(1)
                        content = re.sub(r"<[^>]+>", "", content)
                        content = (
                            content.replace("&nbsp;", " ")
                            .replace("&lt;", "<")
                            .replace("&gt;", ">")
                            .replace("&amp;", "&")
                        )
                        content = re.sub(r"\s+", " ", content).strip()
                        if len(content) > 200:
                            logger.info(f"Wayback Machine 提取成功: {url}")
                            return content

        logger.debug(f"Wayback Machine 无可用快照: {url}")
        return None

    except Exception as e:
        logger.debug(f"Wayback Machine 提取失败: {url} - {e}")
        return None


def extract_with_bypass(url: str, timeout: float = 10.0) -> Optional[str]:
    """
    尝试通过修改请求头绕过付费墙
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        proxies = {}
        proxy = (
            os.environ.get("JINA_PROXY_URL")
            or os.environ.get("http_proxy")
            or os.environ.get("HTTP_PROXY")
        )
        if proxy:
            proxies = {"http": proxy, "https": proxy}

        response = requests.get(
            url, headers=headers, timeout=timeout, proxies=proxies if proxies else None
        )

        if response.status_code == 200 and len(response.text) > 500:
            import re

            text = response.text

            # 尝试提取 article/main/body 内容
            match = re.search(
                r"<article[^>]*>(.*?)</article>", text, re.DOTALL | re.IGNORECASE
            )
            if not match:
                match = re.search(
                    r"<main[^>]*>(.*?)</main>", text, re.DOTALL | re.IGNORECASE
                )
            if not match:
                match = re.search(
                    r"<body[^>]*>(.*?)</body>", text, re.DOTALL | re.IGNORECASE
                )

            if match:
                content = match.group(1)
                content = re.sub(
                    r"<script[^>]*>.*?</script>",
                    "",
                    content,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                content = re.sub(
                    r"<style[^>]*>.*?</style>",
                    "",
                    content,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                content = re.sub(r"<[^>]+>", "", content)
                content = (
                    content.replace("&nbsp;", " ")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&amp;", "&")
                )
                content = re.sub(r"\s+", " ", content).strip()
                if len(content) > 200:
                    logger.info(f"Bypass 提取成功: {url}")
                    return content

        logger.debug(f"Bypass 返回 {response.status_code}: {url}")
        return None

    except Exception as e:
        logger.debug(f"Bypass 提取失败: {url} - {e}")
        return None


class RaceExtractor:
    """并发竞速提取器

    同时运行多个提取器，返回最先成功（非空）的结果。
    适用于：Trafilatura 和 Jina 并发竞争，谁先返回用谁。
    """

    def __init__(self, extractors: List[Callable], timeout: float = 30.0):
        """
        Args:
            extractors: 提取器列表，每个提取器需要是 callable(url) -> Optional[str]
            timeout: 最大等待时间（秒）
        """
        self.extractors = extractors
        self.timeout = timeout
        self._result_lock = threading.Lock()
        self._result = {"content": None, "method": None, "error": None}

    def extract(self, url: str) -> Optional[str]:
        """并发提取，返回最先成功的结果"""
        self._result = {"content": None, "method": None, "error": None}

        def try_extractor(extractor, idx):
            if self._result["content"] is not None:
                return None

            try:
                result = (
                    extractor.extract(url)
                    if hasattr(extractor, "extract")
                    else extractor(url)
                )

                with self._result_lock:
                    if self._result["content"] is None and result:
                        self._result["content"] = result
                        self._result["method"] = idx
                        logger.debug(f"Extractor {idx} won the race for {url}")
                        return result
            except Exception as e:
                logger.debug(f"Extractor {idx} failed: {e}")
                with self._result_lock:
                    if self._result["error"] is None:
                        self._result["error"] = str(e)
                return None

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.extractors)
        ) as executor:
            futures = [
                executor.submit(try_extractor, extractor, idx)
                for idx, extractor in enumerate(self.extractors)
            ]

            try:
                concurrent.futures.wait(futures, timeout=self.timeout)
            except Exception as e:
                logger.warning(f"RaceExtractor timeout/error: {e}")

        return self._result["content"]

    def get_winner_method(self) -> Optional[str]:
        return self._result.get("method")


class FastExtractor:
    """快速提取器 - Trafilatura 和 Jina 并发竞速

    Trafilatura 和 Jina 并发竞速，都失败则降级到 Crawl4AI。
    三个提取器都只执行一次，不重试。
    """

    def __init__(self, trafilatura_extractor, jina_extractor, crawl4ai_extractor=None):
        self.trafilatura = trafilatura_extractor
        self.jina = jina_extractor
        self.crawl4ai = crawl4ai_extractor
        self.timeout = 8.0  # 竞速超时

        # Trafilatura 和 Jina 竞速
        self.race_extractor = RaceExtractor(
            [trafilatura_extractor, jina_extractor], timeout=self.timeout
        )

    def extract(self, url: str, use_race: bool = True) -> tuple[Optional[str], str]:
        """
        提取内容 - Trafilatura 和 Jina 竞速，都失败则降级到 Crawl4AI
        三个提取器都只执行一次，不重试

        Args:
            url: 目标 URL
            use_race: 是否使用竞速模式（默认 True）

        Returns:
            (content, method): 内容和方法名
        """
        if not use_race:
            return None, "failed"

        # 第一轮：Trafilatura 和 Jina 竞速
        content = self.race_extractor.extract(url)
        winner_idx = self.race_extractor.get_winner_method()

        if content:
            method = "trafilatura" if winner_idx == 0 else "jina"
            logger.info(f"竞速模式 - {method} 获胜: {url}")
            return content, method

        # 第二轮：降级到 Crawl4AI（只执行一次）
        if self.crawl4ai:
            try:
                content = self.crawl4ai.extract(url)
                if content:
                    logger.info(f"Crawl4AI 提取成功: {url}")
                    return content, "crawl4ai"
            except Exception as e:
                logger.debug(f"Crawl4AI failed: {e}")

        # 第三轮：降级到 Google Cache
        try:
            content = extract_from_google_cache(url)
            if content:
                logger.info(f"Google Cache 提取成功: {url}")
                return content, "google-cache"
        except Exception as e:
            logger.debug(f"Google Cache failed: {e}")

        # 第四轮：降级到 Wayback Machine
        try:
            content = extract_from_wayback(url)
            if content:
                logger.info(f"Wayback Machine 提取成功: {url}")
                return content, "wayback"
        except Exception as e:
            logger.debug(f"Wayback Machine failed: {e}")

        # 第五轮：尝试绕过付费墙
        try:
            content = extract_with_bypass(url)
            if content:
                logger.info(f"Bypass 提取成功: {url}")
                return content, "bypass"
        except Exception as e:
            logger.debug(f"Bypass failed: {e}")

        logger.info(f"所有提取器失败: {url}")
        return "-1", "failed"
