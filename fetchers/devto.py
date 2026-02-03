# -*- coding: utf-8 -*-
"""
Dev.to 抓取器

抓取 Dev.to AI 相关文章
API: https://dev.to/api/articles
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


class DevToFetcher:
    """Dev.to 抓取器"""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 2,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })

    def fetch(
        self,
        tag: str = "ai",
        per_page: int = 10,
    ) -> List[Dict]:
        """
        抓取 Dev.to 文章

        Args:
            tag: 标签
            per_page: 每页数量
        """
        url = f"https://dev.to/api/articles"

        params = {
            "tag": tag,
            "per_page": min(per_page, 30),
            "top": 1,  # 按热度排序
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                articles = self._parse_json(response.text)
                logger.info(f"[Dev.to #{tag}] {len(articles)} 条")
                return articles

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[Dev.to] 抓取失败: {e}")

        return []

    def _parse_json(self, content: str) -> List[Dict]:
        """解析 JSON"""
        import json

        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)

        try:
            data = json.loads(content)

            for item in data:
                # 清理描述中的 HTML
                description = item.get("description", "")[:300]
                if "<p>" in description:
                    # 简单清理
                    description = description.replace("<p>", "").replace("</p>", "")[:300]

                articles.append({
                    "title": item.get("title", "")[:500],
                    "url": item.get("url", ""),
                    "summary": description,
                    "source": "Dev.to",
                    "source_id": "devto",
                    "published_at": item.get("published_at", ""),
                    "timestamp": now.isoformat(),
                    "hot_score": item.get("positive_reactions_count", 0) + 50,
                    "author": item.get("user", {}).get("name", "") if isinstance(item.get("user"), dict) else "",
                })
        except Exception as e:
            logger.warning(f"Dev.to 解析失败: {e}")

        return articles

    def fetch_all(self, tags: List[str] = None) -> Dict[str, List[Dict]]:
        """抓取多个标签"""
        if tags is None:
            tags = ["ai", "machine-learning", "python"]

        results = {}
        for tag in tags:
            articles = self.fetch(tag=tag)
            if articles:
                results[tag] = articles

        return results

    def get_hotspots(self, limit: int = 10) -> List[Dict]:
        """获取热点文章"""
        articles = self.fetch(tag="ai")
        return articles[:limit]


# 全局实例
devto_fetcher = DevToFetcher()


def fetch_devto(tag: str = "ai", per_page: int = 10) -> List[Dict]:
    """抓取 Dev.to"""
    return devto_fetcher.fetch(tag, per_page)


def fetch_devto_hotspots(limit: int = 10) -> List[Dict]:
    """获取 Dev.to 热点"""
    return devto_fetcher.get_hotspots(limit)
