# AI Daily Collector - 自定义异常

from datetime import datetime


class AICollectorError(Exception):
    """基础异常类"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class CrawlerError(AICollectorError):
    """采集相关异常"""
    pass


class RSSFetchError(CrawlerError):
    """RSS 获取失败"""
    pass


class SummarizerError(AICollectorError):
    """总结生成相关异常"""
    pass


class ReportError(AICollectorError):
    """日报生成相关异常"""
    pass


class NotionSyncError(AICollectorError):
    """Notion 同步相关异常"""
    pass


class ConfigurationError(AICollectorError):
    """配置相关异常"""
    pass


# 异常处理装饰器
def handle_exceptions(default_return=None, log_errors: bool = True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AICollectorError:
                raise
            except Exception as e:
                if log_errors:
                    print(f"Error in {func.__name__}: {e}")
                if default_return is not None:
                    return default_return
                raise AICollectorError(f"Unexpected error: {e}") from e
        return wrapper
    return decorator


# 错误代码
ERROR_CODES = {
    1001: "RSS 源连接失败",
    1002: "RSS 解析错误",
    2001: "AI API 密钥未配置",
    2002: "AI API 调用失败",
    3001: "分类配置错误",
    4001: "Notion Token 未配置",
}


def get_error_message(code: int) -> str:
    return ERROR_CODES.get(code, f"未知错误 (代码: {code})")
