# -*- coding: utf-8 -*-
"""
Product Hunt 抓取器

抓取 Product Hunt 每日热门产品
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


class ProductHuntFetcher:
    """Product Hunt 抓取器"""

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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def fetch_rss(self) -> List[Dict]:
        """从 RSS 抓取"""
        rss_url = "https://www.producthunt.com/feed"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(rss_url, timeout=self.timeout)
                response.raise_for_status()

                articles = self._parse_rss(response.text)
                logger.info(f"[Product Hunt] RSS: {len(articles)} 条")
                return articles

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[Product Hunt] RSS 抓取失败: {e}")

        return []

    def _parse_rss(self, content: str) -> List[Dict]:
        """解析 Atom 格式 (Product Hunt 使用 Atom 而非 RSS)"""
        from xml.etree import ElementTree as ET

        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)

        try:
            root = ET.fromstring(content)
            # Product Hunt 使用 Atom 格式，命名空间为 http://www.w3.org/2005/Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns)[:10]:
                title = entry.findtext("atom:title", "", ns)
                # Atom 的 link 在 href 属性中
                link_elem = entry.find("atom:link", ns)
                link = link_elem.get("href", "") if link_elem is not None else ""

                # 获取 alternate link
                if not link:
                    for link_elem in entry.findall("atom:link", ns):
                        if link_elem.get("rel") == "alternate":
                            link = link_elem.get("href", "")
                            break

                # Atom 使用 content 而非 description
                content_elem = entry.find("atom:content", ns)
                desc = content_elem.text if content_elem is not None else ""

                # 清理描述中的 HTML
                if desc:
                    soup = BeautifulSoup(desc, "html.parser")
                    desc = soup.get_text(strip=True)[:300]

                pub_date = entry.findtext("atom:published", "", ns)

                articles.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "summary": desc,
                    "source": "Product Hunt",
                    "source_id": "producthunt",
                    "published_at": pub_date,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_score(pub_date),
                })
        except Exception as e:
            logger.warning(f"Product Hunt Atom 解析失败: {e}")

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
        return {"producthunt": articles}

    def get_hotspots(self, limit: int = 10) -> List[Dict]:
        """获取热点"""
        articles = self.fetch_rss()
        return articles[:limit]


# 全局实例
producthunt_fetcher = ProductHuntFetcher()


def fetch_producthunt() -> Dict[str, List[Dict]]:
    """抓取 Product Hunt"""
    return producthunt_fetcher.fetch_all()


def fetch_producthunt_hotspots(limit: int = 10) -> List[Dict]:
    """获取 Product Hunt 热点"""
    return producthunt_fetcher.get_hotspots(limit)
