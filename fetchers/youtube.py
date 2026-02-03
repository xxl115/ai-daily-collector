# -*- coding: utf-8 -*-
"""
YouTube 抓取器

抓取:
- YouTube Trending (各国)
- YouTube 频道视频
- YouTube 搜索结果
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from pytz import timezone

from .logger import get_logger

logger = get_logger(__name__)


# YouTube 配置
YOUTUBE_CONFIG = {
    "trending": {
        "name": "YouTube Trending",
        "url": "https://www.youtube.com/feed/trending",
        "region": "GLOBAL",
    },
    "trending_us": {
        "name": "YouTube Trending (US)",
        "url": "https://www.youtube.com/feed/trending?bp=4gINGGt5eG11ZW5sbmVQeQ%3D%3D",
        "region": "US",
    },
    "trending_cn": {
        "name": "YouTube Trending (Taiwan)",
        "url": "https://www.youtube.com/feed/trending?bp=4gINGGt5eG11ZW5sbmVQeQ%3D%3D",
        "region": "TW",
    },
    "ai_education": {
        "name": "AI & Education",
        "url": "https://www.youtube.com/results?search_query=AI+machine+learning+course",
        "category": "education",
    },
    "tech_reviews": {
        "name": "Tech Reviews",
        "url": "https://www.youtube.com/results?search_query=tech+review+AI",
        "category": "tech",
    },
}

# AI 相关频道
AI_CHANNELS = {
    "lex-fridman": "UC2TX-_23AbJ5X5j3nF8F5w",
    "mKB3qZ6QQ2I": "Two Minute Papers",
    "3Blue1Brown": "3Blue1Brown",
    "statquest": "StatQuest with Josh Starmer",
    "sentdex": "sentdex",
    "AndrejKarpathy": "Andrej Karpathy",
    "YannicKilcher": "Yannic Kilcher",
    "DavidShapiro": "David Shapiro",
    "BrandonRoth": "Brandon Roth",
    "AIEngineer": "AI Engineer",
}


class YouTubeFetcher:
    """YouTube 数据抓取器"""
    
    def __init__(
        self,
        api_key: str = None,
        timeout: int = 30,
        max_retries: int = 2,
    ):
        """
        初始化
        
        Args:
            api_key: YouTube Data API Key (可选，有 API 时更稳定)
            timeout: 请求超时
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def fetch_trending(self, region: str = "GLOBAL") -> List[Dict]:
        """
        抓取 Trending 视频
        
        Args:
            region: 地区 (GLOBAL, US, TW, etc.)
        
        Returns:
            视频列表
        """
        if region == "GLOBAL":
            url = YOUTUBE_CONFIG["trending"]["url"]
        elif region == "US":
            url = YOUTUBE_CONFIG["trending_us"]["url"]
        else:
            url = YOUTUBE_CONFIG["trending"]["url"]
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # 提取视频数据
                videos = self._parse_trending(response.text, region)
                logger.info(f"[YouTube Trending {region}] 获取 {len(videos)} 条")
                return videos
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[YouTube Trending {region}] 抓取失败: {e}")
        
        return []
    
    def _parse_trending(self, html: str, region: str) -> List[Dict]:
        """解析 Trending 页面"""
        videos = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        # 从 HTML 中提取 ytInitialData
        try:
            # 查找 ytInitialData
            import re
            pattern = r'ytInitialData\s*=\s*({.+?});'
            match = re.search(pattern, html)
            
            if not match:
                # 备用: 查找 var 声明
                pattern = r'var\s+ytInitialData\s*=\s*({.+?});'
                match = re.search(pattern, html)
            
            if match:
                data = json.loads(match.group(1))
                
                # 遍历数据结构
                contents = data.get("contents", {})
                two_col = contents.get("twoColumnBrowseResultsRenderer", {})
                tabs = two_col.get("tabs", [])
                
                for tab in tabs:
                    tab_renderer = tab.get("tabRenderer", {})
                    content = tab_renderer.get("content", {})
                    section_list = content.get("sectionListRenderer", {})
                    contents = section_list.get("contents", {})
                    
                    for item in contents:
                        rich_item = item.get("richItemRenderer", {})
                        content_renderer = rich_item.get("content", {})
                        video_renderer = content_renderer.get("videoRenderer", {})
                        
                        if video_renderer:
                            video = self._extract_video(video_renderer, region, now)
                            if video:
                                videos.append(video)
                
                # 只取前 10 个
                videos = videos[:10]
                
        except Exception as e:
            logger.warning(f"解析 YouTube Trending 失败: {e}")
        
        return videos
    
    def _extract_video(self, renderer: Dict, region: str, now: datetime) -> Optional[Dict]:
        """提取视频信息"""
        try:
            video_id = renderer.get("videoId", "")
            if not video_id:
                return None
            
            title_renderer = renderer.get("title", {})
            title = ""
            if "runs" in title_renderer:
                title = "".join(
                    run.get("text", "")
                    for run in title_renderer["runs"]
                )
            
            # 缩略图
            thumbnail = ""
            thumbs = renderer.get("thumbnail", {}).get("thumbnails", [])
            if thumbs:
                thumbnail = thumbs[-1].get("url", "")
            
            # 频道信息
            channel_renderer = renderer.get("longBylineRenderer", {}).get("runs", [{}])
            channel_name = ""
            channel_url = ""
            if channel_renderer:
                channel_name = channel_renderer[0].get("text", "")
                navigation = channel_renderer[0].get("navigationEndpoint", {})
                browse = navigation.get("browseEndpoint", {})
                channel_url = f"https://youtube.com/channel/{browse.get('browseId', '')}"
            
            # 视图数
            view_count_text = ""
            view_count = 0
            if "viewCountText" in renderer:
                view_count_text = renderer["viewCountText"].get("simpleText", "")
                # 提取数字
                import re
                nums = re.findall(r"[\d,]+", view_count_text)
                if nums:
                    try:
                        view_count = int(nums[0].replace(",", ""))
                    except:
                        pass
            
            # 发布时间
            published_text = ""
            if "publishedTimeText" in renderer:
                published_text = renderer["publishedTimeText"].get("simpleText", "")
            
            # 计算热度分数
            hot_score = self._calculate_hot_score(view_count, published_text)
            
            return {
                "title": title[:200],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "thumbnail": thumbnail,
                "channel": channel_name,
                "channel_url": channel_url,
                "view_count": view_count,
                "view_count_text": view_count_text,
                "published_text": published_text,
                "source": f"YouTube Trending ({region})",
                "source_id": f"youtube_trending_{region.lower()}",
                "timestamp": now.isoformat(),
                "hot_score": hot_score,
            }
            
        except Exception as e:
            logger.warning(f"提取视频信息失败: {e}")
            return None
    
    def _calculate_hot_score(self, view_count: int, published_text: str) -> float:
        """计算热度分数"""
        # 视图数基础分 (0-50)
        score = min(view_count / 10000, 50) if view_count > 0 else 0
        
        # 新鲜度加分 (0-50)
        if "hour" in published_text:
            score += 50
        elif "day" in published_text:
            days = 1
            try:
                import re
                nums = re.findall(r"\d+", published_text)
                if nums:
                    days = int(nums[0])
            except:
                pass
            score += max(0, 50 - days * 5)
        elif "week" in published_text:
            score += 20
        elif "month" in published_text:
            score += 10
        else:
            score += 5
        
        return min(score, 100)
    
    def fetch_channel_videos(self, channel_id: str, limit: int = 10) -> List[Dict]:
        """
        抓取频道最新视频
        
        Args:
            channel_id: 频道 ID
            limit: 返回数量
        
        Returns:
            视频列表
        """
        # 使用非 API 方式抓取
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                videos = self._parse_channel_videos(response.text, channel_id)
                logger.info(f"[YouTube Channel {channel_id}] 获取 {len(videos)} 条")
                return videos[:limit]
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[YouTube Channel {channel_id}] 抓取失败: {e}")
        
        return []
    
    def _parse_channel_videos(self, html: str, channel_id: str) -> List[Dict]:
        """解析频道视频页面"""
        videos = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        try:
            import re
            pattern = r'ytInitialData\s*=\s*({.+?});'
            match = re.search(pattern, html)
            
            if match:
                data = json.loads(match.group(1))
                
                # 提取视频列表
                contents = data.get("contents", {})
                two_col = contents.get("twoColumnBrowseResultsRenderer", {})
                tabs = two_col.get("tabs", [])
                
                for tab in tabs:
                    tab_renderer = tab.get("tabRenderer", {})
                    if tab_renderer.get("selected"):
                        content = tab_renderer.get("content", {})
                        section_list = content.get("sectionListRenderer", {})
                        contents = section_list.get("contents", [])
                        
                        for item in contents:
                            item_renderer = item.get("itemSectionRenderer", {})
                            contents2 = item_renderer.get("contents", [])
                            
                            for item2 in contents2:
                                grid_renderer = item2.get("gridRenderer", {})
                                items = grid_renderer.get("items", [])
                                
                                for grid_item in items:
                                    video_renderer = grid_item.get("gridVideoRenderer", {})
                                    
                                    if video_renderer:
                                        video = self._extract_grid_video(video_renderer, channel_id, now)
                                        if video:
                                            videos.append(video)
                
        except Exception as e:
            logger.warning(f"解析频道视频失败: {e}")
        
        return videos
    
    def _extract_grid_video(self, renderer: Dict, channel_id: str, now: datetime) -> Optional[Dict]:
        """提取网格视频信息"""
        try:
            video_id = renderer.get("videoId", "")
            if not video_id:
                return None
            
            title_renderer = renderer.get("title", {})
            title = ""
            if "runs" in title_renderer:
                title = "".join(
                    run.get("text", "")
                    for run in title_renderer["runs"]
                )
            
            # 缩略图
            thumbnail = ""
            thumbs = renderer.get("thumbnail", {}).get("thumbnails", [])
            if thumbs:
                thumbnail = thumbs[-1].get("url", "")
            
            # 视图数和发布时间
            view_count_text = ""
            view_count = 0
            if "viewCountText" in renderer:
                view_count_text = renderer["viewCountText"].get("simpleText", "")
                import re
                nums = re.findall(r"[\d,]+", view_count_text)
                if nums:
                    try:
                        view_count = int(nums[0].replace(",", ""))
                    except:
                        pass
            
            published_text = ""
            if "publishedTimeText" in renderer:
                published_text = renderer["publishedTimeText"].get("simpleText", "")
            
            return {
                "title": title[:200],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "thumbnail": thumbnail,
                "view_count": view_count,
                "view_count_text": view_count_text,
                "published_text": published_text,
                "source": "YouTube Channel",
                "source_id": f"youtube_channel_{channel_id}",
                "timestamp": now.isoformat(),
                "hot_score": self._calculate_hot_score(view_count, published_text),
            }
            
        except Exception as e:
            return None
    
    def fetch_search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索视频
        
        Args:
            query: 搜索关键词
            limit: 返回数量
        """
        url = f"https://www.youtube.com/results?search_query={query}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                videos = self._parse_search(response.text, query)
                logger.info(f"[YouTube Search {query}] 获取 {len(videos)} 条")
                return videos[:limit]
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    logger.warning(f"[YouTube Search {query}] 抓取失败: {e}")
        
        return []
    
    def _parse_search(self, html: str, query: str) -> List[Dict]:
        """解析搜索结果"""
        videos = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        try:
            import re
            pattern = r'ytInitialData\s*=\s*({.+?});'
            match = re.search(pattern, html)
            
            if match:
                data = json.loads(match.group(1))
                
                contents = data.get("contents", {})
                two_col = contents.get("twoColumnSearchResultsRenderer", {})
                primary = two_col.get("primary", {})
                sections = primary.get("sections", [])
                
                for section in sections:
                    section_renderer = section.get("sectionRenderer", {})
                    contents2 = section_renderer.get("contents", [])
                    
                    for item in contents2:
                        video_renderer = item.get("videoRenderer", {})
                        
                        if video_renderer:
                            video = self._extract_video(video_renderer, query, now)
                            if video:
                                videos.append(video)
                
        except Exception as e:
            logger.warning(f"解析搜索结果失败: {e}")
        
        return videos
    
    def get_ai_trending(self, limit: int = 20) -> List[Dict]:
        """获取 AI 相关 Trending"""
        all_videos = []
        
        # 抓取全局 Trending
        trending = self.fetch_trending("GLOBAL")
        all_videos.extend(trending)
        
        # 抓取 US Trending
        trending_us = self.fetch_trending("US")
        all_videos.extend(trending_us)
        
        # AI 关键词搜索
        ai_videos = self.fetch_search("AI+machine+learning", 10)
        all_videos.extend(ai_videos)
        
        # 去重
        seen = set()
        unique = []
        for video in all_videos:
            if video["video_id"] not in seen:
                seen.add(video["video_id"])
                unique.append(video)
        
        # 按热度排序
        unique.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
        
        return unique[:limit]
    
    def get_hotspots(self, limit: int = 30) -> List[Dict]:
        """获取热点视频"""
        return self.get_ai_trending(limit)


# 全局实例
youtube_fetcher = YouTubeFetcher()


def fetch_youtube_trending(region: str = "GLOBAL") -> List[Dict]:
    """抓取 YouTube Trending"""
    return youtube_fetcher.fetch_trending(region)


def fetch_youtube_search(query: str, limit: int = 10) -> List[Dict]:
    """搜索 YouTube"""
    return youtube_fetcher.fetch_search(query, limit)


def fetch_youtube_ai_trending(limit: int = 20) -> List[Dict]:
    """获取 AI 相关热点"""
    return youtube_fetcher.get_ai_trending(limit)


def fetch_youtube_hotspots(limit: int = 30) -> List[Dict]:
    """获取 YouTube 热点"""
    return youtube_fetcher.get_hotspots(limit)


def get_ai_channels() -> List[Dict]:
    """获取 AI 相关频道"""
    return [
        {"id": k, "name": v, "url": f"https://www.youtube.com/channel/{k}"}
        for k, v in AI_CHANNELS.items()
    ]
