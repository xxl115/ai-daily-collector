"""Hacker News API scraper."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import json
import re
from datetime import datetime


def fetch_hackernews(keyword: str = "", hours: int = 24, max_articles: int = 30) -> List[Dict[str, Any]]:
    """Fetch top stories from Hacker News.
    
    Uses the official Firebase API (https://github.com/HackerNews/API).
    
    Args:
        keyword: Filter keywords (e.g., "AI|ml|agent|mcp|llm")
        hours: Time window (not directly supported by API, used for filtering)
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    items: List[Dict[str, Any]] = []
    
    try:
        # Get top stories IDs
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(top_stories_url, timeout=30) as response:
            story_ids = json.loads(response.read().decode('utf-8'))
        
        if not isinstance(story_ids, list):
            return []
        
        # Compile keyword pattern if provided
        keyword_pattern = None
        if keyword:
            try:
                keyword_pattern = re.compile(keyword, re.IGNORECASE)
            except re.error:
                keyword_pattern = None
        
        # Fetch details for each story
        for story_id in story_ids[:max_articles * 2]:  # Fetch more to allow for filtering
            if len(items) >= max_articles:
                break
                
            try:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                with urllib.request.urlopen(story_url, timeout=10) as response:
                    story = json.loads(response.read().decode('utf-8'))
                
                if not isinstance(story, dict):
                    continue
                
                title = story.get("title", "")
                if not title:
                    continue
                
                # Filter by keyword if provided
                if keyword_pattern and not keyword_pattern.search(title):
                    continue
                
                # Get URL (use story URL or HN discussion URL)
                url = story.get("url", "")
                if not url:
                    url = f"https://news.ycombinator.com/item?id={story_id}"
                
                # Get timestamp
                timestamp = story.get("time", 0)
                pub_date = datetime.fromtimestamp(timestamp).isoformat() if timestamp else ""
                
                items.append({
                    "id": f"hn-{story_id}",
                    "title": title,
                    "url": url,
                    "description": story.get("text", "")[:500],  # Truncate long text
                    "pub_date": pub_date,
                    "source": "Hacker News",
                    "score": story.get("score", 0),
                    "comments": story.get("descendants", 0),
                })
                
            except Exception:
                continue
                
    except Exception:
        return []
    
    return items[:max_articles]
