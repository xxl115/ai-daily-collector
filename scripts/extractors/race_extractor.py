"""并发竞速提取器 - 同时运行多个提取器，返回最先成功的结果"""

import concurrent.futures
import logging
import threading
from typing import Optional, List, Callable

logger = logging.getLogger(__name__)


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

    同时调用 Trafilatura 和 Jina Reader，返回最先成功的内容。
    如果都失败，则降级到 Crawl4AI。
    """

    def __init__(self, trafilatura_extractor, jina_extractor, crawl4ai_extractor=None):
        self.trafilatura = trafilatura_extractor
        self.jina = jina_extractor
        self.crawl4ai = crawl4ai_extractor
        self.timeout = 5.0  # 减少竞速超时，防止长时间等待

        self.race_extractor = RaceExtractor(
            [trafilatura_extractor, jina_extractor], timeout=self.timeout
        )

    def extract(self, url: str, use_race: bool = True) -> tuple[Optional[str], str]:
        """
        提取内容

        Args:
            url: 目标 URL
            use_race: 是否使用竞速模式（默认 True）

        Returns:
            (content, method): 内容和方法名
        """
        content = None
        method = None

        if use_race:
            content = self.race_extractor.extract(url)
            winner_idx = self.race_extractor.get_winner_method()

            if content:
                method = "trafilatura" if winner_idx == 0 else "jina"
                logger.info(f"竞速模式 - {method} 获胜: {url}")
                return content, method
            else:
                # 竞速超时，两个都失败了，继续 fallback
                logger.info(f"竞速模式超时，继续 fallback: {url}")

        if not content:
            try:
                content = self.trafilatura.extract(url)
                if content:
                    method = "trafilatura"
            except Exception as e:
                logger.debug(f"Trafilatura failed: {e}")

        if not content:
            try:
                content = self.jina.extract(url)
                if content:
                    method = "jina"
            except Exception as e:
                logger.debug(f"Jina failed: {e}")

        if not content and self.crawl4ai:
            try:
                content = self.crawl4ai.extract(url)
                if content:
                    method = "crawl4ai"
            except Exception as e:
                logger.debug(f"Crawl4AI failed: {e}")

        if not content:
            method = "failed"

        return content, method
