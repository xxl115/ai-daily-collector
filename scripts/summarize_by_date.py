#!/usr/bin/env python3
"""总结指定日期范围的文章"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path.cwd()))

from datetime import datetime, timedelta, timezone
import argparse
import json

from config.config import load_config_from_env, get_storage_adapter
from api.storage.dao import ArticleDAO
from scripts.summarizers.ollama_summarizer import OllamaSummarizer


def get_articles_by_date_range(date_start=None, date_end=None, source=None):
    """获取指定日期范围的文章

    Args:
        date_start: 开始日期字符串 (YYYY-MM-DD) 或 datetime 对象
        date_end: 结束日期字符串 (YYYY-MM-DD) 或 datetime 对象
        source: 可选，按来源过滤

    Returns:
        (articles_list, date_start_str, date_end_str)
    """
    config = load_config_from_env()
    storage = get_storage_adapter(config)
    dao = ArticleDAO(storage_adapter=storage)

    # 构建日期范围
    if date_start:
        if isinstance(date_start, str):
            date_start = datetime.strptime(date_start, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
    else:
        date_start = datetime.now(timezone.utc) - timedelta(days=1)

    date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_end:
        if isinstance(date_end, str):
            date_end = datetime.strptime(date_end, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
    else:
        date_end = date_start + timedelta(days=1)

    date_end = date_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 构建查询参数
    filters = {
        "date_start": date_start.isoformat(),
        "date_end": date_end.isoformat(),
    }
    if source:
        filters["source"] = source

    # 使用数据库日期过滤查询
    articles = dao.fetch_articles(filters=filters, limit=1000)

    return articles, date_start.isoformat(), date_end.isoformat()


def summarize_articles(
    articles, dry_run=False, force=False, include_summary_status=True
):
    """批量总结文章

    Args:
        articles: 文章列表
        dry_run: 预览模式，不实际生成摘要
        force: 强制重新总结已有摘要的文章
        include_summary_status: 是否只处理无摘要的文章

    Returns:
        处理结果字典
    """
    summarizer = OllamaSummarizer()
    config = load_config_from_env()
    storage = get_storage_adapter(config)

    results = {
        "total": len(articles),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "articles": [],
    }

    for article in articles:
        art_dict = article.model_dump()

        # 检查是否已经有摘要
        has_summary = bool(art_dict.get("summary"))

        if not force and has_summary:
            results["skipped"] += 1
            results["articles"].append(
                {
                    "id": article.id,
                    "title": article.title,
                    "status": "skipped",
                    "reason": "已有摘要",
                }
            )
            continue

        # 如果 include_summary_status=False 且有摘要，则强制跳过
        if include_summary_status and has_summary and not force:
            results["skipped"] += 1
            results["articles"].append(
                {
                    "id": article.id,
                    "title": article.title,
                    "status": "skipped",
                    "reason": "已有摘要",
                }
            )
            continue

        print(f"处理: {article.title}")

        if dry_run:
            results["processed"] += 1
            results["articles"].append(
                {"id": article.id, "title": article.title, "status": "dry_run"}
            )
            continue

        try:
            # 生成摘要
            summary = summarizer.summarize(article.content[:3000])

            # 更新文章
            article.summary = summary
            storage.upsert_article(article)

            results["processed"] += 1
            results["articles"].append(
                {"id": article.id, "title": article.title, "status": "success"}
            )
            print(f"  ✅ 摘要: {summary[:50]}...")

        except Exception as e:
            results["failed"] += 1
            results["articles"].append(
                {
                    "id": article.id,
                    "title": article.title,
                    "status": "failed",
                    "error": str(e),
                }
            )
            print(f"  ❌ 失败: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="总结指定日期范围的文章",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 总结昨天的文章
  python scripts/summarize_by_date.py

  # 总结指定日期的文章
  python scripts/summarize_by_date.py --date 2026-03-01

  # 总结日期范围的文章
  python scripts/summarize_by_date.py --date-start 2026-03-01 --date-end 2026-03-03

  # 预览模式
  python scripts/summarize_by_date.py --date 2026-03-01 --dry-run

  # 强制重新总结所有文章
  python scripts/summarize_by_date.py --date 2026-03-01 --force

  # 只处理特定来源的文章
  python scripts/summarize_by_date.py --date 2026-03-01 --source rss
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="预览模式，不实际生成摘要"
    )
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)，默认昨天")
    parser.add_argument("--date-start", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--date-end", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--source", help="只处理指定来源的文章")
    parser.add_argument(
        "--force", action="store_true", help="强制重新总结已有摘要的文章"
    )
    parser.add_argument("--output", help="输出结果到 JSON 文件")
    args = parser.parse_args()

    # 参数验证
    if args.date and (args.date_start or args.date_end):
        print("错误: 不能同时使用 --date 和 --date-start/--date-end")
        return 1

    if (args.date_start and not args.date_end) or (
        args.date_end and not args.date_start
    ):
        print("错误: --date-start 和 --date-end 必须同时使用")
        return 1

    print("=" * 60)
    print("总结指定日期范围的文章")
    print("=" * 60)

    # 获取指定日期范围的文章
    articles, date_start_str, date_end_str = get_articles_by_date_range(
        date_start=args.date,
        date_end=args.date if args.date else None,
        source=args.source,
    )

    print(f"日期范围: {date_start_str[:10]} ~ {date_end_str[:10]}")
    if args.source:
        print(f"来源过滤: {args.source}")
    print(f"找到 {len(articles)} 篇文章")

    if not articles:
        print("没有找到文章")
        return 0

    # 显示文章列表
    print("\n文章列表:")
    for i, article in enumerate(articles, 1):
        art_dict = article.model_dump()
        has_summary = bool(art_dict.get("summary"))
        print(f"  {i}. {article.title}")
        print(f"     ID: {article.id}")
        print(f"     有摘要: {'是' if has_summary else '否'}")
        if args.source and article.source != args.source:
            print(f"     来源: {article.source}")

    # 统计摘要状态
    has_summary_count = sum(1 for a in articles if a.summary)
    no_summary_count = len(articles) - has_summary_count
    print(f"\n摘要状态: {has_summary_count} 篇有摘要, {no_summary_count} 篇无摘要")

    # 确认
    if not args.dry_run:
        if args.force:
            print(f"\n警告: --force 模式将重新总结所有 {len(articles)} 篇文章！")
            print("确认要处理这些文章吗？(yes/no): ", end="")
            confirm = input().strip().lower()
            if confirm != "yes":
                print("已取消")
                return 0
        else:
            print(f"\n将处理 {no_summary_count} 篇无摘要的文章。")
            print("确认要处理这些文章吗？(y/n): ", end="")
            confirm = input().strip().lower()
            if confirm != "y":
                print("已取消")
                return 0

    # 批量总结
    print("\n" + "=" * 60)
    print("开始处理...")
    print("=" * 60)

    results = summarize_articles(articles, dry_run=args.dry_run, force=args.force)

    # 显示结果
    print("\n" + "=" * 60)
    print("处理结果")
    print("=" * 60)
    print(f"总数: {results['total']}")
    print(f"处理成功: {results['processed']}")
    print(f"跳过（已有摘要）: {results['skipped']}")
    print(f"失败: {results['failed']}")

    # 输出到文件
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n结果已保存到: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
