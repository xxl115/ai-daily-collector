# -*- coding: utf-8 -*-
"""
限流模块

支持多种限流策略:
- fixed_window: 固定窗口
- sliding_window: 滑动窗口
- token_bucket: 令牌桶
- leaky_bucket: 漏桶

特性:
- 多维度限流（IP、用户、API）
- 动态配置
- 限流惩罚
"""

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Dict, List, Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests: int = 60          # 允许的请求数
    window: int = 60            # 时间窗口（秒）
    burst: int = 10             # 突发请求数（令牌桶）
    penalty: int = 300          # 惩罚时间（秒）
    strategies: List[str] = field(default_factory=list)  # 适用策略


class RateLimitBackend(ABC):
    """限流后端基类"""
    
    @abstractmethod
    def is_allowed(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """
        检查是否允许请求
        
        Returns:
            (是否允许, 剩余请求数, 等待时间/惩罚时间)
        """
        pass
    
    @abstractmethod
    def reset(self, identifier: str):
        """重置限流计数"""
        pass
    
    @abstractmethod
    def get_stats(self, identifier: str) -> Dict:
        """获取统计信息"""
        pass


class MemoryRateLimitBackend(RateLimitBackend):
    """内存限流后端"""
    
    def __init__(self):
        self._counters: Dict[str, Dict] = {}
        self._last_reset: Dict[str, float] = {}
        self._tokens: Dict[str, float] = {}
        self._stats: Dict[str, Dict] = {}
    
    def _get_key(self, identifier: str, config: RateLimitConfig) -> str:
        """生成缓存键"""
        return f"{identifier}:{config.requests}:{config.window}"
    
    def _get_strategy(self, identifier: str, config: RateLimitConfig) -> str:
        """获取限流策略"""
        if config.strategies:
            return config.strategies[0]
        return "sliding_window"
    
    def is_allowed(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """检查是否允许请求"""
        key = self._get_key(identifier, config)
        strategy = self._get_strategy(identifier, config)
        now = time.time()
        
        # 初始化
        if key not in self._counters:
            self._counters[key] = {
                "count": 0,
                "window_start": now,
                "penalty_until": 0,
            }
            self._tokens[key] = float(config.burst)
            self._stats[key] = {
                "total_requests": 0,
                "blocked_requests": 0,
                "last_request": now,
            }
        
        counter = self._counters[key]
        
        # 检查惩罚期
        if now < counter["penalty_until"]:
            self._stats[key]["blocked_requests"] += 1
            return False, 0, int(counter["penalty_until"] - now)
        
        # 策略：滑动窗口
        if strategy == "sliding_window":
            return self._sliding_window(key, now, config)
        
        # 策略：令牌桶
        elif strategy == "token_bucket":
            return self._token_bucket(key, now, config)
        
        # 策略：漏桶
        elif strategy == "leaky_bucket":
            return self._leaky_bucket(key, now, config)
        
        # 策略：固定窗口（默认）
        return self._fixed_window(key, now, config)
    
    def _fixed_window(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """固定窗口限流"""
        counter = self._counters[key]
        
        # 检查窗口是否过期
        if now - counter["window_start"] >= config.window:
            counter["count"] = 0
            counter["window_start"] = now
        
        # 检查是否超过限制
        if counter["count"] >= config.requests:
            # 触发惩罚
            counter["penalty_until"] = now + config.penalty
            self._stats[key]["blocked_requests"] += 1
            return False, 0, config.penalty
        
        # 允许请求
        counter["count"] += 1
        self._stats[key]["total_requests"] += 1
        self._stats[key]["last_request"] = now
        
        remaining = config.requests - counter["count"]
        return True, remaining, 0
    
    def _sliding_window(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """滑动窗口限流"""
        counter = self._counters[key]
        window_start = counter["window_start"]
        
        # 计算当前窗口的请求数
        elapsed = now - window_start
        if elapsed >= config.window:
            # 新窗口
            counter["count"] = 1
            counter["window_start"] = now
            self._stats[key]["total_requests"] += 1
            return True, config.requests - 1, 0
        
        # 检查是否超过限制
        if counter["count"] >= config.requests:
            counter["penalty_until"] = now + config.penalty
            self._stats[key]["blocked_requests"] += 1
            return False, 0, config.penalty
        
        # 允许请求
        counter["count"] += 1
        self._stats[key]["total_requests"] += 1
        self._stats[key]["last_request"] = now
        
        remaining = config.requests - counter["count"]
        wait_time = max(0, config.window - elapsed)
        return True, remaining, 0
    
    def _token_bucket(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """令牌桶限流"""
        counter = self._counters[key]
        last_time = self._stats[key]["last_request"]
        
        # 计算新增令牌
        elapsed = now - last_time
        tokens_to_add = elapsed * (config.requests / config.window)
        self._tokens[key] = min(
            self._tokens[key] + tokens_to_add,
            float(config.burst)
        )
        
        # 检查令牌
        if self._tokens[key] < 1:
            counter["penalty_until"] = now + config.penalty
            self._stats[key]["blocked_requests"] += 1
            wait_time = int((1 - self._tokens[key]) * config.window / config.requests)
            return False, 0, max(wait_time, config.penalty)
        
        # 消耗令牌
        self._tokens[key] -= 1
        counter["count"] += 1
        self._stats[key]["total_requests"] += 1
        self._stats[key]["last_request"] = now
        
        remaining = int(self._tokens[key])
        return True, remaining, 0
    
    def _leaky_bucket(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """漏桶限流"""
        counter = self._counters[key]
        last_time = self._stats[key]["last_request"]
        
        # 计算处理时间
        elapsed = now - last_time
        processed = elapsed * (config.requests / config.window)
        counter["count"] = max(0, counter["count"] - processed)
        
        # 检查桶是否满
        if counter["count"] >= config.requests:
            counter["penalty_until"] = now + config.penalty
            self._stats[key]["blocked_requests"] += 1
            return False, 0, config.penalty
        
        # 添加请求
        counter["count"] += 1
        self._stats[key]["total_requests"] += 1
        self._stats[key]["last_request"] = now
        
        remaining = config.requests - int(counter["count"])
        return True, remaining, 0
    
    def reset(self, identifier: str):
        """重置限流计数"""
        for key in list(self._counters.keys()):
            if key.startswith(identifier):
                del self._counters[key]
                if key in self._tokens:
                    del self._tokens[key]
                if key in self._stats:
                    del self._stats[key]
    
    def get_stats(self, identifier: str) -> Dict:
        """获取统计信息"""
        stats = {
            "identifier": identifier,
            "limits": [],
        }
        
        for key, data in self._stats.items():
            if key.startswith(identifier):
                stats["limits"].append({
                    "key": key,
                    "total_requests": data["total_requests"],
                    "blocked_requests": data["blocked_requests"],
                    "last_request": data["last_request"],
                })
        
        return stats


class RateLimiter:
    """限流管理器"""
    
    # 默认限流配置
    DEFAULT_CONFIGS: Dict[str, RateLimitConfig] = {
        "default": RateLimitConfig(
            requests=60,
            window=60,
            burst=10,
            penalty=300,
            strategies=["sliding_window"],
        ),
        "api": RateLimitConfig(
            requests=100,
            window=60,
            burst=20,
            penalty=300,
            strategies=["token_bucket"],
        ),
        "crawler": RateLimitConfig(
            requests=30,
            window=60,
            burst=5,
            penalty=600,
            strategies=["leaky_bucket"],
        ),
        "webhook": RateLimitConfig(
            requests=10,
            window=60,
            burst=2,
            penalty=300,
            strategies=["fixed_window"],
        ),
    }
    
    def __init__(self):
        self._backend = MemoryRateLimitBackend()
        self._configs: Dict[str, RateLimitConfig] = {}
        self._identifiers: Dict[str, str] = {}
    
    def add_config(self, name: str, config: RateLimitConfig):
        """添加限流配置"""
        self._configs[name] = config
    
    def get_config(self, name: str) -> RateLimitConfig:
        """获取限流配置"""
        return self._configs.get(name, self.DEFAULT_CONFIGS.get(
            name, self.DEFAULT_CONFIGS["default"]
        ))
    
    def check(
        self,
        identifier: str,
        config_name: str = "default",
    ) -> Tuple[bool, int, int]:
        """
        检查是否允许请求
        
        Args:
            identifier: 标识符（IP、用户ID等）
            config_name: 配置名称
        
        Returns:
            (是否允许, 剩余请求数, 等待时间)
        """
        config = self.get_config(config_name)
        return self._backend.is_allowed(identifier, config)
    
    def limit(
        self,
        identifier_builder: Callable = None,
        config_name: str = "default",
    ):
        """
        限流装饰器
        
        Usage:
            @limiter.limit()
            def my_api():
                ...
            
            @limiter.limit(identifier_builder=lambda: request.ip)
            def protected_api():
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取标识符
                if identifier_builder:
                    identifier = identifier_builder(*args, **kwargs)
                else:
                    # 默认使用函数名 + 参数
                    key = f"{func.__module__}:{func.__name__}:{args}:{kwargs}"
                    identifier = hashlib.md5(key.encode()).hexdigest()[:16]
                
                # 检查限流
                allowed, remaining, wait = self.check(identifier, config_name)
                
                if not allowed:
                    # 添加限流响应头
                    if hasattr(args[0], 'headers') if args else False:
                        pass  # 已经在 headers 中处理
                    
                    raise RateLimitExceeded(
                        "请求过于频繁，请稍后再试",
                        wait_time=wait,
                        retry_after=wait,
                    )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def reset(self, identifier: str):
        """重置限流"""
        self._backend.reset(identifier)
    
    def get_stats(self, identifier: str = None) -> Dict:
        """获取统计"""
        if identifier:
            return self._backend.get_stats(identifier)
        return {
            "backend": "memory",
            "configs": list(self._configs.keys()),
            "default_configs": list(self.DEFAULT_CONFIGS.keys()),
        }
    
    def get_headers(
        self,
        identifier: str,
        config_name: str = "default",
    ) -> Dict[str, str]:
        """获取限流响应头"""
        config = self.get_config(config_name)
        allowed, remaining, wait = self._backend.is_allowed(identifier, config)
        
        return {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(time.time() + config.window)),
            "Retry-After": str(wait) if not allowed else "",
        }


class RateLimitExceeded(Exception):
    """超过限流异常"""
    
    def __init__(self, message: str, wait_time: int = 0, retry_after: int = 0):
        super().__init__(message)
        self.wait_time = wait_time
        self.retry_after = retry_after


# 全局限流器实例
limiter = RateLimiter()


def rate_limit(
    requests: int = 60,
    window: int = 60,
    burst: int = 10,
    penalty: int = 300,
    strategy: str = "sliding_window",
):
    """
    快速限流装饰器
    
    Usage:
        @rate_limit(requests=30, window=60)
        def my_api():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成标识符
            key = f"{func.__module__}:{func.__name__}"
            identifier = hashlib.md5(key.encode()).hexdigest()[:16]
            
            # 创建临时配置
            config = RateLimitConfig(
                requests=requests,
                window=window,
                burst=burst,
                penalty=penalty,
                strategies=[strategy],
            )
            
            # 检查限流
            allowed, remaining, wait = limiter._backend.is_allowed(identifier, config)
            
            if not allowed:
                raise RateLimitExceeded(
                    f"请求过于频繁，请等待 {wait} 秒",
                    wait_time=wait,
                    retry_after=wait,
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# 针对不同场景的便捷装饰器
def rate_limit_api(func):
    """API 限流 (100 请求/分钟)"""
    return limiter.limit(config_name="api")(func)


def rate_limit_crawler(func):
    """爬虫限流 (30 请求/分钟)"""
    return limiter.limit(config_name="crawler")(func)


def rate_limit_webhook(func):
    """Webhook 限流 (10 请求/分钟)"""
    return limiter.limit(config_name="webhook")(func)
