# -*- coding: utf-8 -*-
"""
错误处理模块

特性:
- 统一错误类型
- 错误降级策略
- 错误日志记录
- 自动重试机制
"""

import functools
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"       # 低: 日志记录
    MEDIUM = "medium" # 中: 警告 + 通知
    HIGH = "high"     # 高: 错误 + 通知
    CRITICAL = "critical"  # 严重: 致命 + 停止服务


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"           # 网络错误
    PARSE = "parse"               # 解析错误
    AUTH = "auth"                 # 认证错误
    RATE_LIMIT = "rate_limit"     # 限流错误
    DATA = "data"                 # 数据错误
    SYSTEM = "system"             # 系统错误
    CONFIG = "config"             # 配置错误
    UNKNOWN = "unknown"           # 未知错误


@dataclass
class ErrorContext:
    """错误上下文"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    function: str = ""
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    retry_count: int = 0
    affected_data: Dict = field(default_factory=dict)


class BaseError(Exception):
    """基础错误类"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: ErrorContext = None,
        original_error: Exception = None,
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.original_error = original_error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "context": {
                "function": self.context.function,
                "retry_count": self.context.retry_count,
                "affected_data": self.context.affected_data,
            },
            "original_error": str(self.original_error) if self.original_error else None,
        }
    
    def log(self, logger=None):
        """记录日志"""
        if logger is None:
            logger = get_logger(__name__)
        
        log_func = {
            ErrorSeverity.LOW: logger.debug,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
        }.get(self.severity, logger.warning)
        
        log_func(f"[{self.category.value}] {self.message}")


class NetworkError(BaseError):
    """网络错误"""
    
    def __init__(
        self,
        message: str = "网络请求失败",
        status_code: int = None,
        url: str = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            **kwargs,
        )
        self.status_code = status_code
        self.url = url
    
    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["status_code"] = self.status_code
        d["url"] = self.url
        return d


class ParseError(BaseError):
    """解析错误"""
    
    def __init__(
        self,
        message: str = "数据解析失败",
        data_type: str = None,
        position: int = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PARSE,
            **kwargs,
        )
        self.data_type = data_type
        self.position = position
    
    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["data_type"] = self.data_type
        d["position"] = self.position
        return d


class AuthenticationError(BaseError):
    """认证错误"""
    
    def __init__(
        self,
        message: str = "认证失败",
        auth_type: str = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTH,
            **kwargs,
        )
        self.auth_type = auth_type


class RateLimitError(BaseError):
    """限流错误"""
    
    def __init__(
        self,
        message: str = "请求过于频繁",
        retry_after: int = 60,
        limit: int = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.RATE_LIMIT,
            **kwargs,
        )
        self.retry_after = retry_after
        self.limit = limit
    
    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["retry_after"] = self.retry_after
        d["limit"] = self.limit
        return d


class DataError(BaseError):
    """数据错误"""
    
    def __init__(
        self,
        message: str = "数据异常",
        data_source: str = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.DATA,
            **kwargs,
        )
        self.data_source = data_source


class ConfigurationError(BaseError):
    """配置错误"""
    
    def __init__(
        self,
        message: str = "配置错误",
        config_key: str = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.CONFIG,
            **kwargs,
        )
        self.config_key = config_key


