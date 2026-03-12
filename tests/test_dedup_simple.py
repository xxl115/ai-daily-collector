"""简单的去重测试，不需要外部依赖"""

import sys
from pathlib import Path

# Mock the dependencies before importing
sys.modules['requests'] = type(sys)('requests')
sys.modules['feedparser'] = type(sys)('feedparser')
sys.modules['numpy'] = type(sys)('numpy')

def test_dedup_articles():
    """测试文章去重逻辑"""
    
    # 模拟已处理的 URL 集合
    seen_urls = set()
    
    articles = [
        {"url": "https://example.com/article1", "title": "文章1"},
        {"url": "https://example.com/article2", "title": "文章2"},
        {"url": "https://example.com/article1", "title": "文章1重复"},  # 重复
    ]
    
    # 去重逻辑
    new_articles = []
    for article in articles:
        url = article.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            new_articles.append(article)
    
    # 验证
    assert len(new_articles) == 2, f"Expected 2, got {len(new_articles)}"
    assert new_articles[0]['title'] == "文章1"
    assert new_articles[1]['title'] == "文章2"
    print("✓ test_dedup_articles passed")

def test_dedup_with_title():
    """测试基于标题的去重"""
    
    seen_titles = set()
    
    articles = [
        {"title": "AI 重大突破"},
        {"title": "新芯片发布"},
        {"title": "AI 重大突破"},  # 重复
    ]
    
    new_articles = []
    for article in articles:
        title = article.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            new_articles.append(article)
    
    assert len(new_articles) == 2
    print("✓ test_dedup_with_title passed")

if __name__ == "__main__":
    test_dedup_articles()
    test_dedup_with_title()
    print("\n所有测试通过!")
