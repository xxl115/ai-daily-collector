# -*- coding: utf-8 -*-
"""
统一抓取器接口

提供统一的抓取器接口，便于扩展和管理

Features:
- 统一的接口定义
- 自动注册和发现
- 配置化管理
- 健康检查
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from ..utils.logger import get_logger

logger = get_logger(__name__)


class FetcherStatus(Enum):
    """抓取器状态"""
    IDLE = "idle"         # 空闲
    RUNNING = "running"   # 运行中
    ERROR = "error"       # 错误
    DISABLED = "disabled" # 禁用


class FetcherType(Enum):
    """抓取器类型"""
    RSS = "rss"
    API = "api"
    HTML = "html"
    GRAPHQL = "graphql"


@dataclass
class FetcherConfig:
    """抓取器配置"""
    name: str
    type: FetcherType
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    rate_limit: int = 0  # 请求间隔（秒），0 表示无限制
    cache_ttl: int = 3600  # 缓存时间（秒）
    priority: int = 0  # 优先级，数字越小优先级越高
    metadata: Dict = field(default_factory=dict)


@dataclass
class FetchResult:
    """抓取结果"""
    success: bool
    data: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    cached: bool = False
    fetch_time: float = 0
    item_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseFetcher(ABC):
    """抓取器基类"""
    
    # 子类应该设置这些类属性
    fetcher_type: FetcherType = FetcherType.API
    default_config: FetcherConfig = None
    
    def __init__(self, config: FetcherConfig = None):
        """
        初始化
        
        Args:
            config: 抓取器配置
        """
        self.config = config or self.default_config
        if self.config is None:
            self.config = FetcherConfig(
                name=self.__class__.__name__,
                type=self.fetcher_type,
            )
        
        self.status = FetcherStatus.IDLE
        self._last_fetch: Optional[FetchResult] = None
        self._fetch_count = 0
        self._error_count = 0
        self._total_fetch_time = 0
    
    @property
    def name(self) -> str:
        """获取名称"""
        return self.config.name
    
    @abstractmethod
    async def fetch(self, **kwargs) -> FetchResult:
        """
        执行抓取
        
        Returns:
            FetchResult: 抓取结果
        """
        pass
    
    @abstractmethod
    def get_sources(self) -> List[str]:
        """获取数据源列表"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def _normalize_articles(
        self,
        items: List[Dict],
        source: str = None,
        rank_start: int = 1,
    ) -> List[Dict]:
        """
        标准化文章格式
        
        Args:
            items: 原始数据列表
            source: 来源标识
            rank_start: 起始排名
        
        Returns:
            标准化文章列表
        """
        articles = []
        source = source or self.config.name
        
        for rank, item in enumerate(items, rank_start):
            article = {
                "title": item.get("title", ""),
                "url": item.get("url", "") or item.get("link", ""),
                "summary": item.get("summary", "") or item.get("description", ""),
                "source": source,
                "source_id": self.config.name,
                "rank": rank,
                "timestamp": datetime.now().isoformat(),
                "hot_score": item.get("hot_score", 0) or item.get("score", 0),
                "published_at": item.get("published_at") or item.get("pubDate"),
                "author": item.get("author", ""),
                "tags": item.get("tags", []) or item.get("categories", []),
            }
            articles.append(article)
        
        return articles
    
    def _log_result(self, result: FetchResult, duration: float):
        """记录抓取结果"""
        self._last_fetch = result
        self._fetch_count += 1
        self._total_fetch_time += duration
        
        if result.success:
            logger.debug(
                f"[{self.name}] 抓取成功: {result.item_count} 条 "
                f"(耗时 {duration:.2f}s, 平均 {self._total_fetch_time / self._fetch_count:.2f}s)"
            )
        else:
            self._error_count += 1
            logger.warning(
                f"[{self.name}] 抓取失败: {result.error}"
            )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        avg_time = self._total_fetch_time / self._fetch_count if self._fetch_count > 0 else 0
        
        return {
            "name": self.name,
            "type": self.fetcher_type.value,
            "status": self.status.value,
            "fetch_count": self._fetch_count,
            "error_count": self._error_count,
            "success_rate": (
                f"{((self._fetch_count - self._error_count) / self._fetch_count * 100):.1f}%"
                if self._fetch_count > 0 else "N/A"
            ),
            "avg_fetch_time": f"{avg_time:.2f}s",
            "last_fetch": self._last_fetch.timestamp if self._last_fetch else None,
            "config": {
                "enabled": self.config.enabled,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "rate_limit": self.config.rate_limit,
                "cache_ttl": self.config.cache_ttl,
                "priority": self.config.priority,
            },
        }


