# -*- coding: utf-8 -*-
"""
科技媒体抓取器

抓取:
- TechCrunch
- The Verge
- Wired
- MIT Technology Review
- VentureBeat
- Ars Technica
- HackerNoon
- BetaList
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


# 媒体配置
MEDIA = {
    # ===== 中文科技媒体 =====
    "36kr": {
        "name": "36氪",
        "url": "https://36kr.com/",
        "rss": "https://36kr.com/feed",
        "language": "zh",
        "selectors": {
            "article": ".item-item",
            "title": ".item-title a",
            "link": ".item-title a",
            "summary": ".item-desc",
        }
    },
    "jiqizhixin": {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/",
        "rss": "https://www.jiqizhixin.com/rss",
        "language": "zh",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
    "tmtpost": {
        "name": "钛媒体",
        "url": "https://www.tmtpost.com/",
        "rss": "https://www.tmtpost.com/feed",
        "language": "zh",
        "selectors": {
            "article": ".post-item",
            "title": ".post-title a",
            "link": ".post-title a",
            "summary": ".post-excerpt",
        }
    },
    "leiphone": {
        "name": "雷锋网",
        "url": "https://www.leiphone.com/",
        "rss": "https://www.leiphone.com/feed",
        "language": "zh",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },

    # ===== 英文科技媒体 =====
    "techcrunch": {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/",
        "rss": "https://techcrunch.com/feed/",
        "selectors": {
            "article": "article.post-block",
            "title": ".post-block__title__link",
            "link": ".post-block__title__link",
            "summary": ".post-block__summary",
        }
    },
    "theverge": {
        "name": "The Verge",
        "url": "https://www.theverge.com/",
        "rss": "https://www.theverge.com/rss/index.xml",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
    "wired": {
        "name": "Wired",
        "url": "https://www.wired.com/",
        "rss": "https://www.wired.com/feed/rss",
        "selectors": {
            "article": "div.card-component",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
    "mit-tech": {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/",
        "rss": "https://www.technologyreview.com/feed/",
        "selectors": {
            "article": "article",
            "title": "h3 a",
            "link": "h3 a",
            "summary": ".dek",
        }
    },
    "venturebeat": {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/",
        "rss": "https://venturebeat.com/feed/",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
    "ars-technica": {
        "name": "Ars Technica",
        "url": "https://arstechnica.com/",
        "rss": "https://arstechnica.com/feed/",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".excerpt",
        }
    },
    "hackernoon": {
        "name": "HackerNoon",
        "url": "https://hackernoon.com/",
        "rss": "https://hackernoon.com/feed",
        "selectors": {
            "article": "article",
            "title": "h3 a",
            "link": "h3 a",
            "summary": ".summary",
        }
    },
    "betablist": {
        "name": "BetaList",
        "url": "https://betablist.com/",
        "rss": "https://betablist.com/feed",
        "selectors": {
            "article": ".startup-item",
            "title": ".startup-name",
            "link": ".startup-link",
            "summary": ".startup-tagline",
        }
    },
    "yahootech": {
        "name": "Yahoo Tech",
        "url": "https://www.yahoo.com/tech/",
        "rss": None,
        "selectors": {
            "article": "article",
            "title": "h3 a",
            "link": "h3 a",
            "summary": ".summary",
        }
    },
}


class TechMediaFetcher:
    """科技媒体抓取器"""
    
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
    
    def fetch_rss(self, media_id: str) -> List[Dict]:
        """从 RSS 抓取"""
        if media_id not in MEDIA:
            return []
        
        config = MEDIA[media_id]
        rss_url = config.get("rss")
        if not rss_url:
            return []
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(rss_url, timeout=self.timeout)
                response.raise_for_status()
                
                articles = self._parse_rss(response.text, media_id)
                logger.info(f"[{config['name']}] RSS: {len(articles)} 条")
                return articles
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[{config['name']}] RSS 抓取失败: {e}")
        
        return []
    
    def _parse_rss(self, content: str, media_id: str) -> List[Dict]:
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
                    "source": MEDIA[media_id]["name"],
                    "source_id": media_id,
                    "published_at": pub_date,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_score(pub_date),
                })
        except Exception as e:
            logger.warning(f"RSS 解析失败: {e}")
        
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
    
    def fetch_html(self, media_id: str) -> List[Dict]:
        """从 HTML 抓取"""
        if media_id not in MEDIA:
            return []
        
        url = MEDIA[media_id]["url"]
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                articles = self._parse_html(response.text, media_id)
                logger.info(f"[{MEDIA[media_id]['name']}] HTML: {len(articles)} 条")
                return articles
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[{MEDIA[media_id]['name']}] HTML 抓取失败: {e}")
        
        return []
    
    def _parse_html(self, html: str, media_id: str) -> List[Dict]:
        """解析 HTML"""
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        soup = BeautifulSoup(html, "html.parser")
        config = MEDIA[media_id]
        selectors = config["selectors"]
        
        for article in soup.select(selectors["article"])[:10]:
            link_elem = article.select_one(selectors["link"])
            title_elem = article.select_one(selectors["title"])
            summary_elem = article.select_one(selectors["summary"])
            
            if not link_elem:
                continue
            
            href = link_elem.get("href", "")
            title = title_elem.get_text(strip=True) if title_elem else ""
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            if not href or not title:
                continue
            
            # 补全 URL
            if href.startswith("/"):
                href = f"https://{media_id}.com{href}"
            elif not href.startswith("http"):
                continue
            
            articles.append({
                "title": title[:200],
                "url": href,
                "summary": summary[:300],
                "source": config["name"],
                "source_id": media_id,
                "published_at": "",
                "timestamp": now.isoformat(),
                "hot_score": 50,
            })
        
        return articles
    
    def fetch_all(self, media_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """抓取所有媒体"""
        if media_ids is None:
            media_ids = list(MEDIA.keys())
        
        results = {}
        
        for media_id in media_ids:
            if media_id not in MEDIA:
                continue
            
            # 优先 RSS
            articles = self.fetch_rss(media_id)
            
            # HTML 备用
            if not articles:
                articles = self.fetch_html(media_id)
            
            if articles:
                results[media_id] = articles
        
        return results
    
    def get_hotspots(self, limit: int = 50) -> List[Dict]:
        """获取热点文章"""
        all_articles = []
        
        for articles in self.fetch_all().values():
            all_articles.extend(articles)
        
        all_articles.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
        return all_articles[:limit]


# 全局实例
tech_media_fetcher = TechMediaFetcher()


def fetch_tech_media(media_ids: List[str] = None) -> Dict[str, List[Dict]]:
    """抓取科技媒体"""
    return tech_media_fetcher.fetch_all(media_ids)


def fetch_tech_media_hotspots(limit: int = 50) -> List[Dict]:
    """获取科技媒体热点"""
    return tech_media_fetcher.get_hotspots(limit)


def get_supported_media() -> List[Dict]:
    """获取支持的媒体列表"""
    return [
        {"id": k, "name": v["name"], "url": v["url"]}
        for k, v in MEDIA.items()
    ]
