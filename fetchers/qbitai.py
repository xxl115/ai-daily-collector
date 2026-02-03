# -*- coding: utf-8 -*-
"""
量子位 API 抓取器

从量子位 API 采集 AI 相关文章
"""

from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


class QbitaiFetcher:
    """量子位 API 抓取器"""

    API_URL = "https://api.qbitai.com/v1/articles"
    BASE_URL = "https://www.qbitai.com"

    def __init__(self, timeout: int = 30, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def fetch(self, limit: int = 30, keyword: str = "AI") -> List[Dict]:
        """
        采集量子位文章

        Args:
            limit: 最大文章数
            keyword: 关键词过滤

        Returns:
            文章列表
        """
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)

        for attempt in range(self.max_retries):
            try:
                # 尝试调用 API
                response = self.session.get(
                    self.API_URL,
                    params={"limit": limit},
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                articles = self._parse_api_response(data, now, keyword)
                logger.info(f"[量子位] API: {len(articles)} 条")
                return articles

            except Exception as e:
                # API 失败，尝试从网站抓取
                logger.warning(f"[量子位] API 失败: {e}，尝试从网站抓取")
                articles = self._fetch_from_website(limit, keyword, now)
                if articles:
                    return articles

                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(2)
                else:
                    logger.error(f"[量子位] 全部失败: {e}")

        return articles

    def _parse_api_response(self, data: dict, now: datetime, keyword: str) -> List[Dict]:
        """解析 API 响应"""
        articles = []

        for item in data.get("articles", [])[:30]:
            title = item.get("title", "")
            url = item.get("url", "")

            # 关键词过滤
            if keyword and keyword.lower() not in title.lower():
                continue

            summary = item.get("summary", "") or item.get("description", "")
            if summary:
                # 清理 HTML 标签
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text(strip=True)[:300]

            articles.append({
                "title": title[:200],
                "url": url,
                "summary": summary,
                "source": "量子位",
                "source_id": "qbitai",
                "published_at": item.get("published_at", ""),
                "timestamp": now.isoformat(),
                "hot_score": item.get("views", 0) or 50,
            })

        return articles

    def _fetch_from_website(self, limit: int, keyword: str, now: datetime) -> List[Dict]:
        """从网站抓取"""
        articles = []

        try:
            response = self.session.get(
                self.BASE_URL,
                timeout=self.timeout
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 量子位文章列表选择器（需要根据实际页面调整）
            for article_elem in soup.select("article")[:limit]:
                title_elem = article_elem.select_one("h2 a, h3 a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")

                if not url:
                    continue

                # 补全 URL
                if url.startswith("/"):
                    url = self.BASE_URL + url

                # 关键词过滤
                if keyword and keyword.lower() not in title.lower():
                    continue

                summary_elem = article_elem.select_one(".summary, .excerpt, p")
                summary = summary_elem.get_text(strip=True)[:300] if summary_elem else ""

                articles.append({
                    "title": title[:200],
                    "url": url,
                    "summary": summary,
                    "source": "量子位",
                    "source_id": "qbitai",
                    "published_at": "",
                    "timestamp": now.isoformat(),
                    "hot_score": 50,
                })

            logger.info(f"[量子位] 网站: {len(articles)} 条")

        except Exception as e:
            logger.warning(f"[量子位] 网站抓取失败: {e}")

        return articles


# 全局实例
qbitai_fetcher = QbitaiFetcher()


def fetch_qbitai(limit: int = 30, keyword: str = "AI") -> List[Dict]:
    """采集量子位"""
    return qbitai_fetcher.fetch(limit=limit, keyword=keyword)


def fetch_qbitai_hotspots(limit: int = 30) -> List[Dict]:
    """获取量子位热点文章"""
    return fetch_qbitai(limit=limit)
