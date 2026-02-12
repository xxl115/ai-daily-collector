"""Dev.to API scraper."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import json
from datetime import datetime, timedelta


def fetch_devto(tag: str = "AI", max_articles: int = 15) -> List[Dict[str, Any]]:
    """Fetch articles from Dev.to API.
    
    Dev.to has a public API that doesn't require authentication.
    
    Args:
        tag: Tag to filter by (default: "AI")
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    items: List[Dict[str, Any]] = []
    
    try:
        # Dev.to API endpoint for articles with tag
        url = f"https://dev.to/api/articles?tag={tag}&per_page={max_articles}"
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            articles = json.loads(response.read().decode('utf-8'))
        
        if not isinstance(articles, list):
            return []
        
        for article in articles[:max_articles]:
            if not isinstance(article, dict):
                continue
            
            title = article.get("title", "")
            if not title:
                continue
            
            # Get publication date
            pub_date = article.get("published_at", "")
            
            # Get author info
            user = article.get("user", {})
            author = user.get("name", "") or user.get("username", "")
            
            items.append({
                "id": f"devto-{article.get('id', '')}",
                "title": title,
                "url": article.get("url", ""),
                "description": article.get("description", "")[:500],
                "pub_date": pub_date,
                "source": "Dev.to",
                "author": author,
                "tags": article.get("tag_list", []),
                "reading_time": article.get("reading_time_minutes", 0),
                "reactions": article.get("public_reactions_count", 0),
            })
            
    except Exception:
        return []
    
    return items
