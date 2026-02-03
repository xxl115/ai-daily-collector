# AI Daily Collector - 日志配置
# 支持控制台和文件输出，支持按日期切割

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import colorlog

from config.settings import config


def setup_logger(
    name: str = "ai-collector",
    log_level: str = None,
    log_file: str = None,
    console: bool = True,
    file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置 logger
    
    Args:
        name: logger 名称
        log_level: 日志级别
        log_file: 日志文件路径
        console: 是否输出到控制台
        file: 是否输出到文件
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    
    Returns:
        配置好的 logger
    """
    logger = logging.getLogger(name)
    
    # 设置级别
    level = getattr(logging, (log_level or config.log.level).upper(), logging.INFO)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 控制台输出（带颜色）
    if console:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_format = (
            "%(log_color)s%(asctime)s%(reset)s - "
            "%(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(colorlog.ColoredFormatter(
            console_format,
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            }
        ))
        logger.addHandler(console_handler)
    
    # 文件输出（按大小切割）
    if file:
        log_dir = Path(config.log.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = log_file or config.log.file_path
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
        logger.addHandler(file_handler)
    
    return logger


def get_timed_rotating_logger(
    name: str = "ai-collector-timed",
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30
) -> logging.Logger:
    """
    获取按日期切割的 logger（适合日报使用）
    
    Args:
        name: logger 名称
        when: 切割周期 ('S', 'M', 'H', 'D', 'W0'-'W6')
        interval: 间隔
        backup_count: 保留天数
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    log_dir = Path(config.data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 按日期切割，每天凌晨生成新日志
    log_file = log_dir / "ai-collector.log"
    file_handler = TimedRotatingFileHandler(
        str(log_file),
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    format_str = "%(asctime)s - %(levelname)s - %(message)s"
    file_handler.setFormatter(logging.Formatter(format_str))
    
    logger.addHandler(file_handler)
    
    return logger


class LoggerMixin:
    """为类添加 logger"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger


# 便捷函数
def get_logger(name: str = "ai-collector") -> logging.Logger:
    """获取 logger"""
    return setup_logger(name)


# 默认 logger
logger = setup_logger()
