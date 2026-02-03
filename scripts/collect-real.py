#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 统一采集脚本
从 sources.yaml 读取配置，调用对应的 fetcher
"""

import json
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入 fetchers 统一调度接口
from fetchers import fetch_by_config


def load_sources_config() -> dict:
    """加载 sources.yaml"""
    config_path = project_root / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def collect_with_fallback(sources_config: dict) -> Tuple[List[Dict], List[str]]:
    """
    带降级策略的采集

    Returns:
        (成功采集的数据, 失败的数据源名称列表)
    """
    results = []
    failures = []

    print("📥 开始采集数据源...")
    start_time = datetime.now()

    for source in sources_config.get('sources', []):
        if not source.get('enabled', False):
            continue

        source_name = source['name']
        print(f"\n📡 采集: {source_name}")

        try:
            items = fetch_by_config(source)
            if items:
                results.extend(items)
                print(f"   ✅ {len(items)} 条")
            else:
                print(f"   ⚠️ 无数据")
                failures.append(source_name)
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failures.append(source_name)

        # 避免请求过快
        time.sleep(0.5)

    elapsed = (datetime.now() - start_time).total_seconds()

    if failures:
        print(f"\n⚠️ 失败的数据源: {', '.join(failures)}")

    print(f"\n📊 总计采集 {len(results)} 条数据 ({elapsed:.1f}秒)")

    return results, failures


def sort_by_hot_score(items: List[Dict]) -> List[Dict]:
    """按热度排序"""
    return sorted(items, key=lambda x: x.get('hot_score', 0), reverse=True)


def deduplicate_by_url(items: List[Dict]) -> List[Dict]:
    """基于 URL 去重"""
    seen_urls = set()
    unique_items = []

    for item in items:
        url = item.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item)

    removed = len(items) - len(unique_items)
    if removed > 0:
        print(f"🔗 去重: 移除 {removed} 条重复")

    return unique_items


def generate_report(items: List[Dict]) -> dict:
    """生成日报"""
    return {
        'success': True,
        'title': f'AI Daily - {datetime.now().strftime("%Y-%m-%d")}',
        'generated_at': datetime.now().isoformat(),
        'total_collected': len(items),
        'hotspots': items,
    }


def main():
    print("🚀 AI Daily Collector - 统一采集")
    print("=" * 50)
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 加载配置
        config = load_sources_config()
        total_sources = len(config.get('sources', []))
        enabled_sources = [s['name'] for s in config.get('sources', []) if s.get('enabled', False)]
        disabled_count = total_sources - len(enabled_sources)

        print(f"📋 配置的数据源: {total_sources} 个")
        print(f"✅ 已启用: {len(enabled_sources)} 个")
        if disabled_count > 0:
            print(f"⭕ 已禁用: {disabled_count} 个")
        if enabled_sources:
            print(f"   源列表: {', '.join(enabled_sources[:5])}{'...' if len(enabled_sources) > 5 else ''}")
        print()

        if not enabled_sources:
            print("⚠️ 没有启用的数据源，请检查 config/sources.yaml")
            return 1

        # 采集数据
        items, failures = collect_with_fallback(config)

        if not items:
            print("\n❌ 没有采集到任何数据")
            if failures:
                print(f"   失败源: {', '.join(failures)}")
            return 1

        # 去重
        items = deduplicate_by_url(items)

        # 排序
        items = sort_by_hot_score(items)

        # 限制数量
        max_items = config.get('max_articles', 100)
        if len(items) > max_items:
            items = items[:max_items]
            print(f"✂️  限制数量: 保留前 {max_items} 条")

        # 生成报告
        report = generate_report(items)

        # 创建数据目录
        data_dir = project_root / 'data'
        data_dir.mkdir(exist_ok=True)

        # 保存
        output_file = data_dir / 'daily.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print()
        print("=" * 50)
        print("✅ 采集完成!")
        print(f"   总计: {report['total_collected']} 条")
        print(f"   文件: {output_file}")

        if failures:
            print(f"\n⚠️ 部分数据源失败: {len(failures)} 个")
            print(f"   {', '.join(failures)}")
            return 1  # 有失败但也保存了数据

        return 0

    except FileNotFoundError as e:
        print(f"❌ 配置文件未找到: {e}")
        print("   请确保 config/sources.yaml 存在")
        return 1
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return 1
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
