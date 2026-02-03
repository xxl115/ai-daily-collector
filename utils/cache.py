# -*- coding: utf-8 -*-
"""
缓存模块

支持多种缓存后端:
- memory: 内存缓存（默认）
- redis: Redis 缓存
- disk: 磁盘缓存

特性:
- TTL 过期机制
- LRU 淘汰策略
- 序列化支持
- 统计信息
"""

import hashlib
import json
import os
import pickle
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CacheBackend(ABC):
    """缓存后端基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict:
        """获取统计信息"""
        pass


class MemoryCache(CacheBackend):
    """内存缓存"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        """
        初始化
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }
        self._cleanup()
    
    def _generate_key(self, key: str) -> str:
        """生成标准化的 key"""
        return key.lower().strip()
    
    def _is_expired(self, entry: Dict) -> bool:
        """检查是否过期"""
        if "expire_at" not in entry:
            return False
        return time.time() > entry["expire_at"]
    
    def _cleanup(self):
        """清理过期条目"""
        # 不自动清理，避免性能问题
        pass
    
    def _evict(self):
        """淘汰最旧的条目"""
        if len(self._cache) < self.max_size:
            return
        
        # LRU 淘汰：删除最早的条目
        oldest_key = None
        oldest_time = float("inf")
        
        for key, entry in self._cache.items():
            if "created_at" in entry and entry["created_at"] < oldest_time:
                oldest_time = entry["created_at"]
                oldest_key = key
        
        if oldest_key:
            del self._cache[oldest_key]
            self._stats["evictions"] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(key)
        
        if key not in self._cache:
            self._stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        if self._is_expired(entry):
            del self._cache[key]
            self._stats["misses"] += 1
            return None
        
        self._stats["hits"] += 1
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        # 序列化大对象
        if isinstance(value, (list, dict)) and len(str(value)) > 10000:
            try:
                value = pickle.dumps(value)
                is_pickled = True
            except Exception:
                is_pickled = False
        else:
            is_pickled = False
        
        entry = {
            "value": value,
            "created_at": time.time(),
            "expire_at": time.time() + ttl,
            "is_pickled": is_pickled,
        }
        
        # 淘汰机制
        while len(self._cache) >= self.max_size:
            self._evict()
        
        self._cache[key] = entry
        self._stats["sets"] += 1
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        key = self._generate_key(key)
        
        if key in self._cache:
            del self._cache[key]
            self._stats["deletes"] += 1
            return True
        return False
    
    def clear(self) -> bool:
        """清空缓存"""
        self._cache.clear()
        return True
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        key = self._generate_key(key)
        
        if key not in self._cache:
            return False
        
        if self._is_expired(self._cache[key]):
            del self._cache[key]
            return False
        
        return True
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "backend": "memory",
            "max_size": self.max_size,
            "current_size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "evictions": self._stats["evictions"],
        }


class DiskCache(CacheBackend):
    """磁盘缓存"""
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        max_size: int = 100,
        default_ttl: int = 86400,
    ):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        self._cleanup()
    
    def _generate_key(self, key: str) -> str:
        """生成安全的文件名"""
        # 使用 hash 保证文件名安全
        hash_key = hashlib.md5(key.encode()).hexdigest()[:32]
        return f"{hash_key}.cache"
    
    def _get_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / self._generate_key(key)
    
    def _is_expired(self, path: Path) -> bool:
        """检查是否过期"""
        if not path.exists():
            return True
        
        # 检查修改时间
        mtime = path.stat().st_mtime
        if time.time() - mtime > self.default_ttl:
            return True
        
        return False
    
    def _cleanup(self):
        """清理过期和过多的缓存"""
        if not self.cache_dir.exists():
            return
        
        # 清理过期文件
        for path in self.cache_dir.glob("*.cache"):
            if self._is_expired(path):
                try:
                    path.unlink()
                except Exception:
                    pass
    
    def _evict(self):
        """淘汰最旧的缓存"""
        files = sorted(
            self.cache_dir.glob("*.cache"),
            key=lambda p: p.stat().st_mtime,
        )
        
        if len(files) > self.max_size:
            for path in files[:len(files) - self.max_size]:
                try:
                    path.unlink()
                except Exception:
                    pass
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        path = self._get_path(key)
        
        if not path.exists() or self._is_expired(path):
            self._stats["misses"] += 1
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass
            return None
        
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            
            self._stats["hits"] += 1
            return data
            
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        path = self._get_path(key)
        ttl = ttl or self.default_ttl
        
        try:
            # 淘汰机制
            self._evict()
            
            data = {
                "value": value,
                "expire_at": time.time() + ttl,
            }
            
            with open(path, "wb") as f:
                pickle.dump(data, f)
            
            self._stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        path = self._get_path(key)
        
        if path.exists():
            try:
                path.unlink()
                self._stats["deletes"] += 1
                return True
            except Exception:
                pass
        return False
    
    def clear(self) -> bool:
        """清空缓存"""
        for path in self.cache_dir.glob("*.cache"):
            try:
                path.unlink()
            except Exception:
                pass
        return True
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        path = self._get_path(key)
        
        if not path.exists() or self._is_expired(path):
            return False
        return True
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        cache_count = len(list(self.cache_dir.glob("*.cache")))
        
        return {
            "backend": "disk",
            "cache_dir": str(self.cache_dir),
            "max_size": self.max_size,
            "current_size": cache_count,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
        }


