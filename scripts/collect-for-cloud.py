#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 云端采集脚本（含原文提取）
从 sources.yaml 读取配置，提取原文并保存到文件
"""

import json
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False
    print("ERROR: requests 未安装", file=sys.stderr)
    sys.exit(1)

from fetchers import fetch_by_config


def load_sources_config():
    """加载 sources.yaml"""
    config_path = project_root / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_content(url, max_length=5000):
    """使用 jina.ai 提取原文内容"""
    try:
        clean_url = url.replace('https://', '').replace('http://', '')
        api_url = "https://r.jina.ai/http://" + clean_url
        response = requests.get(api_url, timeout=15)
        if response.ok:
            content = response.text
            content = re.sub(r'<[^>]+>', '\n', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
            return content.strip()[:max_length]
    except:
        pass
    return ""


def save_article(article, output_dir):
    """保存单篇文章到文件"""
    source = article['source']
    title = article['title']
    url = article['url']
    score = article.get('score', 0)

    timestamp = int(datetime.now().timestamp())
    source_short = source.split()[0] if ' ' in source else source[:3]
    filename = f"{source_short}_{score}_{timestamp}.md"

    print(f"   📄 {source}: {title[:50]}")
    content = extract_content(url)

    file_content = f"""---
title: "{title}"
url: "{url}"
source: "{source}"
date: {datetime.now().strftime('%Y-%m-%d')}
score: {score}
---

# {title}

**来源**: [{source}]({url}) | **热度**: {score}

## 原文内容

{content if content else "*内容提取失败*"}

---
*自动采集于 {datetime.now().strftime('%Y-%m-%d')}*
"""

    filepath = output_dir / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return True
    except Exception as e:
        print(f"ERROR: 保存文件失败 {filepath}: {e}", file=sys.stderr)
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="采集 AI 热点资讯（云端版）")
    parser.add_argument('--output-dir', type=str, help='输出目录')
    parser.add_argument('--limit', type=int, help='每源文章数量限制')
    parser.add_argument('--total-limit', type=int, default=50, help='总文章数量限制')

    args = parser.parse_args()

    # 配置输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_dir = project_root / 'ai' / 'articles' / 'original' / date_str

    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载配置
    config = load_sources_config()

    print("============================================")
    print("AI Daily Collector (Cloud Enhanced)")
    print(f"日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"输出目录: {output_dir}")
    print("============================================")
    print()

    total_count = 0
    source_counts = {}

    # 采集每个数据源
    for source in config.get('sources', []):
        if not source.get('enabled', False):
            continue

        source_name = source['name']
        print(f"📥 采集 {source_name}...", flush=True)

        try:
            items = fetch_by_config(source)

            # 限制每源文章数量
            if args.limit:
                items = items[:args.limit]

            # 保存文章
            source_count = 0
            for item in items:
                if total_count >= args.total_limit:
                    break

                article = {
                    'source': source_name,
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'score': item.get('hot_score', 0),
                }

                if save_article(article, output_dir):
                    source_count += 1
                    total_count += 1

            source_counts[source_name] = source_count
            print(f"   -> {source_name}: {source_count} 条", flush=True)

        except Exception as e:
            print(f"   ❌ {source_name}: {e}", flush=True)

        print()

        if total_count >= args.total_limit:
            break

    print("============================================")
    print(f"📊 采集完成! 总计: {total_count} 条")
    for source, count in source_counts.items():
        print(f"   - {source}: {count}")
    print("============================================")
    print()
    print(f"✅ 完成! 文件保存于: {output_dir}/")

    return 0


if __name__ == '__main__':
    sys.exit(main())
