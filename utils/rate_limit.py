"""限流工具模块 - 提供速率限制和并发控制"""
import time
import threading
import logging
from collections import deque
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """滑动窗口速率限制器"""

    def __init__(self, max_calls: int, period: float = 60.0):
        """初始化速率限制器

        Args:
            max_calls: 时间周期内允许的最大调用次数
            period: 时间周期（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = threading.Lock()

    def acquire(self) -> bool:
        """尝试获取令牌

        Returns:
            True 表示允许执行，False 表示需要等待
        """
        with self.lock:
            now = time.time()

            # 清理过期的调用记录
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True

            return False

    def wait_and_acquire(self) -> float:
        """等待并获取令牌，返回等待时间

        Returns:
            实际等待时间（秒）
        """
        start_wait = time.time()

        while True:
            if self.acquire():
                return time.time() - start_wait

            # 计算需要等待的时间
            with self.lock:
                if self.calls:
                    oldest = self.calls[0]
                    wait_time = self.period - (time.time() - oldest)
                else:
                    wait_time = 0.1

            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))


class SemaphoreLimiter:
    """信号量并发限制器"""

    def __init__(self, max_concurrent: int):
        """初始化并发限制器

        Args:
            max_concurrent: 最大并发数
        """
        self.semaphore = threading.Semaphore(max_concurrent)

    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        """获取执行许可

        Args:
            blocking: 是否阻塞等待
            timeout: 超时时间（秒）

        Returns:
            True 表示获取成功
        """
        return self.semaphore.acquire(blocking, timeout)

    def release(self) -> None:
        """释放执行许可"""
        self.semaphore.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def rate_limited(max_calls: int, period: float = 60.0):
    """速率限制装饰器

    Args:
        max_calls: 时间周期内允许的最大调用次数
        period: 时间周期（秒）

    Example:
        @rate_limited(max_calls=60, period=60.0)
        def make_api_request():
            pass
    """

    limiter = RateLimiter(max_calls, period)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            limiter.wait_and_acquire()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def concurrent_limited(max_concurrent: int):
    """并发限制装饰器

    Args:
        max_concurrent: 最大并发数

    Example:
        @concurrent_limited(max_concurrent=5)
        def process_item(item):
            pass
    """

    limiter = SemaphoreLimiter(max_concurrent)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            limiter.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                limiter.release()

        return wrapper

    return decorator
