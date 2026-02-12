"""V2EX API scraper."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import json
import re


def fetch_v2ex(keyword: str = "", max_articles: int = 20) -> List[Dict[str, Any]]:
    """Fetch topics from V2EX API.
    
    V2EX has a public API (https://www.v2ex.com/p/7).
    
    Args:
        keyword: Filter keywords (e.g., "AI|大模型|GPT|Claude")
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    items: List[Dict[str, Any]] = []
    
    try:
        # V2EX API - get latest topics
        url = "https://www.v2ex.com/api/topics/latest.json"
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            topics = json.loads(response.read().decode('utf-8'))
        
        if not isinstance(topics, list):
            return []
        
        # Compile keyword pattern if provided
        keyword_pattern = None
        if keyword:
            try:
                keyword_pattern = re.compile(keyword, re.IGNORECASE)
            except re.error:
                keyword_pattern = None
        
        for topic in topics[:max_articles * 2]:
            if not isinstance(topic, dict):
                continue
            
            title = topic.get("title", "")
            if not title:
                continue
            
            # Filter by keyword if provided
            content = topic.get("content", "")
            text_to_check = f"{title} {content}"
            if keyword_pattern and not keyword_pattern.search(text_to_check):
                continue
            
            # Get node (category) info
            node = topic.get("node", {})
            node_title = node.get("title", "") if isinstance(node, dict) else ""
            
            items.append({
                "id": f"v2ex-{topic.get('id', '')}",
                "title": title,
                "url": topic.get("url", ""),
                "description": content[:500] if content else "",
                "pub_date": topic.get("created", ""),
                "source": "V2EX",
                "author": topic.get("member", {}).get("username", "") if isinstance(topic.get("member"), dict) else "",
                "node": node_title,
                "replies": topic.get("replies", 0),
            })
            
            if len(items) >= max_articles:
                break
            
    except Exception:
        return []
    
    return items
