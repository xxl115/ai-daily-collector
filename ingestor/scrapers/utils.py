"""Utilities for scrapers."""
from __future__ import annotations

import time
import urllib.request
from typing import Callable, TypeVar, Any
from functools import wraps

T = TypeVar('T')


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


def fetch_url(url: str, timeout: int = 30, headers: dict | None = None) -> bytes:
    """Fetch URL content with proper headers and error handling.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Additional headers
        
    Returns:
        Response content as bytes
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
    }
    
    if headers:
        default_headers.update(headers)
    
    req = urllib.request.Request(url, headers=default_headers)
    
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()
