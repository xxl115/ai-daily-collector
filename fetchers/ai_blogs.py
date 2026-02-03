# -*- coding: utf-8 -*-
"""
AI 官方博客抓取器

抓取:
- OpenAI Blog
- Google AI Blog
- Anthropic Blog
- Meta AI Blog
- DeepMind Blog
- Microsoft AI Blog
- AWS AI Blog
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


# 博客配置
BLOGS = {
    "openai": {
        "name": "OpenAI",
        "url": "https://openai.com/blog/",
        "rss": "https://openai.com/blog/rss.xml",
    },
    "google-ai": {
        "name": "Google AI",
        "url": "https://blog.google/technology/ai/",
        "rss": "https://blog.google/technology/ai/rss.xml",
    },
    "anthropic": {
        "name": "Anthropic",
        "url": "https://www.anthropic.com/news",
        "rss": "https://www.anthropic.com/rss",
    },
    "meta-ai": {
        "name": "Meta AI",
        "url": "https://ai.meta.com/blog/",
        "rss": "https://ai.meta.com/blog/rss.xml",
    },
    "deepmind": {
        "name": "DeepMind",
        "url": "https://deepmind.google/blog/",
        "rss": None,  # 无 RSS
    },
    "microsoft-ai": {
        "name": "Microsoft AI",
        "url": "https://www.microsoft.com/en-us/ai",
        "rss": None,
    },
    "aws-ai": {
        "name": "AWS AI",
        "url": "https://aws.amazon.com/blogs/machine-learning/",
        "rss": "https://aws.amazon.com/blogs/machine-learning/feed/",
    },
    "nvidia-ai": {
        "name": "NVIDIA AI",
        "url": "https://blogs.nvidia.com/blog/category/deep-learning/",
        "rss": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
    },
    "stability-ai": {
        "name": "Stability AI",
        "url": "https://stability.ai/blog",
        "rss": None,
    },
    "mistral": {
        "name": "Mistral AI",
        "url": "https://mistral.ai/news/",
        "rss": None,
    },
}


class AIBlogFetcher:
    """AI 博客抓取器"""
    
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
    
    def fetch_rss(self, blog_id: str) -> List[Dict]:
        """从 RSS 抓取"""
        if blog_id not in BLOGS:
            return []
        
        config = BLOGS[blog_id]
        rss_url = config.get("rss")
        if not rss_url:
            return []
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(rss_url, timeout=self.timeout)
                response.raise_for_status()
                
                # 解析 RSS
                articles = self._parse_rss(response.text, blog_id)
                logger.info(f"[{config['name']}] RSS: {len(articles)} 条")
                return articles
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[{config['name']}] RSS 抓取失败: {e}")
        
        return []
    
    def _parse_rss(self, content: str, blog_id: str) -> List[Dict]:
        """解析 RSS 内容"""
        from xml.etree import ElementTree as ET
        
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        try:
            root = ET.fromstring(content)
            for item in root.findall(".//item")[:10]:  # 取前 10 条
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
                    "source": BLOGS[blog_id]["name"],
                    "source_id": blog_id,
                    "published_at": pub_date,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_score(pub_date),
                })
        except Exception as e:
            logger.warning(f"RSS 解析失败: {e}")
        
        return articles
    
    def _calculate_score(self, pub_date: str) -> float:
        """计算热度分数（基于时间）"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            hours_ago = (datetime.now() - dt).total_seconds() / 3600
            # 越新分数越高
            return max(0, 100 - hours_ago * 5)
        except:
            return 50
    
    def fetch_html(self, blog_id: str) -> List[Dict]:
        """从 HTML 页面抓取"""
        if blog_id not in BLOGS:
            return []
        
        url = BLOGS[blog_id]["url"]
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                articles = self._parse_html(response.text, blog_id)
                logger.info(f"[{BLOGS[blog_id]['name']}] HTML: {len(articles)} 条")
                return articles
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[{BLOGS[blog_id]['name']}] HTML 抓取失败: {e}")
        
        return []
    
    def _parse_html(self, html: str, blog_id: str) -> List[Dict]:
        """解析 HTML 页面"""
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找文章链接 (各网站结构不同)
        selectors = {
            "deepmind": "a.post-link, article a[href*='/blog/']",
            "microsoft-ai": "a[href*='/blog/ai/']",
            "stability-ai": "a[href*='/blog/']",
            "mistral": "a[href*='/news/']",
        }
        
        selector = selectors.get(blog_id, "article a, .post a")
        links = soup.select(selector)[:10]
        
        seen = set()
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            
            if not href or not title or len(title) < 10:
                continue
            
            # 补全 URL
            if href.startswith("/"):
                href = f"https://{blog_id}.ai{href}"
            elif not href.startswith("http"):
                continue
            
            if href in seen:
                continue
            seen.add(href)
            
            articles.append({
                "title": title[:200],
                "url": href,
                "summary": "",
                "source": BLOGS[blog_id]["name"],
                "source_id": blog_id,
                "published_at": "",
                "timestamp": now.isoformat(),
                "hot_score": 50,
            })
        
        return articles
    
    def fetch_all(self, blog_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """
        抓取所有配置的博客
        
        Args:
            blog_ids: 指定博客 ID 列表，None 表示全部
        
        Returns:
            博客文章字典
        """
        if blog_ids is None:
            blog_ids = list(BLOGS.keys())
        
        results = {}
        
        for blog_id in blog_ids:
            if blog_id not in BLOGS:
                continue
            
            # 优先使用 RSS
            articles = self.fetch_rss(blog_id)
            
            # 如果 RSS 失败，使用 HTML
            if not articles:
                articles = self.fetch_html(blog_id)
            
            if articles:
                results[blog_id] = articles
        
        return results
    
    def get_hotspots(self, limit: int = 30) -> List[Dict]:
        """获取热点文章"""
        all_articles = []
        
        for blog_id, articles in self.fetch_all().items():
            all_articles.extend(articles)
        
        # 按热度排序
        all_articles.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
        
        return all_articles[:limit]


# 全局实例
ai_blog_fetcher = AIBlogFetcher()


def fetch_ai_blogs(blog_ids: List[str] = None) -> Dict[str, List[Dict]]:
    """抓取 AI 博客"""
    return ai_blog_fetcher.fetch_all(blog_ids)


def fetch_ai_blog_hotspots(limit: int = 30) -> List[Dict]:
    """获取 AI 博客热点"""
    return ai_blog_fetcher.get_hotspots(limit)


def get_supported_blogs() -> List[Dict]:
    """获取支持的博客列表"""
    return [
        {"id": k, "name": v["name"], "url": v["url"]}
        for k, v in BLOGS.items()
    ]
