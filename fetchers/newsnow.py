# -*- coding: utf-8 -*-
"""
NewsNow API 抓取器

从 newsnow.busiyi.world 获取中文热点数据

支持的平台:
- 今日头条 (toutiao)
- 百度热搜 (baidu)
- 微博 (weibo)
- 抖音 (douyin)
- 知乎 (zhihu)
- B站 (bilibili)
- 华尔街见闻 (wallstreetcn-hot)
- 财联社 (cls-hot)
- 36氪 (36kr)
- 虎扑 (hupu)
- 贴吧 (tieba)
- 什么值得买 (smzdm)
- V2EX (v2ex)
- 掘金 (juejin)
- 雪球 (xueqiu)
- 澎湃新闻 (thepaper)
- 凤凰网 (ifeng)
- 爱奇艺 (iqiyi)
- 快手 (kuaishou)
- 腾讯视频 (qqvideo)
"""

import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import requests
from pytz import timezone

from ..utils.logger import get_logger

logger = get_logger(__name__)


# NewsNow API 配置
NEWSNOW_BASE_URL = "https://newsnow.busiyi.world/api"

# 支持的平台列表
SUPPORTED_PLATFORMS = {
    "toutiao": "今日头条",
    "baidu": "百度热搜",
    "weibo": "微博",
    "douyin": "抖音",
    "zhihu": "知乎",
    "bilibili": "bilibili 热搜",
    "wallstreetcn-hot": "华尔街见闻",
    "cls-hot": "财联社",
    "36kr": "36氪",
    "hupu": "虎扑",
    "tieba": "贴吧",
    "smzdm": "什么值得买",
    "v2ex": "V2EX",
    "juejin": "掘金",
    "xueqiu": "雪球",
    "thepaper": "澎湃新闻",
    "ifeng": "凤凰网",
    "iqiyi": "爱奇艺",
    "kuaishou": "快手",
    "qqvideo": "腾讯视频",
    "github": "GitHub Trending",
    "hackernews": "Hacker News",
    "producthunt": "Product Hunt",
}


