# -*- coding: utf-8 -*-
"""
Hugging Face 抓取器

抓取 Hugging Face 博客和模型动态
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


class HuggingFaceFetcher:
    """Hugging Face 抓取器"""

    def __init__(
        self,
        timeout: int = 60,  # 增加超时时间到 60 秒
        max_retries: int = 3,  # 增加重试次数到 3 次
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def fetch_rss(self) -> List[Dict]:
        """从 RSS 抓取"""
        rss_url = "https://huggingface.co/blog/feed.xml"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(rss_url, timeout=self.timeout)
                response.raise_for_status()

                articles = self._parse_rss(response.text)
                logger.info(f"[Hugging Face] RSS: {len(articles)} 条")
                return articles

            except Exception as e:
                if attempt < self.max_retries - 1:
                    # 增加重试延迟
                    import time
                    wait_time = (attempt + 1) * 5  # 5秒, 10秒, 15秒
                    logger.warning(f"[Hugging Face] 尝试 {attempt + 1} 失败: {e}，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"[Hugging Face] RSS 抓取失败: {e}")

        return []

    def _parse_rss(self, content: str) -> List[Dict]:
        """解析 RSS"""
        from xml.etree import ElementTree as ET

        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)

        try:
            root = ET.fromstring(content)
            for item in root.findall(".//item")[:10]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                pub_date = item.findtext("pubDate", "")

                # 清理描述
                if desc:
                    soup = BeautifulSoup(desc, "html.parser")
                    desc = soup.get_text()[:300]

                articles.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "summary": desc,
                    "source": "Hugging Face",
                    "source_id": "huggingface",
                    "published_at": pub_date,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_score(pub_date),
                })
        except Exception as e:
            logger.warning(f"Hugging Face RSS 解析失败: {e}")

        return articles

    def _calculate_score(self, pub_date: str) -> float:
        """计算热度分数"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            hours_ago = (datetime.now() - dt).total_seconds() / 3600
            return max(0, 100 - hours_ago * 5)
        except:
            return 50

    def fetch_all(self) -> Dict[str, List[Dict]]:
        """抓取所有"""
        articles = self.fetch_rss()
        return {"huggingface": articles}

    def get_hotspots(self, limit: int = 10) -> List[Dict]:
        """获取热点"""
        articles = self.fetch_rss()
        return articles[:limit]


# 全局实例
huggingface_fetcher = HuggingFaceFetcher()


def fetch_huggingface() -> Dict[str, List[Dict]]:
    """抓取 Hugging Face"""
    return huggingface_fetcher.fetch_all()


def fetch_huggingface_hotspots(limit: int = 10) -> List[Dict]:
    """获取 Hugging Face 热点"""
    return huggingface_fetcher.get_hotspots(limit)
