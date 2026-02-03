# -*- coding: utf-8 -*-
"""
V2EX 热门抓取器

从 v2ex.com 获取技术社区热门话题

API:
- https://www.v2ex.com/api/v2/tabs/hot
- https://www.v2ex.com/api/v2/topics/hot
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import requests
from pytz import timezone

from utils.logger import get_logger

logger = get_logger(__name__)


# V2EX API 配置
V2EX_API_BASE = "https://www.v2ex.com/api/v2"
V2EX_BASE_URL = "https://www.v2ex.com"

# V2EX 节点分类
NODE_CATEGORIES = {
    "分享": "share",
    "问答": "qna",
    "创造": "creative",
    "酷工作": "jobs",
    "交易": "deals",
    "城市": "city",
    "关注": "hot",
}


class V2EXFetcher:
    """V2EX 数据获取器"""
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 2,
    ):
        """
        初始化
        
        Args:
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": V2EX_BASE_URL,
        }
    
    def fetch_hot_topics(self, limit: int = 30) -> Tuple[List[Dict], bool]:
        """
        获取热门话题
        
        Args:
            limit: 返回数量
        
        Returns:
            (话题列表, 是否成功)
        """
        url = f"{V2EX_API_BASE}/topics/hot"
        params = {"limit": min(limit, 50)}
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                
                data = response.json()
                topics = data.get("results", data if isinstance(data, list) else [])
                
                logger.info(f"V2EX 热门话题: {len(topics)} 条")
                return topics, True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    logger.warning(f"V2EX 请求失败: {e}, 重试...")
                    time.sleep(2)
                else:
                    logger.error(f"V2EX 请求失败: {e}")
                    return [], False
            except json.JSONDecodeError as e:
                logger.error(f"V2EX JSON 解析失败: {e}")
                return [], False
        
        return [], False
    
    def fetch_recent_topics(
        self,
        node: Optional[str] = None,
        limit: int = 30,
    ) -> Tuple[List[Dict], bool]:
        """
        获取最新话题
        
        Args:
            node: 节点名称 (如 "python", "ai")
            limit: 返回数量
        
        Returns:
            (话题列表, 是否成功)
        """
        url = f"{V2EX_API_BASE}/topics"
        params = {
            "limit": min(limit, 50),
            "node_slug": node,
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            topics = data.get("results", data if isinstance(data, list) else [])
            
            logger.info(f"V2EX 最新话题 ({node or '全部'}): {len(topics)} 条")
            return topics, True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"V2EX 请求失败: {e}")
            return [], False
        except json.JSONDecodeError as e:
            logger.error(f"V2EX JSON 解析失败: {e}")
            return [], False
    
    def fetch_node_info(self, node_slug: str) -> Tuple[Optional[Dict], bool]:
        """
        获取节点信息
        
        Args:
            node_slug: 节点别名
        
        Returns:
            (节点信息, 是否成功)
        """
        url = f"{V2EX_API_BASE}/nodes/{node_slug}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json(), True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"V2EX 节点请求失败: {e}")
            return None, False
    
    def normalize_articles(
        self,
        topics: List[Dict],
        topic_type: str = "hot",
    ) -> List[Dict]:
        """
        转换为标准化格式
        
        Args:
            topics: 原始话题列表
            topic_type: 话题类型 (hot/recent)
        
        Returns:
            标准化文章列表
        """
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        for rank, topic in enumerate(topics, 1):
            # 解析时间
            created_time = topic.get("created", "")
            if created_time:
                try:
                    # V2EX 时间格式: 2026-02-03T08:00:00.000000+08:00
                    created_dt = datetime.fromisoformat(
                        created_time.replace("+08:00", "+00:00")
                    ).astimezone(beijing_tz)
                    time_diff = (now - created_dt).total_seconds() / 3600
                except ValueError:
                    time_diff = 0
            else:
                time_diff = 0
            
            # 计算热度分数
            hot_score = self._calculate_hot_score(
                topic.get("replies", 0),
                topic.get("views", 0),
                time_diff,
                rank,
            )
            
            article = {
                "title": topic.get("title", ""),
                "url": f"{V2EX_BASE_URL}/t/{topic.get('id', '')}",
                "source": "V2EX",
                "source_id": "v2ex",
                "rank": rank,
                "timestamp": now.isoformat(),
                "hot_score": hot_score,
                "replies": topic.get("replies", 0),
                "views": topic.get("views", 0),
                "node": topic.get("node", {}).get("title", ""),
                "member": topic.get("member", {}).get("username", ""),
                "time_diff_hours": round(time_diff, 1) if time_diff else None,
                "content": topic.get("content", "")[:200] if topic.get("content") else "",
                "topic_type": topic_type,
            }
            articles.append(article)
        
        return articles
    
    def _calculate_hot_score(
        self,
        replies: int,
        views: int,
        time_diff_hours: float,
        rank: int,
    ) -> float:
        """
        计算热度分数
        
        公式: (回复数 * 2 + 浏览量/100) / (时间 + 2) + 排名奖励
        """
        if time_diff_hours <= 0:
            time_diff_hours = 0.1
        
        # 基础热度
        base_score = (replies * 2 + views / 100) / (time_diff_hours + 1)
        
        # 排名奖励
        rank_bonus = max(0, 100 - rank * 2) / 10
        
        # 限制最大值
        hot_score = min(base_score + rank_bonus, 100)
        
        return round(hot_score, 2)
    
    def get_hotspots(self, limit: int = 30) -> List[Dict]:
        """获取 V2EX 热门"""
        topics, success = self.fetch_hot_topics(limit)
        if not success:
            return []
        return self.normalize_articles(topics, "hot")


class V2EXManager:
    """V2EX 管理器"""
    
    def __init__(self):
        self.fetcher = V2EXFetcher()
    
    def get_hotspots(self, limit: int = 30, node: str = None) -> List[Dict]:
        """获取热点列表"""
        if node:
            topics, _ = self.fetch_recent_topics(node, limit)
            return self.fetcher.normalize_articles(topics, f"recent_{node}")
        return self.fetcher.get_hotspots(limit)
    
    def get_popular_nodes(self) -> List[Dict]:
        """获取热门节点"""
        return [
            {"id": "python", "name": "Python", "count": "10k+"},
            {"id": "programming", "name": "编程", "count": "20k+"},
            {"id": "ai", "name": "人工智能", "count": "5k+"},
            {"id": "machine-learning", "name": "机器学习", "count": "3k+"},
            {"id": "jobs", "name": "酷工作", "count": "15k+"},
            {"id": "share", "name": "分享", "count": "50k+"},
            {"id": "qna", "name": "问答", "count": "30k+"},
            {"id": "macos", "name": "macOS", "count": "8k+"},
        ]


# 全局实例
v2ex_manager = V2EXManager()


def fetch_v2ex_hotspots(limit: int = 30) -> List[Dict]:
    """获取 V2EX 热门"""
    return v2ex_manager.get_hotspots(limit)
