#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 每日热点采集工作流

功能:
1. 采集多平台 AI 热点资讯
2. 关键词过滤和智能排序
3. 生成每日报告
4. 多渠道推送

支持的数据源:
- RSS 订阅 (英文 AI 资讯)
- GitHub Trending
- Hacker News
- Product Hunt
- NewsNow (中文热点)
- V2EX 热门
- Reddit 热门
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    DEFAULT_CONFIG,
)
from utils.logger import setup_logger, get_logger
from utils.rss import RSSGenerator
from utils.notification import notification_manager
from utils.filter import keyword_filter, sort_by_hotness
from utils.cache import cache
from utils.rate_limit import limiter
from utils.errors import retry, FallbackManager, fallback_return_empty

# 导入抓取器（使用 fetchers 模块）
from fetchers import (
    fetch_by_config,           # 统一调度接口
    fetch_newsnow_hotspots,
    fetch_v2ex_hotspots,
    fetch_reddit_hotspots,
    fetch_tech_media_hotspots,  # 替代原来的 RSS 采集
    fetch_ai_blog_hotspots,     # AI 博客
)

# GitHub Trending 需要单独实现或使用第三方服务
# 暂时注释掉，后续可以添加
# from collectors.github import fetch_github_trending
# from collectors.hackernews import fetch_hacker_news
# from collectors.producthunt import fetch_product_hunt


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    setup_logger(
        name="ai-daily",
        level=level,
        log_file=DEFAULT_CONFIG["log_file"],
        max_bytes=DEFAULT_CONFIG["log_max_bytes"],
        backup_count=DEFAULT_CONFIG["log_backup_count"],
    )


def collect_all_sources(config: Dict) -> Dict[str, List[Dict]]:
    """
    采集所有数据源（从 sources.yaml 读取配置）

    Returns:
        采集结果字典
    """
    import yaml
    from pathlib import Path

    logger = get_logger(__name__)
    results = {
        "tech_media": [],    # 科技媒体（包括中文）
        "ai_blogs": [],      # AI 官方博客
        "newsnow": [],       # NewsNow 中文热点
        "v2ex": [],          # V2EX
        "reddit": [],        # Reddit
    }

    logger.info("=" * 60)
    logger.info("开始采集 AI 热点资讯")
    logger.info("=" * 60)

    # 加载 sources.yaml 配置
    config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            sources_config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return results

    # 遍历配置中的每个数据源
    for source in sources_config.get('sources', []):
        if not source.get('enabled', False):
            continue

        source_name = source['name']
        source_type = source.get('type', '')

        logger.info(f"\n📡 采集: {source_name}")

        try:
            # 使用统一调度接口
            items = fetch_by_config(source)

            if items:
                # 根据类型归类
                if source_type == 'tech_media':
                    results['tech_media'].extend(items)
                elif source_type == 'ai_blogs':
                    results['ai_blogs'].extend(items)
                elif source_type == 'newsnow':
                    results['newsnow'].extend(items)
                elif source_type == 'v2ex':
                    results['v2ex'].extend(items)
                elif source_type == 'reddit':
                    results['reddit'].extend(items)
                else:
                    # 未知类型，放入 tech_media
                    results['tech_media'].extend(items)

                logger.info(f"   ✅ {source_name}: {len(items)} 条")
            else:
                logger.info(f"   ⚠️ {source_name}: 无数据")

        except Exception as e:
            logger.error(f"   ❌ {source_name}: {e}")

    # 统计
    total = sum(len(v) for v in results.values())
    logger.info("\n" + "=" * 60)
    logger.info(f"采集完成! 总计: {total} 条")
    logger.info("=" * 60)

    return results


