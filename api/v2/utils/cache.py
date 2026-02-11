"""
缓存机制
提供内存缓存和磁盘缓存，减少文件 I/O 操作
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta


# ==================== 内存缓存 ====================

class MemoryCache:
    """简单的内存缓存"""

    def __init__(self, ttl_seconds: int = 300):  # 默认 5 分钟
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return data
            else:
                # 缓存过期，删除
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def cleanup(self) -> None:
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]

    def __len__(self) -> int:
        """返回缓存项数量"""
        return len(self._cache)


# ==================== 磁盘缓存 ====================

class DiskCache:
    """简单的磁盘缓存"""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):  # 默认 1 小时
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 将 key 转换为安全的文件名
        safe_key = "".join(c if c.isalnum() or c in "-_." else "_" for c in key).strip("_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            # 检查文件修改时间
            mtime = cache_path.stat().st_mtime
            if time.time() - mtime > self.ttl_seconds:
                cache_path.unlink()
                return None

            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception:
            return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 忽略写入错误

    def clear(self) -> None:
        """清空缓存"""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def cleanup(self) -> None:
        """清理过期缓存"""
        if not self.cache_dir.exists():
            return

        now = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if now - cache_file.stat().st_mtime > self.ttl_seconds:
                    cache_file.unlink()
            except Exception:
                pass

    def __len__(self) -> int:
        """返回缓存项数量"""
        if not self.cache_dir.exists():
            return 0
        return len(list(self.cache_dir.glob("*.json")))


# ==================== 缓存管理器 ====================

class CacheManager:
    """缓存管理器"""

    def __init__(self, memory_ttl: int = 300, disk_ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            memory_ttl: 内存缓存 TTL（秒）
            disk_ttl: 磁盘缓存 TTL（秒）
        """
        self.memory_cache = MemoryCache(ttl_seconds=memory_ttl)
        self.disk_cache = None  # 延迟初始化

    def _get_disk_cache(self, cache_dir: Path) -> DiskCache:
        """获取磁盘缓存实例"""
        if self.disk_cache is None:
            self.disk_cache = DiskCache(cache_dir / ".cache", ttl_seconds=86400)  # 24 小时
        return self.disk_cache

    def get_or_set(self, key: str, fetch_func, cache_dir: Optional[Path] = None) -> Any:
        """
        获取缓存，如果不存在则调用 fetch_func 获取

        Args:
            key: 缓存键
            fetch_func: 获取数据的函数
            cache_dir: 磁盘缓存目录

        Returns:
            缓存的数据或 fetch_func 的返回值
        """
        # 1. 先尝试从内存缓存获取
        data = self.memory_cache.get(key)
        if data is not None:
            return data

        # 2. 如果有磁盘缓存，尝试从磁盘获取
        if cache_dir is not None:
            disk_cache = self._get_disk_cache(cache_dir)
            data = disk_cache.get(key)
            if data is not None:
                # 存入内存缓存
                self.memory_cache.set(key, data)
                return data

        # 3. 调用 fetch_func 获取数据
        data = fetch_func()

        # 4. 存入缓存
        self.memory_cache.set(key, data)
        if cache_dir is not None:
            disk_cache = self._get_disk_cache(cache_dir)
            disk_cache.set(key, data)

        return data

    def invalidate(self, key: str) -> None:
        """使缓存失效"""
        if key in self.memory_cache._cache:
            del self.memory_cache._cache[key]

        if self.disk_cache is not None:
            self.disk_cache.clear()  # 简化：清除所有磁盘缓存

    def cleanup(self) -> None:
        """清理过期缓存"""
        self.memory_cache.cleanup()
        if self.disk_cache is not None:
            self.disk_cache.cleanup()


# ==================== 全局缓存实例 ====================

# 创建全局缓存实例
cache_manager = CacheManager(
    memory_ttl=300,  # 5 分钟内存缓存
    disk_ttl=86400    # 24 小时磁盘缓存
)
