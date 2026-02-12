"""NewsNow API scraper for Chinese hot topics."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import json
from datetime import datetime


def fetch_newsnow(platform_id: str, keyword: str = "", hours: int = 24, max_articles: int = 20) -> List[Dict[str, Any]]:
    """Fetch articles from NewsNow API.
    
    Args:
        platform_id: Platform identifier (toutiao, baidu, weibo, zhihu, bilibili, github, hackernews, producthunt)
        keyword: Filter keyword(s), supports regex patterns like "AI|大模型"
        hours: Time window in hours
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    base_url = "https://newsnow.busiyi.world/api"
    
    params = {
        "platform": platform_id,
        "hours": hours,
        "limit": max_articles
    }
    
    if keyword:
        params["keyword"] = keyword
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}?{query_string}"
    
    items: List[Dict[str, Any]] = []
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception:
        return []
    
    if not isinstance(data, list):
        return []
    
    for article in data[:max_articles]:
        if not isinstance(article, dict):
            continue
            
        title = article.get("title", "")
        url_field = article.get("url", "")
        summary = article.get("summary", "") or article.get("description", "")
        pub_time = article.get("pub_time", "") or article.get("publish_time", "")
        source = article.get("source", platform_id)
        
        if not title:
            continue
        
        items.append({
            "id": url_field or f"{platform_id}-{hash(title)}",
            "title": title,
            "url": url_field,
            "description": summary,
            "pub_date": pub_time,
            "source": f"NewsNow-{platform_id}",
            "platform": platform_id,
        })
    
    return items