def filter_and_process(articles: List[Dict], config: Dict) -> List[Dict]:
    """
    过滤和处理文章
    
    Args:
        articles: 原始文章列表
        config: 配置
    
    Returns:
        处理后的文章列表
    """
    logger = get_logger(__name__)
    
    # 1. 关键词过滤
    if config.get("enable_filter", True):
        logger.info("\n🔍 应用关键词过滤...")
        matched, filtered = keyword_filter.filter_articles(
            articles,
            title_field="title",
        )
        logger.info(f"   匹配: {len(matched)}, 过滤: {len(filtered)}")
        articles = matched
    
    # 2. 去重 (基于 URL)
    seen_urls = set()
    unique_articles = []
    for article in articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    logger.info(f"\n🔗 去重: {len(unique_articles)} 条")
    
    # 3. 按热度排序
    if config.get("enable_sorting", True):
        logger.info("\n📊 按热度排序...")
        unique_articles = sort_by_hotness(
            unique_articles,
            rank_field="rank",
            count_field="count",
            rank_weight=0.6,
            frequency_weight=0.3,
            hotness_weight=0.1,
        )
    
    # 限制数量
    limit = config.get("max_articles", 50)
    return unique_articles[:limit]


def generate_report(
    articles: List[Dict],
    config: Dict,
    output_dir: Path,
) -> Path:
    """
    生成每日报告
    
    Returns:
        报告文件路径
    """
    logger = get_logger(__name__)
    
    beijing_tz = __import__("pytz").timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    date_str = now.strftime("%Y-%m-%d")
    
    # 按来源分组
    sources = {}
    for article in articles:
        source = article.get("source", "Unknown")
        if source not in sources:
            sources[source] = []
        sources[source].append(article)
    
    # 生成 Markdown 报告
    report_content = f"""# AI Daily - {date_str}

> 生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
> 总计: {len(articles)} 条

## 统计

| 来源 | 数量 |
|------|------|
"""
    for source, items in sorted(sources.items(), key=lambda x: -len(x[1])):
        report_content += f"| {source} | {len(items)} |\n"
    
    report_content += "\n## 热点排行\n\n"
    
    for i, article in enumerate(articles[:30], 1):
        title = article.get("title", "无标题")
        url = article.get("url", "")
        source = article.get("source", "")
        rank = article.get("rank", 0)
        hot_score = article.get("hot_score", 0)
        
        if url:
            report_content += f"{i}. **[{title}]({url})**\n"
        else:
            report_content += f"{i}. **{title}**\n"
        
        report_content += f"   - 来源: {source}"
        if rank:
            report_content += f" | 排名: #{rank}"
        if hot_score:
            report_content += f" | 热度: {hot_score}"
        report_content += "\n\n"
    
    # 保存报告
    report_file = output_dir / f"ai-hotspot-{date_str}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"\n📄 报告已生成: {report_file}")
    return report_file


def generate_rss_feed(
    articles: List[Dict],
    config: Dict,
    output_dir: Path,
) -> Path:
    """
    生成 RSS Feed
    
    Returns:
        RSS 文件路径
    """
    beijing_tz = __import__("pytz").timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    date_str = now.strftime("%Y-%m-%d")
    
    rss = RSSGenerator(
        title="AI Daily - 人工智能热点资讯",
        link="https://github.com/xxl115/ai-daily-collector",
        description="每日 AI 热点资讯聚合，包括 RSS 订阅、GitHub Trending、Hacker News、NewsNow、V2EX、Reddit 等多平台内容",
        language="zh-CN",
    )
    
    for article in articles[:30]:
        rss.add_item(
            title=article.get("title", "无标题"),
            link=article.get("url", ""),
            description=article.get("summary", "")[:500],
            pub_date=now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            guid=article.get("url", ""),
            category=article.get("source", ""),
        )
    
    rss_content = rss.generate()
    
    # 保存 RSS
    rss_file = output_dir / f"rss/{date_str}.xml"
    rss_file.parent.mkdir(parents=True, exist_ok=True)
    with open(rss_file, "w", encoding="utf-8") as f:
        f.write(rss_content)
    
    return rss_file


