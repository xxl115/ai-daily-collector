"""文章去重测试"""

import pytest


def test_dedup_by_url():
    """基于 URL 去重"""
    seen_urls = set()
    
    articles = [
        {"url": "https://example.com/1", "title": "A"},
        {"url": "https://example.com/2", "title": "B"},
        {"url": "https://example.com/1", "title": "A重复"},
    ]
    
    new_articles = []
    for a in articles:
        if a['url'] not in seen_urls:
            seen_urls.add(a['url'])
            new_articles.append(a)
    
    assert len(new_articles) == 2


def test_dedup_by_title():
    """基于标题去重"""
    seen_titles = set()
    
    articles = [
        {"title": "AI 突破"},
        {"title": "新芯片"},
        {"title": "AI 突破"},
    ]
    
    new_articles = []
    for a in articles:
        if a['title'] not in seen_titles:
            seen_titles.add(a['title'])
            new_articles.append(a)
    
    assert len(new_articles) == 2


def test_empty_articles():
    """空列表测试"""
    assert len([]) == 0