class NewsNowFetcher:
    """NewsNow 热点数据获取器"""
    
    def __init__(
        self,
        proxy_url: Optional[str] = None,
        request_interval: int = 1000,
        max_retries: int = 2,
    ):
        """
        初始化
        
        Args:
            proxy_url: 代理 URL
            request_interval: 请求间隔 (毫秒)
            max_retries: 最大重试次数
        """
        self.proxy_url = proxy_url
        self.request_interval = request_interval
        self.max_retries = max_retries
    
    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if self.proxy_url:
            return {"http": self.proxy_url, "https": self.proxy_url}
        return None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }
    
    def fetch_platform(
        self,
        platform_id: str,
        latest: bool = True,
    ) -> Tuple[Optional[List[Dict]], str, bool]:
        """
        获取单个平台的热数据
        
        Args:
            platform_id: 平台 ID
            latest: 是否获取最新数据
        
        Returns:
            (数据列表, 状态消息, 是否成功)
        """
        url = f"{NEWSNOW_BASE_URL}/s"
        params = {
            "id": platform_id,
            "latest": "true" if latest else "false",
        }
        
        proxies = self._get_proxies()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    proxies=proxies,
                    headers=self._get_headers(),
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status", "unknown")
                
                if status in ["success", "cache"]:
                    items = data.get("items", [])
                    logger.info(f"获取 {platform_id} 成功: {len(items)} 条")
                    return items, f"{status} ({len(items)} 条)", True
                else:
                    logger.warning(f"{platform_id} 状态异常: {status}")
                    return [], f"状态异常: {status}", False
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = random.uniform(3, 5) + attempt * random.uniform(1, 2)
                    logger.warning(f"{platform_id} 请求失败: {e}, {wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{platform_id} 请求失败: {e}")
                    return None, str(e), False
            except json.JSONDecodeError as e:
                logger.error(f"{platform_id} JSON 解析失败: {e}")
                return None, str(e), False
        
        return None, "重试次数耗尽", False
    
    def fetch_multiple(
        self,
        platform_ids: List[str],
        progress_interval: int = 5,
    ) -> Dict[str, List[Dict]]:
        """
        获取多个平台的数据
        
        Args:
            platform_ids: 平台 ID 列表
            progress_interval: 进度报告间隔
        
        Returns:
            平台数据字典 {platform_id: items}
        """
        results = {}
        total = len(platform_ids)
        
        for i, platform_id in enumerate(platform_ids, 1):
            items, status, success = self.fetch_platform(platform_id)
            
            if success and items:
                # 添加平台信息到每个 item
                for item in items:
                    item["source_platform"] = platform_id
                    item["source_name"] = SUPPORTED_PLATFORMS.get(
                        platform_id, platform_id
                    )
                
                results[platform_id] = items
            else:
                logger.warning(f"[{i}/{total}] {platform_id}: {status}")
            
            # 避免请求过快
            if i < total:
                actual_interval = self.request_interval + random.randint(-10, 20)
                actual_interval = max(500, actual_interval)
                time.sleep(actual_interval / 1000)
        
        return results
    
    def fetch_all_supported(
        self,
        enabled_platforms: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict]]:
        """
        获取所有支持平台的数据
        
        Args:
            enabled_platforms: 启用的平台列表，None 表示全部
        
        Returns:
            平台数据字典
        """
        if enabled_platforms is None:
            platform_ids = list(SUPPORTED_PLATFORMS.keys())
        else:
            platform_ids = [
                p for p in enabled_platforms if p in SUPPORTED_PLATFORMS
            ]
        
        logger.info(f"开始获取 {len(platform_ids)} 个平台的数据...")
        return self.fetch_multiple(platform_ids)
    
    def normalize_articles(
        self,
        platform_data: Dict[str, List[Dict]],
    ) -> List[Dict]:
        """
        将平台数据转换为统一格式
        
        Returns:
            标准化文章列表
        """
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        for platform_id, items in platform_data.items():
            source_name = SUPPORTED_PLATFORMS.get(platform_id, platform_id)
            
            for rank, item in enumerate(items, 1):
                article = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "mobile_url": item.get("mobileUrl", ""),
                    "source": source_name,
                    "source_id": platform_id,
                    "rank": rank,
                    "timestamp": now.isoformat(),
                    "hot_score": self._calculate_hot_score(item, rank),
                }
                articles.append(article)
        
        return articles
    
    def _calculate_hot_score(self, item: Dict, rank: int) -> float:
        """
        计算热度分数
        
        Args:
            item: 原始数据
            rank: 当前排名
        
        Returns:
            热度分数 (0-100)
        """
        # 基础分数：排名越高分数越高
        base_score = 100 - min(rank - 1, 99) * 1.0
        
        # 如果有热度值，使用热度值
        if "hot" in item:
            try:
                hot_value = float(item["hot"])
                base_score = max(base_score, min(hot_value, 100))
            except (ValueError, TypeError):
                pass
        
        return base_score


class NewsNowManager:
    """NewsNow 管理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.fetcher = NewsNowFetcher(
            proxy_url=self.config.get("proxy_url"),
            request_interval=self.config.get("request_interval", 1000),
            max_retries=self.config.get("max_retries", 2),
        )
    
    def get_hotspots(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        获取热点列表
        
        Args:
            platforms: 平台列表，None 表示全部
            limit: 返回数量限制
        
        Returns:
            热点列表
        """
        # 获取数据
        platform_data = self.fetcher.fetch_all_supported(platforms)
        
        # 标准化
        articles = self.fetcher.normalize_articles(platform_data)
        
        # 按热度排序
        articles.sort(key=lambda x: (-x["hot_score"], x["rank"]))
        
        return articles[:limit]
    
    def get_platforms(self) -> Dict[str, str]:
        """获取支持的平台列表"""
        return SUPPORTED_PLATFORMS.copy()


# 全局实例
newsnow_manager = NewsNowManager()


def fetch_newsnow_hotspots(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Dict]:
    """获取 NewsNow 热点"""
    return newsnow_manager.get_hotspots(platforms, limit)