class RedisCache(CacheBackend):
    """Redis 缓存（可选依赖）"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        key_prefix: str = "ai-daily:",
        default_ttl: int = 3600,
    ):
        """
        初始化
        
        Args:
            host: Redis 主机
            port: Redis 端口
            db: 数据库编号
            password: 密码
            key_prefix: 键前缀
            default_ttl: 默认过期时间
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._client = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
    
    def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password or None,
                    decode_responses=True,
                )
                # 测试连接
                self._client.ping()
                logger.info(f"Redis 连接成功: {self.host}:{self.port}")
            except ImportError:
                logger.warning("Redis 模块未安装，请运行: pip install redis")
                return None
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
                return None
        return self._client
    
    def _generate_key(self, key: str) -> str:
        """生成标准化的 key"""
        return f"{self.key_prefix}{key.lower().strip()}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        client = self._get_client()
        if client is None:
            return None
        
        try:
            key = self._generate_key(key)
            value = client.get(key)
            
            if value is None:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return json.loads(value)
            
        except Exception as e:
            logger.warning(f"Redis 获取失败: {e}")
            self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        client = self._get_client()
        if client is None:
            return False
        
        try:
            key = self._generate_key(key)
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False)
            
            client.setex(key, ttl, serialized)
            self._stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.warning(f"Redis 设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        client = self._get_client()
        if client is None:
            return False
        
        try:
            key = self._generate_key(key)
            result = client.delete(key)
            if result > 0:
                self._stats["deletes"] += 1
                return True
            return False
            
        except Exception as e:
            logger.warning(f"Redis 删除失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空缓存"""
        client = self._get_client()
        if client is None:
            return False
        
        try:
            # 删除所有带前缀的键
            keys = client.keys(f"{self.key_prefix}*")
            if keys:
                client.delete(*keys)
            return True
            
        except Exception as e:
            logger.warning(f"Redis 清空失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = self._get_client()
        if client is None:
            return False
        
        try:
            key = self._generate_key(key)
            return client.exists(key) > 0
        except Exception:
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "backend": "redis",
            "host": self.host,
            "port": self.port,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
        }


class Cache:
    """缓存管理器"""
    
    def __init__(
        self,
        backend: str = "memory",
        **kwargs,
    ):
        """
        初始化
        
        Args:
            backend: 缓存后端类型 ("memory", "disk", "redis")
            **kwargs: 后端特定参数
        """
        self._backends: Dict[str, CacheBackend] = {}
        self._default_backend = backend
        self._default_ttl = kwargs.get("default_ttl", 3600)
        
        # 初始化默认后端
        self._init_backend(backend, **kwargs)
    
    def _init_backend(self, name: str, **kwargs) -> CacheBackend:
        """初始化指定后端"""
        if name == "memory":
            return self._add_backend("default", MemoryCache(
                max_size=kwargs.get("max_size", 1000),
                default_ttl=self._default_ttl,
            ))
        elif name == "disk":
            return self._add_backend("default", DiskCache(
                cache_dir=kwargs.get("cache_dir", ".cache"),
                max_size=kwargs.get("max_size", 100),
                default_ttl=self._default_ttl,
            ))
        elif name == "redis":
            return self._add_backend("default", RedisCache(
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 6379),
                db=kwargs.get("db", 0),
                password=kwargs.get("password"),
                key_prefix=kwargs.get("key_prefix", "ai-daily:"),
                default_ttl=self._default_ttl,
            ))
        else:
            logger.warning(f"未知的缓存后端: {name}，使用内存缓存")
            return self._add_backend("default", MemoryCache(
                default_ttl=self._default_ttl,
            ))
    
    def _add_backend(self, name: str, backend: CacheBackend) -> CacheBackend:
        """添加缓存后端"""
        self._backends[name] = backend
        return backend
    
    def get_backend(self, name: str = "default") -> CacheBackend:
        """获取缓存后端"""
        return self._backends.get(name)
    
    def get(self, key: str, backend: str = "default") -> Optional[Any]:
        """获取缓存"""
        b = self.get_backend(backend)
        if b is None:
            return None
        return b.get(key)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        backend: str = "default",
    ) -> bool:
        """设置缓存"""
        b = self.get_backend(backend)
        if b is None:
            return False
        return b.set(key, value, ttl or self._default_ttl)
    
    def delete(self, key: str, backend: str = "default") -> bool:
        """删除缓存"""
        b = self.get_backend(backend)
        if b is None:
            return False
        return b.delete(key)
    
    def clear(self, backend: str = "default") -> bool:
        """清空缓存"""
        b = self.get_backend(backend)
        if b is None:
            return False
        return b.clear()
    
    def exists(self, key: str, backend: str = "default") -> bool:
        """检查键是否存在"""
        b = self.get_backend(backend)
        if b is None:
            return False
        return b.exists(key)
    
    def get_stats(self, backend: str = "default") -> Dict:
        """获取统计信息"""
        b = self.get_backend(backend)
        if b is None:
            return {"error": "后端不存在"}
        return b.get_stats()
    
    def memoize(self, ttl: int = 3600, key_prefix: str = ""):
        """
        装饰器：缓存函数结果
        
        Usage:
            @cache.memoize(ttl=600)
            def expensive_function(arg1, arg2):
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{key_prefix}{func.__name__}:{args}:{kwargs}"
                result = self.get(cache_key)
                
                if result is not None:
                    return result
                
                # 计算结果
                result = func(*args, **kwargs)
                
                # 缓存结果
                self.set(cache_key, result, ttl)
                return result
            
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper
        return decorator


# 全局缓存实例
cache = Cache()


def cached(ttl: int = 3600, key_builder=None):
    """
    缓存装饰器
    
    Usage:
        @cached(ttl=600)
        def my_function(arg1):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}:{func.__name__}:{args}:{kwargs}"
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, ttl)
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