def send_notifications(
    articles: List[Dict],
    config: Dict,
    report_file: Path,
):
    """
    发送推送通知
    """
    logger = get_logger(__name__)
    
    if not config.get("enable_notification", True):
        logger.info("\n🔕 推送已禁用")
        return
    
    # 获取配置状态
    status = notification_manager.get_config_status()
    configured_platforms = [
        p for p, s in status.items() if s.get("configured")
    ]
    
    if not configured_platforms:
        logger.info("\n🔕 未配置任何推送渠道")
        return
    
    beijing_tz = __import__("pytz").timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    
    # 构建推送内容
    title = f"AI Daily - {now.strftime('%m/%d')} 热点 ({len(articles)} 条)"
    
    content = f"## {title}\n\n"
    for i, article in enumerate(articles[:10], 1):
        title_text = article.get("title", "")[:50]
        source = article.get("source", "")
        url = article.get("url", "")
        
        if url:
            content += f"{i}. [{title_text}]({url}) ({source})\n"
        else:
            content += f"{i}. {title_text} ({source})\n"
    
    content += f"\n... 共 {len(articles)} 条"
    
    # 发送到各平台
    logger.info(f"\n📱 推送到: {', '.join(configured_platforms)}")
    
    results = notification_manager.send_to_all(
        title=title,
        content=content,
    )
    
    for platform, success in results.items():
        if success:
            logger.info(f"   ✅ {platform}")
        else:
            logger.info(f"   ❌ {platform}")


def run_workflow(args: argparse.Namespace):
    """运行完整工作流"""
    # 加载配置
    config = DEFAULT_CONFIG.copy()
    config.update({
        "enable_rss": not args.skip_rss,
        "enable_github": not args.skip_github,
        "enable_hackernews": not args.skip_hn,
        "enable_producthunt": not args.skip_ph,
        "enable_newsnow": not args.skip_newsnow,
        "enable_v2ex": not args.skip_v2ex,
        "enable_reddit": not args.skip_reddit,
        "enable_filter": not args.no_filter,
        "enable_sorting": not args.no_sort,
        "enable_notification": not args.no_notify,
    })
    
    # 设置日志
    setup_logging(args.verbose)
    logger = get_logger(__name__)
    
    try:
        # 1. 采集数据
        results = collect_all_sources(config)
        
        # 合并所有文章
        all_articles = []
        for articles in results.values():
            all_articles.extend(articles)
        
        logger.info(f"\n📊 采集总计: {len(all_articles)} 条")
        
        # 2. 过滤和处理
        articles = filter_and_process(all_articles, config)
        
        # 3. 输出目录
        output_dir = Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 生成报告
        report_file = generate_report(articles, config, output_dir)
        
        # 5. 生成 RSS
        rss_file = generate_rss_feed(articles, config, output_dir)
        
        # 6. 发送推送
        send_notifications(articles, config, report_file)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 工作流完成!")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"工作流失败: {e}")
        sys.exit(1)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="AI Daily Collector - 每日 AI 热点采集工作流"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细日志模式",
    )
    
    # 跳过选项
    skip_group = parser.add_argument_group("跳过采集")
    skip_group.add_argument(
        "--skip-rss",
        action="store_true",
        help="跳过 RSS 采集",
    )
    skip_group.add_argument(
        "--skip-github",
        action="store_true",
        help="跳过 GitHub Trending 采集",
    )
    skip_group.add_argument(
        "--skip-hn",
        action="store_true",
        help="跳过 Hacker News 采集",
    )
    skip_group.add_argument(
        "--skip-ph",
        action="store_true",
        help="跳过 Product Hunt 采集",
    )
    skip_group.add_argument(
        "--skip-newsnow",
        action="store_true",
        help="跳过 NewsNow 采集",
    )
    skip_group.add_argument(
        "--skip-v2ex",
        action="store_true",
        help="跳过 V2EX 采集",
    )
    skip_group.add_argument(
        "--skip-reddit",
        action="store_true",
        help="跳过 Reddit 采集",
    )
    
    # 处理选项
    process_group = parser.add_argument_group("处理选项")
    process_group.add_argument(
        "--no-filter",
        action="store_true",
        help="跳过关键词过滤",
    )
    process_group.add_argument(
        "--no-sort",
        action="store_true",
        help="跳过排序",
    )
    process_group.add_argument(
        "--no-notify",
        action="store_true",
        help="跳过推送",
    )
    
    args = parser.parse_args()
    run_workflow(args)


if __name__ == "__main__":
    main()
