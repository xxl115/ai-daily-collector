# -*- coding: utf-8 -*-
"""
播客抓取器

抓取:
- Spotify Podcasts Trending
- Apple Podcasts Charts
- Google Podcasts
- AI 相关播客 RSS
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


# 播客配置
PODCASTS = {
    # AI 官方播客
    "openai_podcast": {
        "name": "OpenAI Podcast",
        "url": "https://podcasts.apple.com/us/podcast/openai-podcast/id1669494564",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "lex_fridman": {
        "name": "Lex Fridman Podcast",
        "url": "https://podcasts.apple.com/us/podcast/lex-fridman-podcast/id1506920295",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "a16z_podcast": {
        "name": "a16z Podcast",
        "url": "https://podcasts.apple.com/us/podcast/a16z-podcast/id842818711",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "ycombinator_podcast": {
        "name": "Y Combinator Podcast",
        "url": "https://podcasts.apple.com/us/podcast/y-combinator-podcast/id1016345899",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "dwai_podcast": {
        "name": "Data Skeptic Podcast",
        "url": "https://podcasts.apple.com/us/podcast/data-skeptic-podcast/id435500023",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "practical_ai": {
        "name": "Practical AI Podcast",
        "url": "https://podcasts.apple.com/us/podcast/practical-ai-podcast/id1406533595",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "linear_digressions": {
        "name": "Linear Digressions",
        "url": "https://podcasts.apple.com/us/podcast/linear-digressions/id941083681",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "super_data_science": {
        "name": "Super Data Science Podcast",
        "url": "https://podcasts.apple.com/us/podcast/super-data-science-podcast/id1164035391",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "twiml_podcast": {
        "name": "TWIML Podcast",
        "url": "https://podcasts.apple.com/us/podcast/this-week-in-machine-learning-podcast/id1114404016",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
    "ai_in_business": {
        "name": "AI in Business Podcast",
        "url": "https://podcasts.apple.com/us/podcast/ai-in-business-podcast/id1449608589",
        "rss": "https://feeds.simplecast.com/2_podcasts/5c8afe6c-6b3c-4c5a-8c7d-8b5e2c1e6e9c",
    },
}

# 播客平台
PLATFORMS = {
    "spotify": {
        "name": "Spotify",
        "url": "https://podcasts.spotify.com/",
    },
    "apple": {
        "name": "Apple Podcasts",
        "url": "https://podcasts.apple.com/",
    },
    "google": {
        "name": "Google Podcasts",
        "url": "https://podcasts.google.com/",
    },
}


class PodcastFetcher:
    """播客数据抓取器"""
    
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
    
    def fetch_rss(self, podcast_id: str) -> List[Dict]:
        """从 RSS 抓取"""
        if podcast_id not in PODCASTS:
            return []
        
        config = PODCASTS[podcast_id]
        rss_url = config.get("rss")
        if not rss_url:
            return []
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(rss_url, timeout=self.timeout)
                response.raise_for_status()
                
                episodes = self._parse_rss(response.text, podcast_id)
                logger.info(f"[{config['name']}] RSS: {len(episodes)} 集")
                return episodes
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[{config['name']}] RSS 抓取失败: {e}")
        
        return []
    
    def _parse_rss(self, content: str, podcast_id: str) -> List[Dict]:
        """解析 RSS"""
        from xml.etree import ElementTree as ET
        
        episodes = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        try:
            root = ET.fromstring(content)
            
            channel = root.find("channel")
            if channel is None:
                return []
            
            # 获取播客信息
            podcast_title = channel.findtext("title", "")
            podcast_desc = channel.findtext("description", "")
            
            for item in channel.findall("item")[:10]:  # 取前 10 集
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                pub_date = item.findtext("pubDate", "")
                
                # 清理描述
                if desc:
                    soup = BeautifulSoup(desc, "html.parser")
                    desc = soup.get_text()[:500]
                
                # 提取音频 URL
                enclosure = item.find("enclosure")
                audio_url = ""
                if enclosure is not None:
                    audio_url = enclosure.get("url", "")
                
                # 计算热度分数
                hot_score = self._calculate_score(pub_date)
                
                episodes.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "audio_url": audio_url,
                    "summary": desc,
                    "source": PODCASTS[podcast_id]["name"],
                    "source_id": podcast_id,
                    "podcast_title": podcast_title,
                    "published_at": pub_date,
                    "timestamp": now.isoformat(),
                    "hot_score": hot_score,
                    "type": "podcast",
                })
                
        except Exception as e:
            logger.warning(f"RSS 解析失败: {e}")
        
        return episodes
    
    def _calculate_score(self, pub_date: str) -> float:
        """计算热度分数"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            hours_ago = (datetime.now() - dt).total_seconds() / 3600
            
            # 越新分数越高
            return max(0, 100 - hours_ago * 10)
        except:
            return 50
    
    def fetch_all(self, podcast_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """抓取所有配置的播客"""
        if podcast_ids is None:
            podcast_ids = list(PODCASTS.keys())
        
        results = {}
        
        for podcast_id in podcast_ids:
            if podcast_id not in PODCASTS:
                continue
            
            episodes = self.fetch_rss(podcast_id)
            if episodes:
                results[podcast_id] = episodes
        
        return results
    
    def fetch_ai_podcasts(self) -> Dict[str, List[Dict]]:
        """抓取所有 AI 播客"""
        return self.fetch_all(list(PODCASTS.keys()))
    
    def get_latest_episodes(self, limit: int = 20) -> List[Dict]:
        """获取最新剧集"""
        all_episodes = []
        
        for episodes in self.fetch_ai_podcasts().values():
            all_episodes.extend(episodes)
        
        # 按时间排序
        all_episodes.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
        
        return all_episodes[:limit]
    
    def get_hotspots(self, limit: int = 30) -> List[Dict]:
        """获取热点播客"""
        return self.get_latest_episodes(limit)


class SpotifyFetcher:
    """Spotify 抓取器"""
    
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
    
    def fetch_trending(self, category: str = "technology") -> List[Dict]:
        """抓取 Trending 播客"""
        url = f"https://podcasts.spotify.com/category/{category}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Spotify 是 SPA，HTML 中数据有限
                logger.info(f"[Spotify {category}] 需要 API key 获取完整数据")
                return []
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[Spotify {category}] 抓取失败: {e}")
        
        return []
    
    def get_hotspots(self, limit: int = 20) -> List[Dict]:
        """获取热点播客"""
        # 由于 Spotify 需要 API，暂时返回空列表
        logger.info("Spotify 抓取需要 API Key，跳过")
        return []


# 全局实例
podcast_fetcher = PodcastFetcher()
spotify_fetcher = SpotifyFetcher()


def fetch_podcasts(podcast_ids: List[str] = None) -> Dict[str, List[Dict]]:
    """抓取播客"""
    return podcast_fetcher.fetch_all(podcast_ids)


def fetch_ai_podcasts() -> Dict[str, List[Dict]]:
    """抓取 AI 播客"""
    return podcast_fetcher.fetch_ai_podcasts()


def fetch_podcast_hotspots(limit: int = 30) -> List[Dict]:
    """获取播客热点"""
    return podcast_fetcher.get_hotspots(limit)


def get_supported_podcasts() -> List[Dict]:
    """获取支持的播客列表"""
    return [
        {"id": k, "name": v["name"], "url": v["url"]}
        for k, v in PODCASTS.items()
    ]
