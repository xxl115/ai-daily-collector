"""重试工具模块 - 提供指数退避重试机制"""
import time
import functools
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[Exception, int], Any] | None = None,
):
    """指数退避重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数 (exception, attempt_number) -> None
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 达到最大重试次数 ({max_retries}), 放弃"
                        )
                        raise

                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)), max_delay
                    )

                    logger.warning(
                        f"{func.__name__} 第 {attempt}/{max_retries} 次尝试失败: {e}, "
                        f"{delay:.1f}s 后重试..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("重试失败但未捕获异常")

        return wrapper

    return decorator


def retry_with_fixed_interval(
    max_retries: int = 2,
    interval: float = 3.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[Exception, int], Any] | None = None,
):
    """固定间隔重试装饰器

    Args:
        max_retries: 最大重试次数
        interval: 固定间隔（秒）
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数 (exception, attempt_number) -> None
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 达到最大重试次数 ({max_retries}), 放弃"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt}/{max_retries} 次尝试失败: {e}, "
                        f"{interval}s 后重试..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(interval)

            if last_exception:
                raise last_exception
            raise RuntimeError("重试失败但未捕获异常")

        return wrapper

    return decorator