class FallbackManager:
    """降级管理器"""
    
    def __init__(self):
        self._fallbacks: Dict[str, Callable] = {}
        self._error_counts: Dict[str, int] = {}
        self._failure_threshold = 3  # 连续失败次数阈值
        self._recovery_threshold = 2  # 恢复需要的成功次数
    
    def register(self, name: str, fallback: Callable, primary: Callable = None):
        """
        注册降级策略
        
        Args:
            name: 策略名称
            fallback: 降级处理函数
            primary: 主函数（可选，用于自动装饰）
        """
        self._fallbacks[name] = {
            "fallback": fallback,
            "primary": primary,
            "consecutive_failures": 0,
            "consecutive_successes": 0,
            "is_fallback_active": False,
        }
        
        # 如果提供了主函数，自动装饰
        if primary:
            self._wrap_with_fallback(name, primary)
    
    def _wrap_with_fallback(self, name: str, func: Callable):
        """包装函数以支持降级"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            fallback_info = self._fallbacks[name]
            
            # 如果降级已激活，直接调用降级函数
            if fallback_info["is_fallback_active"]:
                return fallback_info["fallback"](*args, **kwargs)
            
            # 尝试主函数
            try:
                result = func(*args, **kwargs)
                self._on_success(name)
                return result
            except Exception as e:
                self._on_failure(name, e)
                
                # 如果降级已激活，调用降级函数
                if fallback_info["is_fallback_active"]:
                    return fallback_info["fallback"](*args, **kwargs)
                
                # 重新抛出
                raise
        
        return wrapper
    
    def _on_success(self, name: str):
        """处理成功"""
        info = self._fallbacks.get(name)
        if info:
            info["consecutive_successes"] += 1
            info["consecutive_failures"] = 0
            
            # 连续成功次数达到阈值，尝试恢复
            if (info["is_fallback_active"] and 
                info["consecutive_successes"] >= self._recovery_threshold):
                info["is_fallback_active"] = False
                logger.info(f"降级策略 '{name}' 已恢复")
    
    def _on_failure(self, name: str, error: Exception):
        """处理失败"""
        info = self._fallbacks.get(name)
        if info:
            info["consecutive_failures"] += 1
            info["consecutive_successes"] = 0
            
            # 连续失败次数达到阈值，激活降级
            if (not info["is_fallback_active"] and 
                info["consecutive_failures"] >= self._failure_threshold):
                info["is_fallback_active"] = True
                logger.warning(f"降级策略 '{name}' 已激活 (连续 {self._failure_threshold} 次失败)")
    
    def activate_fallback(self, name: str):
        """手动激活降级"""
        if name in self._fallbacks:
            self._fallbacks[name]["is_fallback_active"] = True
            logger.info(f"降级策略 '{name}' 已手动激活")
    
    def deactivate_fallback(self, name: str):
        """手动停用降级"""
        if name in self._fallbacks:
            self._fallbacks[name]["is_fallback_active"] = False
            self._fallbacks[name]["consecutive_failures"] = 0
            logger.info(f"降级策略 '{name}' 已手动停用")
    
    def get_status(self, name: str) -> Dict:
        """获取策略状态"""
        info = self._fallbacks.get(name)
        if not info:
            return {"error": "策略不存在"}
        
        return {
            "name": name,
            "is_active": info["is_fallback_active"],
            "consecutive_failures": info["consecutive_failures"],
            "consecutive_successes": info["consecutive_successes"],
        }
    
    def get_all_status(self) -> Dict:
        """获取所有策略状态"""
        return {
            name: self.get_status(name)
            for name in self._fallbacks
        }


def retry(
    max_retries: int = 3,
    delay: Union[int, float, tuple] = 1,
    backoff: float = 2,
    max_delay: int = 60,
    exceptions: tuple = (Exception,),
    on_retry: Callable = None,
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒），可以是单个值或 (min, max) 元组
        backoff: 延迟递增倍数
        max_delay: 最大延迟（秒）
        exceptions: 要重试的异常类型
        on_retry: 重试回调函数
    
    Usage:
        @retry(max_retries=3, delay=1, backoff=2)
        def fetch_data():
            ...
    
    Returns:
        重试后的结果
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # 最后一次不重试
                    if attempt >= max_retries:
                        logger.error(
                            f"函数 {func.__name__} 重试 {max_retries} 次后失败: {e}"
                        )
                        raise
                    
                    # 计算延迟
                    if isinstance(delay, tuple):
                        actual_delay = random.uniform(*delay)
                    else:
                        actual_delay = delay
                    
                    # 指数退避
                    actual_delay = min(actual_delay * (backoff ** attempt), max_delay)
                    
                    # 添加随机抖动
                    jitter = actual_delay * 0.1 * random.random()
                    wait_time = actual_delay + jitter
                    
                    # 调用回调
                    if on_retry:
                        on_retry(
                            func=func,
                            attempt=attempt,
                            exception=e,
                            wait_time=wait_time,
                        )
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次失败: {e}, "
                        f"{wait_time:.2f}秒后重试..."
                    )
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator


# 内置降级策略
def fallback_return_default(default_value=None):
    """返回默认值的降级"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return default_value
        return wrapper
    return decorator


def fallback_return_empty(func):
    """返回空列表/字典的降级"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            # 根据返回类型推断空值
            if hasattr(func, '__annotations__'):
                return_type = func.__annotations__.get('return')
                if return_type == list:
                    return []
                elif return_type == dict:
                    return {}
            return []
    return wrapper


def fallback_cache_last_success(func):
    """缓存上次成功结果的降级"""
    last_success = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            last_success['result'] = result
            last_success['time'] = datetime.now()
            return result
        except Exception:
            if 'result' in last_success:
                logger.warning(f"使用缓存的上次成功结果 (来自 {last_success['time']})")
                return last_success['result']
            raise
    
    return wrapper


# 全局降级管理器
fallback_manager = FallbackManager()


def with_fallback(
    fallback_name: str,
    fallback_func: Callable = None,
):
    """
    快速降级装饰器
    
    Usage:
        @with_fallback("cache_fallback")
        def fetch_data():
            ...
    """
    def decorator(func):
        # 注册降级策略
        fallback_manager.register(
            name=fallback_name,
            primary=func,
            fallback=fallback_func or fallback_return_empty(func),
        )
        
        return fallback_manager._wrap_with_fallback(fallback_name, func)
    
    return decorator
