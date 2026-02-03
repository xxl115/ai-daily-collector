#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 真实数据采集 (独立运行版)
不依赖项目模块，直接抓取数据
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False
    print("⚠️ requests/beautifulsoup4 未安装，将使用示例数据")


def fetch_v2ex_hotspots(limit=10):
    """抓取 V2EX 热门"""
    if not IMPORTS_OK:
        return []
    
    try:
        url = "https://www.v2ex.com/api/v2/topics/hot"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            data = resp.json()
            items = []
            for item in data[:limit]:
                items.append({
                    "title": item.get("title", ""),
                    "url": f"https://www.v2ex.com/t/{item.get('id')}",
                    "source": "V2EX",
                    "hot_score": 100 - len(items),
                    "timestamp": datetime.now().isoformat(),
                })
            print(f"   ✅ V2EX: {len(items)} 条")
            return items
    except Exception as e:
        print(f"   ❌ V2EX 失败: {e}")
    return []


def fetch_hacker_news(limit=10):
    """抓取 Hacker News AI 相关"""
    if not IMPORTS_OK:
        return []
    
    try:
        # 获取 top stories
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        if resp.ok:
            ids = resp.json()[:30]
            items = []
            for story_id in ids:
                try:
                    story_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=5)
                    if story_resp.ok:
                        story = story_resp.json()
                        title = story.get("title", "")
                        # 过滤 AI 相关
                        if any(kw in title.lower() for kw in ["ai", "llm", "gpt", "claude", "agent", "mcp", "deepseek"]):
                            items.append({
                                "title": title,
                                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                "source": "Hacker News",
                                "hot_score": story.get("score", 0),
                                "timestamp": datetime.fromtimestamp(story.get("time", 0)).isoformat() if story.get("time") else datetime.now().isoformat(),
                            })
                            if len(items) >= limit:
                                break
                except:
                    pass
            print(f"   ✅ Hacker News: {len(items)} 条")
            return items
    except Exception as e:
        print(f"   ❌ Hacker News 失败: {e}")
    return []


def fetch_github_trending(limit=10):
    """抓取 GitHub Trending AI"""
    if not IMPORTS_OK:
        return []
    
    try:
        url = "https://github.com/trending?spoken_language_code=en"
        resp = requests.get(url, timeout=15)
        if resp.ok:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = []
            for article in soup.select('article.Box-row')[:limit]:
                title_elem = article.select_one('h2 a')
                if title_elem:
                    title = title_elem.get_text(strip=True).replace('\n', '').replace(' ', '')
                    url = "https://github.com" + title_elem.get('href', '')
                    stars_elem = article.select_one('span.float-right')
                    stars = stars_elem.get_text(strip=True) if stars_elem else "0"
                    
                    items.append({
                        "title": f"[GitHub] {title}",
                        "url": url,
                        "source": "GitHub Trending",
                        "hot_score": 100 + int(stars.replace(',', '')) if stars.replace(',', '').isdigit() else 50,
                        "timestamp": datetime.now().isoformat(),
                    })
            print(f"   ✅ GitHub Trending: {len(items)} 条")
            return items
    except Exception as e:
        print(f"   ❌ GitHub Trending 失败: {e}")
    return []


def fetch_ai_blogs(limit=5):
    """抓取 AI 官方博客"""
    if not IMPORTS_OK:
        return []
    
    blogs = [
        {"name": "OpenAI", "url": "https://openai.com/blog/rss.xml"},
        {"name": "Google AI", "url": "https://developers.google.com/feeds/blog.xml?alt=rss"},
    ]
    
    items = []
    for blog in blogs:
        try:
            resp = requests.get(blog["url"], timeout=10)
            if resp.ok:
                soup = BeautifulSoup(resp.text, 'xml')
                for entry in soup.select('entry')[:limit]:
                    title = entry.select_one('title')
                    link = entry.select_one('link')
                    items.append({
                        "title": title.get_text(strip=True) if title else "",
                        "url": link.get('href') if link else "",
                        "source": f"AI Blog - {blog['name']}",
                        "hot_score": 80,
                        "timestamp": datetime.now().isoformat(),
                    })
        except Exception as e:
            print(f"   ❌ {blog['name']} 失败: {e}")
    
    print(f"   ✅ AI Blogs: {len(items)} 条")
    return items


def fetch_dev_to(limit=10):
    """抓取 Dev.to AI 文章"""
    if not IMPORTS_OK:
        return []
    
    try:
        url = "https://dev.to/api/articles?tag=ai&top=1"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            articles = resp.json()
            items = []
            for article in articles[:limit]:
                items.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": "Dev.to",
                    "hot_score": article.get("positive_reactions_count", 0),
                    "timestamp": article.get("published_at", datetime.now().isoformat()),
                })
            print(f"   ✅ Dev.to: {len(items)} 条")
            return items
    except Exception as e:
        print(f"   ❌ Dev.to 失败: {e}")
    return []


def fetch_all_hotspots():
    """采集所有数据源"""
    all_items = []
    
    print("📥 开始采集数据源...")
    start_time = datetime.now()
    
    # 1. V2EX
    all_items.extend(fetch_v2ex_hotspots(limit=10))
    time.sleep(0.5)
    
    # 2. Hacker News
    all_items.extend(fetch_hacker_news(limit=10))
    time.sleep(0.5)
    
    # 3. GitHub Trending
    all_items.extend(fetch_github_trending(limit=10))
    time.sleep(0.5)
    
    # 4. AI Blogs
    all_items.extend(fetch_ai_blogs(limit=5))
    time.sleep(0.5)
    
    # 5. Dev.to
    all_items.extend(fetch_dev_to(limit=10))
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n📊 总计采集 {len(all_items)} 条数据 ({elapsed:.1f}秒)")
    
    return all_items


def sort_hotspots(items):
    """简单排序"""
    # 按 hot_score 排序
    return sorted(items, key=lambda x: x.get('hot_score', 0), reverse=True)


def generate_report(items):
    """生成日报"""
    return {
        'success': True,
        'title': f'AI Daily - {datetime.now().strftime("%Y-%m-%d")}',
        'generated_at': datetime.now().isoformat(),
        'total_collected': len(items),
        'hotspots': items,
    }


def main():
    print("🚀 AI Daily Collector - 真实数据采集")
    print("=" * 50)
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建数据目录
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    if IMPORTS_OK:
        # 真实采集
        items = fetch_all_hotspots()
        items = sort_hotspots(items)
    else:
        # 示例数据
        print("⚠️ 使用示例数据")
        items = [{
            "title": "AI Daily Collector - 真实数据采集中",
            "url": "https://github.com/xxl115/ai-daily-collector",
            "source": "GitHub",
            "hot_score": 100,
            "timestamp": datetime.now().isoformat(),
        }]
    
    print("\n🔄 处理数据...")
    print(f"   ✅ 保留 {len(items)} 条热点")
    
    print("\n📝 生成日报...")
    report = generate_report(items)
    
    # 保存到文件
    output_file = data_dir / 'daily.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 已保存到: {output_file}")
    
    print()
    print("=" * 50)
    print("✅ 采集完成!")
    print(f"   总计: {report['total_collected']} 条")
    print(f"   热点: {len(items)} 条")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