class FetcherRegistry:
    """抓取器注册表"""
    
    def __init__(self):
        self._fetchers: Dict[str, Type[BaseFetcher]] = {}
        self._instances: Dict[str, BaseFetcher] = {}
        self._configs: Dict[str, FetcherConfig] = {}
    
    def register(self, fetcher_class: Type[BaseFetcher], config: FetcherConfig = None):
        """
        注册抓取器
        
        Args:
            fetcher_class: 抓取器类
            config: 默认配置
        """
        name = config.name if config else fetcher_class.__name__
        self._fetchers[name] = fetcher_class
        self._configs[name] = config or fetcher_class.default_config
        logger.info(f"抓取器已注册: {name}")
    
    def create(self, name: str, config: FetcherConfig = None) -> BaseFetcher:
        """
        创建抓取器实例
        
        Args:
            name: 抓取器名称
            config: 覆盖配置
        
        Returns:
            抓取器实例
        """
        if name not in self._fetchers:
            raise ValueError(f"未注册的抓取器: {name}")
        
        # 合并配置
        fetcher_config = config or self._configs.get(name)
        
        if fetcher_config and config:
            # 合并配置
            fetcher_config = FetcherConfig(
                name=config.name or fetcher_config.name,
                type=config.type or fetcher_config.type,
                enabled=config.enabled if config.enabled is not None else fetcher_config.enabled,
                timeout=config.timeout or fetcher_config.timeout,
                max_retries=config.max_retries or fetcher_config.max_retries,
                retry_delay=config.retry_delay or fetcher_config.retry_delay,
                rate_limit=config.rate_limit or fetcher_config.rate_limit,
                cache_ttl=config.cache_ttl or fetcher_config.cache_ttl,
                priority=config.priority or fetcher_config.priority,
                metadata={**fetcher_config.metadata, **config.metadata},
            )
        
        instance = self._fetchers[name](fetcher_config)
        self._instances[name] = instance
        return instance
    
    def get(self, name: str) -> Optional[BaseFetcher]:
        """获取已创建的实例"""
        return self._instances.get(name)
    
    def get_all_names(self) -> List[str]:
        """获取所有抓取器名称"""
        return list(self._fetchers.keys())
    
    def get_all_configs(self) -> Dict[str, FetcherConfig]:
        """获取所有配置"""
        return self._configs.copy()
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有统计"""
        return {
            name: fetcher.get_stats()
            for name, fetcher in self._instances.items()
        }
    
    def list_fetchers(self) -> List[Dict]:
        """列出所有抓取器"""
        return [
            {
                "name": name,
                "class": fetcher_class.__name__,
                "config": {
                    "type": self._configs[name].type.value if self._configs[name] else None,
                    "enabled": self._configs[name].enabled if self._configs[name] else None,
                    "priority": self._configs[name].priority if self._configs[name] else None,
                },
                "instance": name in self._instances,
            }
            for name, fetcher_class in self._fetchers.items()
        ]


# 全局注册表
registry = FetcherRegistry()


def fetcher(
    name: str = None,
    config: FetcherConfig = None,
):
    """
    抓取器装饰器/注册函数
    
    Usage:
        # 作为装饰器
        @fetcher(name="my_fetcher")
        class MyFetcher(BaseFetcher):
            ...
        
        # 直接注册
        fetcher(MyFetcher, config)
    """
    def decorator(fetcher_class):
        nonlocal config
        if name:
            config = FetcherConfig(
                name=name,
                type=getattr(fetcher_class, 'fetcher_type', FetcherType.API),
                **(config.metadata if config else {}),
            )
        registry.register(fetcher_class, config)
        return fetcher_class
    
    # 如果传入的是类而不是装饰器
    if isinstance(name, type) and issubclass(name, BaseFetcher):
        fetcher_class = name
        registry.register(fetcher_class, config)
        return fetcher_class
    
    return decorator
