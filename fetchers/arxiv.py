# -*- coding: utf-8 -*-
"""
ArXiv 论文抓取器

抓取 ArXiv AI 相关最新论文
API: http://export.arxiv.org/api/query
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


class ArxivFetcher:
    """ArXiv 论文抓取器"""

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
            "Accept": "application/rss+xml,application/xml,*/*",
        })

    def fetch(
        self,
        categories: List[str] = None,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        抓取 ArXiv 论文

        Args:
            categories: 论文分类列表
            max_results: 最大结果数
        """
        if categories is None:
            categories = ["cs.AI", "cs.LG", "cs.CL", "stat.ML"]

        all_papers = []

        for cat in categories:
            papers = self._fetch_category(cat, max_results // len(categories))
            all_papers.extend(papers)

        return all_papers

    def _fetch_category(self, category: str, max_results: int = 5) -> List[Dict]:
        """抓取单个分类"""
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"cat:{category}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                papers = self._parse_atom(response.text, category)
                logger.info(f"[ArXiv {category}] {len(papers)} 篇")
                return papers

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[ArXiv {category}] 抓取失败: {e}")

        return []

    def _parse_atom(self, content: str, category: str) -> List[Dict]:
        """解析 ATOM 格式"""
        from xml.etree import ElementTree as ET

        papers = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)

        try:
            root = ET.fromstring(content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns)[:10]:
                title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
                link = entry.findtext("atom:id", "", ns)
                summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")[:500]

                # 作者
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.findtext("atom:name", "", ns)
                    if name:
                        authors.append(name)

                # 发布日期
                published = entry.findtext("atom:published", "", ns)

                papers.append({
                    "title": title[:500],
                    "url": link,
                    "summary": summary,
                    "source": f"ArXiv ({category})",
                    "source_id": f"arxiv_{category.lower().replace('.', '_')}",
                    "authors": authors,
                    "published_at": published,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_score(published),
                })
        except Exception as e:
            logger.warning(f"ArXiv 解析失败: {e}")

        return papers

    def _calculate_score(self, pub_date: str) -> float:
        """计算热度分数（基于时间）"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            hours_ago = (datetime.now() - dt).total_seconds() / 3600
            return max(0, 100 - hours_ago * 10)
        except:
            return 50

    def fetch_ai_papers(self, max_results: int = 10) -> List[Dict]:
        """抓取 AI 相关论文"""
        return self.fetch(categories=["cs.AI", "cs.LG", "cs.CL"], max_results=max_results)

    def get_hotspots(self, limit: int = 10) -> List[Dict]:
        """获取最新论文"""
        papers = self.fetch_ai_papers(max_results=limit)
        return papers


# 全局实例
arxiv_fetcher = ArxivFetcher()


def fetch_arxiv(categories: List[str] = None, max_results: int = 10) -> List[Dict]:
    """抓取 ArXiv 论文"""
    return arxiv_fetcher.fetch(categories, max_results)


def fetch_arxiv_hotspots(limit: int = 10) -> List[Dict]:
    """获取 ArXiv 热点"""
    return arxiv_fetcher.get_hotspots(limit)
