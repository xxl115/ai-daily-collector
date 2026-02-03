# -*- coding: utf-8 -*-
"""
Reddit 热门抓取器

从 reddit.com 获取热门帖子

API: https://www.reddit.com/r/{subreddit}/hot.json
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from pytz import timezone

from ..utils.logger import get_logger

logger = get_logger(__name__)


# Reddit API 配置
REDDIT_BASE_URL = "https://www.reddit.com"

# 默认订阅的子版块
DEFAULT_SUBREDDITS = {
    "programming": "Programming",
    "technology": "Technology",
    "artificial": "Artificial",
    "MachineLearning": "MachineLearning",
    "computervision": "ComputerVision",
    "deeplearning": "DeepLearning",
    "dataisbeautiful": "DataIsBeautiful",
    "opensource": "OpenSource",
    "github": "GitHub",
    "python": "Python",
    "javascript": "JavaScript",
    "webdev": "webdev",
    "learnprogramming": "learnprogramming",
    "technology": "Technology",
    "futurism": "Futurism",
    "science": "Science",
}


class RedditFetcher:
    """Reddit 数据获取器"""
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 2,
        user_agent: str = "AI-Daily-Collector/1.0",
    ):
        """
        初始化
        
        Args:
            timeout: 请求超时时间
            max_retries: 最大重试次数
            user_agent: 用户代理
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    def fetch_subreddit_hot(
        self,
        subreddit: str,
        limit: int = 25,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str], bool]:
        """
        获取子版块热门帖子
        
        Args:
            subreddit: 子版块名称
            limit: 返回数量 (最大 100)
            after: 分页标记
        
        Returns:
            (帖子列表, 下一页标记, 是否成功)
        """
        url = f"{REDDIT_BASE_URL}/r/{subreddit}/hot.json"
        params = {
            "limit": min(limit, 100),
            "raw_json": 1,
        }
        if after:
            params["after"] = after
        
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
                posts = data.get("data", {}).get("children", [])
                
                # 获取下一页标记
                after = data.get("data", {}).get("after")
                
                logger.info(f"Reddit r/{subreddit}: {len(posts)} 条")
                return posts, after, True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    logger.warning(f"Reddit r/{subreddit} 请求失败: {e}, 重试...")
                    time.sleep(2)
                else:
                    logger.error(f"Reddit r/{subreddit} 请求失败: {e}")
                    return [], None, False
            except json.JSONDecodeError as e:
                logger.error(f"Reddit JSON 解析失败: {e}")
                return [], None, False
        
        return [], None, False
    
    def fetch_multiple_subreddits(
        self,
        subreddits: List[str],
        limit_per_sub: int = 10,
    ) -> Dict[str, List[Dict]]:
        """
        获取多个子版块的热门
        
        Args:
            subreddits: 子版块列表
            limit_per_sub: 每个子版块返回数量
        
        Returns:
            子版块帖子字典
        """
        results = {}
        
        for subreddit in subreddits:
            posts, _, success = self.fetch_subreddit_hot(subreddit, limit_per_sub)
            
            if success:
                normalized = self.normalize_posts(posts, subreddit)
                results[subreddit] = normalized
            else:
                results[subreddit] = []
            
            # 避免请求过快
            time.sleep(1)
        
        return results
    
    def fetch_all_hot(
        self,
        subreddits: Optional[List[str]] = None,
        total_limit: int = 50,
    ) -> List[Dict]:
        """
        获取所有子版块的热门（合并排序）
        
        Args:
            subreddits: 子版块列表，None 表示默认列表
            total_limit: 总返回数量
        
        Returns:
            合并排序后的帖子列表
        """
        if subreddits is None:
            subreddits = list(DEFAULT_SUBREDDITS.keys())
        
        all_posts = []
        seen_urls = set()
        
        # 限制每个子版块的数量
        limit_per_sub = min(20, max(10, total_limit // len(subreddits)))
        
        for subreddit in subreddits:
            posts, _, success = self.fetch_subreddit_hot(subreddit, limit_per_sub)
            
            if success:
                normalized = self.normalize_posts(posts, subreddit)
                
                # 去重
                for post in normalized:
                    if post["url"] not in seen_urls:
                        seen_urls.add(post["url"])
                        all_posts.append(post)
            
            time.sleep(1)
        
        # 按热度排序
        all_posts.sort(key=lambda x: x["hot_score"], reverse=True)
        
        return all_posts[:total_limit]
    
    def normalize_posts(
        self,
        posts: List[Dict],
        subreddit: str,
    ) -> List[Dict]:
        """
        转换为标准化格式
        
        Args:
            posts: 原始帖子列表
            subreddit: 子版块名称
        
        Returns:
            标准化文章列表
        """
        articles = []
        beijing_tz = timezone("Asia/Shanghai")
        now = datetime.now(beijing_tz)
        
        for rank, post_data in enumerate(posts, 1):
            post = post_data.get("data", {})
            
            # 解析时间
            created_utc = post.get("created_utc", 0)
            if created_utc:
                post_time = datetime.fromtimestamp(created_utc, tz=beijing_tz)
                time_diff_hours = (now - post_time).total_seconds() / 3600
            else:
                time_diff_hours = 0
                post_time = now
            
            # 获取缩略图
            thumbnail = post.get("thumbnail")
            if thumbnail and not thumbnail.startswith("http"):
                thumbnail = None
            
            # 获取预览图
            preview_images = post.get("preview", {}).get("images", [])
            preview_url = None
            if preview_images:
                preview_url = preview_images[0].get("source", {}).get("url")
            
            # 计算热度分数 (Reddit 算法近似)
            hot_score = self._calculate_hot_score(
                post.get("ups", 0),
                post.get("downs", 0),
                post.get("num_comments", 0),
                time_diff_hours,
                created_utc,
            )
            
            article = {
                "title": post.get("title", "")[:500],
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "source": f"r/{subreddit}",
                "source_id": f"reddit_{subreddit}",
                "rank": rank,
                "timestamp": post_time.isoformat(),
                "hot_score": hot_score,
                "upvotes": post.get("ups", 0),
                "downvotes": post.get("downs", 0),
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "time_diff_hours": round(time_diff_hours, 1),
                "thumbnail": thumbnail or preview_url,
                "selftext": post.get("selftext", "")[:500] if post.get("is_self") else "",
                "is_self": post.get("is_self", False),
                "over_18": post.get("over_18", False),
                "subreddit": subreddit,
            }
            articles.append(article)
        
        return articles
    
    def _calculate_hot_score(
        self,
        upvotes: int,
        downvotes: int,
        comments: int,
        time_diff_hours: float,
        created_utc: float,
    ) -> float:
        """
        计算热度分数 (参考 Reddit Hot 算法)
        
        公式: log10(max(|(ups - downs)|, 1)) + (sign(ups - downs) * seconds_since_epoch) / 45000
        """
        if time_diff_hours <= 0:
            time_diff_hours = 0.1
        
        # Reddit 热度算法近似
        score = upvotes - downvotes
        
        if score <= 0:
            base_score = 0
        else:
            # log10 缩放
            import math
            base_score = math.log10(max(score, 1)) * 10
        
        # 评论奖励
        comment_bonus = min(comments * 0.5, 20)
        
        # 新鲜度奖励
        freshness_bonus = max(0, 100 - time_diff_hours) / 20
        
        # 总分
        hot_score = min(base_score + comment_bonus + freshness_bonus, 100)
        
        return round(hot_score, 2)
    
    def get_subreddit_info(self, subreddit: str) -> Tuple[Optional[Dict], bool]:
        """获取子版块信息"""
        url = f"{REDDIT_BASE_URL}/r/{subreddit}/about.json"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("data", {}), True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Reddit 节点请求失败: {e}")
            return None, False


class RedditManager:
    """Reddit 管理器"""
    
    def __init__(self):
        self.fetcher = RedditFetcher()
    
    def get_hotspots(
        self,
        subreddits: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """获取热点列表"""
        return self.fetcher.fetch_all_hot(subreddits, limit)
    
    def get_popular_subreddits(self) -> List[Dict]:
        """获取热门子版块"""
        return [
            {"id": "programming", "name": "r/programming", "subscribers": "5M+"},
            {"id": "technology", "name": "r/technology", "subscribers": "15M+"},
            {"id": "artificial", "name": "r/artificial", "subscribers": "300K+"},
            {"id": "MachineLearning", "name": "r/MachineLearning", "subscribers": "3M+"},
            {"id": "python", "name": "r/python", "subscribers": "2M+"},
            {"id": "github", "name": "r/github", "subscribers": "500K+"},
            {"id": "opensource", "name": "r/opensource", "subscribers": "200K+"},
            {"id": "dataisbeautiful", "name": "r/dataisbeautiful", "subscribers": "20M+"},
        ]


# 全局实例
reddit_manager = RedditManager()


def fetch_reddit_hotspots(
    subreddits: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Dict]:
    """获取 Reddit 热门"""
    return reddit_manager.get_hotspots(subreddits, limit)
