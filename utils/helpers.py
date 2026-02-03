# AI Daily Collector - 工具函数

import re
import hashlib
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs


def clean_filename(filename: str, max_length: int = 50) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        max_length: 最大长度
    
    Returns:
        清理后的文件名
    """
    # 移除非法字符
    illegal_chars = r'[<>:"/\\|?*\[\]（）()「」【】…—\'"\n\r]'
    clean = re.sub(illegal_chars, '', filename)
    
    # 替换空格
    clean = clean.replace(' ', '_')
    
    # 移除多余连字符
    clean = re.sub(r'_+', '_', clean)
    clean = re.sub(r'-+', '-', clean)
    
    # 截断
    if len(clean) > max_length:
        clean = clean[:max_length]
    
    return clean.strip('-_')


def slugify(text: str, max_length: int = 60) -> str:
    """生成 URL 友好的 slug"""
    # 转小写
    text = text.lower()
    
    # 移除特殊字符，保留字母数字和空格
    text = re.sub(r'[^\w\s-]', '', text)
    
    # 替换空格为连字符
    text = re.sub(r'[\s_]+', '-', text)
    
    # 移除首尾连字符
    text = text.strip('-')
    
    # 截断
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def extract_domain(url: str) -> str:
    """从 URL 提取域名"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.split(':')[0]  # 移除端口
    except Exception:
        return 'unknown'


def generate_file_hash(content: str) -> str:
    """生成文件内容的 MD5 hash"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_date_string(date_str: str) -> Optional[datetime]:
    """解析各种日期格式"""
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y/%m/%d',
        '%m/%d/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def extract_urls(text: str) -> List[str]:
    """从文本中提取所有 URL"""
    url_pattern = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        re.IGNORECASE
    )
    return url_pattern.findall(text)


def extract_urls_from_markdown(text: str) -> Dict[str, str]:
    """从 Markdown 提取链接 [text](url)"""
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    return {match.group(1): match.group(2) for match in pattern.finditer(text)}


def count_words(text: str) -> int:
    """计算中英文单词数"""
    # 中文按字符
    chinese_count = len(re.findall(r'[\u4e00-\u9fa5]', text))
    # 英文按空格分词
    english_count = len(text.split())
    return chinese_count + english_count


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    else:
        return f"{seconds/3600:.1f}h"


def retry(max_retries: int = 3, delay: float = 1, backoff: float = 2):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


class Timer:
    """计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        self.end_time = None
        return self
    
    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
        return self
    
    @property
    def duration(self) -> float:
        """获取耗时（秒）"""
        if self.start_time is None:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def formatted(self) -> str:
        """格式化耗时"""
        return format_duration(self.duration)


def read_json(file_path: Path, encoding: str = 'utf-8') -> Any:
    """读取 JSON 文件"""
    with open(file_path, 'r', encoding=encoding) as f:
        return json.load(f)


def write_json(data: Any, file_path: Path, encoding: str = 'utf-8', indent: int = 2):
    """写入 JSON 文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
