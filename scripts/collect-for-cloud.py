#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 云端采集辅助脚本

从 sources.yaml 读取配置，输出 bash 可用的数据格式

输出格式:
SOURCE|TITLE|URL|SCORE|AUTHOR

用法:
    python scripts/collect-for-cloud.py

输出示例:
    Hacker News|Agent Skills|https://example.com|100|john
    GitHub|awesome-ai|https://github.com/...|500|octocat
"""

import json
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger, get_logger
from utils.filter import keyword_filter

# 导入 fetchers
from fetchers import (
    fetch_by_config,
)

# 导入配置
import yaml


def load_sources_config():
    """加载 sources.yaml 配置"""
    config_path = project_root / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def collect_from_sources():
    """从配置的数据源采集"""
    sources_config = load_sources_config()
    all_articles = []

    for source in sources_config.get('sources', []):
        if not source.get('enabled', False):
            continue

        source_name = source.get('name', 'Unknown')
        source_type = source.get('type', '')

        try:
            items = fetch_by_config(source)
            if items:
                all_articles.extend(items)
                print(f"✅ {source_name}: {len(items)} 条", file=sys.stderr)
            else:
                print(f"⚠️ {source_name}: 无数据", file=sys.stderr)
        except Exception as e:
            print(f"❌ {source_name}: {e}", file=sys.stderr)

    return all_articles


def filter_articles(articles):
    """过滤文章"""
    if not articles:
        return []

    matched, _ = keyword_filter.filter_articles(
        articles,
        title_field="title",
    )

    return matched


def output_for_bash(articles):
    """输出 bash 可用的格式"""
    # 按热度排序
    articles.sort(key=lambda x: x.get('hot_score', 0), reverse=True)

    for article in articles:
        source = article.get('source', 'Unknown')
        title = article.get('title', '').replace('|', '\\|').replace('\n', ' ')
        url = article.get('url', '')
        score = article.get('hot_score', 0)
        author = article.get('author', article.get('source_id', ''))

        # 输出: SOURCE|TITLE|URL|SCORE|AUTHOR
        print(f"{source}|{title}|{url}|{score}|{author}")


def main():
    """主函数"""
    print("📥 开始采集...", file=sys.stderr)

    # 采集数据
    articles = collect_from_sources()
    print(f"\n📊 总计采集: {len(articles)} 条", file=sys.stderr)

    # 过滤
    articles = filter_articles(articles)
    print(f"🔍 过滤后: {len(articles)} 条", file=sys.stderr)

    # 输出
    output_for_bash(articles)


if __name__ == "__main__":
    main()
