"""Reddit API scraper."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import json
import re


def fetch_reddit(subreddit: str, keyword: str = "", max_articles: int = 15) -> List[Dict[str, Any]]:
    """Fetch posts from Reddit API.
    
    Uses Reddit's JSON API (public, no auth required for reading).
    Note: For production use with high volume, you should use OAuth2.
    
    Args:
        subreddit: Subreddit name (e.g., "MachineLearning", "artificial")
        keyword: Filter keywords
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    items: List[Dict[str, Any]] = []
    
    try:
        # Reddit JSON API
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={max_articles}"
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if not isinstance(data, dict):
            return []
        
        posts_data = data.get("data", {})
        posts = posts_data.get("children", [])
        
        if not isinstance(posts, list):
            return []
        
        # Compile keyword pattern if provided
        keyword_pattern = None
        if keyword:
            try:
                keyword_pattern = re.compile(keyword, re.IGNORECASE)
            except re.error:
                keyword_pattern = None
        
        for post_wrapper in posts[:max_articles]:
            if not isinstance(post_wrapper, dict):
                continue
            
            post = post_wrapper.get("data", {})
            if not isinstance(post, dict):
                continue
            
            title = post.get("title", "")
            if not title:
                continue
            
            # Filter by keyword if provided
            selftext = post.get("selftext", "")
            text_to_check = f"{title} {selftext}"
            if keyword_pattern and not keyword_pattern.search(text_to_check):
                continue
            
            # Get URL (external link or Reddit permalink)
            url = post.get("url", "")
            if url.startswith("/r/"):
                url = f"https://www.reddit.com{url}"
            
            items.append({
                "id": f"reddit-{post.get('id', '')}",
                "title": title,
                "url": url,
                "description": selftext[:500] if selftext else "",
                "pub_date": post.get("created_utc", ""),
                "source": f"Reddit-r/{subreddit}",
                "author": post.get("author", ""),
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "subreddit": subreddit,
            })
            
    except Exception:
        return []
    
    return items
