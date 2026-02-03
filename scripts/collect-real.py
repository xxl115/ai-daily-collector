#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 简化的采集脚本 (用于 GitHub Actions)

功能:
1. 采集多平台 AI 热点资讯
2. 生成每日报告
3. 保存到 data/daily.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fetchers import (
        fetch_v2ex_hotspots,
        fetch_reddit_hotspots,
        fetch_ai_blogs,
        fetch_tech_media,
    )
    from utils.filter import keyword_filter, sort_by_hotness
    FETCHERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 抓取器导入失败: {e}")
    FETCHERS_AVAILABLE = False


def fetch_all_hotspots(max_per_source: int = 10) -> list:
    """采集所有数据源"""
    all_items = []
    
    print("📥 开始采集数据源...")
    start_time = datetime.now()
    
    # 1. V2EX
    try:
        if FETCHERS_AVAILABLE:
            v2ex = fetch_v2ex_hotspots(limit=max_per_source)
            print(f"   ✅ V2EX: {len(v2ex)} 条")
            all_items.extend(v2ex)
        else:
            print("   ⏭️ V2EX (抓取器不可用)")
    except Exception as e:
        print(f"   ❌ V2EX 失败: {e}")
    
    # 2. Reddit
    try:
        if FETCHERS_AVAILABLE:
            reddit = fetch_reddit_hotspots(limit=max_per_source)
            print(f"   ✅ Reddit: {len(reddit)} 条")
            all_items.extend(reddit)
        else:
            print("   ⏭取器不可用️ Reddit (抓)")
    except Exception as e:
        print(f"   ❌ Reddit 失败: {e}")
    
    # 3. AI 博客
    try:
        if FETCHERS_AVAILABLE:
            blogs = fetch_ai_blogs(limit=max_per_source)
            print(f"   ✅ AI 博客: {sum(len(v) for v in blogs.values())} 条")
            for source, items in blogs.items():
                for item in items:
                    item['source'] = source
                    all_items.append(item)
        else:
            print("   ⏭️ AI 博客 (抓取器不可用)")
    except Exception as e:
        print(f"   ❌ AI 博客 失败: {e}")
    
    # 4. 科技媒体
    try:
        if FETCHERS_AVAILABLE:
            media = fetch_tech_media(limit=max_per_source)
            print(f"   ✅ 科技媒体: {sum(len(v) for v in media.values())} 条")
            for source, items in media.items():
                for item in items:
                    item['source'] = source
                    all_items.append(item)
        else:
            print("   ⏭️ 科技媒体 (抓取器不可用)")
    except Exception as e:
        print(f"   ❌ 科技媒体 失败: {e}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n📊 总计采集 {len(all_items)} 条数据 ({elapsed:.1f}秒)")
    
    return all_items


def process_hotspots(items: list, limit: int = 30) -> list:
    """处理和排序热点"""
    if not items:
        return []
    
    # 去重
    seen = set()
    unique_items = []
    for item in items:
        url = item.get('url', '')
        if url and url not in seen:
            seen.add(url)
            unique_items.append(item)
    
    # 过滤无效项目
    valid_items = [item for item in unique_items if item.get('title')]
    
    # 排序
    sorted_items = sort_by_hotness(valid_items)
    
    return sorted_items[:limit]


def generate_report(items: list) -> dict:
    """生成日报"""
    return {
        'success': True,
        'title': f'AI Daily - {datetime.now().strftime("%Y-%m-%d")}',
        'generated_at': datetime.now().isoformat(),
        'total_collected': len(items),
        'hotspots': items,
    }


def main():
    """主函数"""
    print("🚀 AI Daily Collector - 真实数据采集")
    print("=" * 50)
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建数据目录
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # 采集数据
    items = fetch_all_hotspots(max_per_source=10)
    
    # 处理数据
    print("\n🔄 处理数据...")
    hotspots = process_hotspots(items, limit=30)
    print(f"   ✅ 保留 {len(hotspots)} 条热点")
    
    # 生成报告
    print("\n📝 生成日报...")
    report = generate_report(hotspots)
    
    # 保存到文件
    output_file = data_dir / 'daily.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 已保存到: {output_file}")
    
    print()
    print("=" * 50)
    print("✅ 采集完成!")
    print(f"   总计: {report['total_collected']} 条")
    print(f"   热点: {len(hotspots)} 条")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
