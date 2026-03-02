#!/usr/bin/env python3
"""生成昨日文章总结报告"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path.cwd()))

from datetime import datetime, timedelta, timezone
from collections import defaultdict

from config.config import load_config_from_env, get_storage_adapter
from api.storage.dao import ArticleDAO


def generate_yesterday_report(target_date=None):
    """生成昨日文章总结报告

    Args:
        target_date: 指定日期字符串 (YYYY-MM-DD)，默认昨天
    """
    config = load_config_from_env()
    storage = get_storage_adapter(config)
    dao = ArticleDAO(storage_adapter=storage)

    # 确定目标日期
    if target_date:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
    else:
        target_date = datetime.now(timezone.utc) - timedelta(days=1)

    date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    print(f"查询日期: {date_start.strftime('%Y-%m-%d')}")

    # 查询指定日期的文章
    filters = {
        "date_start": date_start.isoformat(),
        "date_end": date_end.isoformat(),
    }
    articles = dao.fetch_articles(filters=filters, limit=1000)

    print(f"找到 {len(articles)} 篇文章\n")

    # 分类统计
    category_map = defaultdict(list)
    for article in articles:
        art_dict = article.model_dump()
        categories = art_dict.get("categories", [])
        if categories:
            category = categories[0]
        else:
            category = "未分类"
        category_map[category].append(article)

    # 生成报告
    report_lines = []

    # 标题
    report_lines.append(f"# AI 日报 - {target_date.strftime('%Y年%m月%d日')}")

    # 生成时间
    report_lines.append(
        f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    report_lines.append(f"**文章总数**: {len(articles)}")

    # 今日焦点（推荐 3 篇重要文章）
    if len(articles) >= 3:
        # 选择前 3 篇文章作为今日焦点
        top_articles = articles[:3]
        report_lines.append("\n---\n")
        report_lines.append("## 今日焦点\n")

        for i, article in enumerate(top_articles, 1):
            title = getattr(article, "title", "无标题")
            summary = getattr(article, "summary", None)

            report_lines.append(
                f"{i}. **[{title}]({summary[:50] if summary else '无摘要'}...**"
            )
    else:
        report_lines.append("\n---\n")

    # 按分类展示
    report_lines.append("\n---\n")
    for category in sorted(category_map.keys()):
        articles_in_cat = category_map[category]
        if category == "未分类":
            report_lines.append(f"\n## {category} ({len(articles_in_cat)} 篇)\n")
        else:
            report_lines.append(f"\n## {category}\n")

        for i, article in enumerate(articles_in_cat, 1):
            # 直接使用 article 对象的属性
            title = getattr(article, "title", "无标题")
            url = getattr(article, "url", "")
            summary = getattr(article, "summary", None)
            tags = getattr(article, "tags", None) or []

            # 文章标题
            report_lines.append(f"### {i}. {title}")

            # 摘要（如果有）
            if summary:
                report_lines.append(f"**摘要**: {summary}")
            else:
                report_lines.append("**摘要**: 无")

            # 标签（如果有）
            if tags:
                report_lines.append(f"**标签**: {', '.join(tags)}")

            # 链接
            report_lines.append(f"**链接**: {url}")

            # 分隔线
            report_lines.append("")

    # 统计信息
    report_lines.append("---\n")
    report_lines.append("## 统计信息\n")
    report_lines.append(f"| 分类 | 数量 |")
    report_lines.append(f"|------|------|")
    for category in sorted(category_map.keys()):
        report_lines.append(f"| {category} | {len(category_map[category])} |")

    # 标签统计
    all_tags = []
    for article in articles:
        art_dict = article.model_dump()
        tags = art_dict.get("tags", [])
        all_tags.extend(tags)

    tag_counts = defaultdict(int)
    for tag in all_tags:
        tag_counts[tag] += 1

    if tag_counts:
        report_lines.append("\n### 标签统计\n")
        report_lines.append("| 标签 | 出现次数 |")
        report_lines.append("|------|----------|")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
            :20
        ]:
            report_lines.append(f"| {tag} | {count} |")

    # 返回报告
    return "\n".join(report_lines), target_date


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成文章总结报告")
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)，默认昨天")
    args = parser.parse_args()

    print("=" * 60)
    print("生成文章总结报告")
    print("=" * 60)

    report, target_date = generate_yesterday_report(target_date=args.date)

    # 打印报告
    print("\n" + report)

    # 保存到文件
    report_path = Path("ai/reports/daily_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    filename = f"daily_report_{target_date.strftime('%Y%m%d')}.md"
    full_path = report_path.parent / filename

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存到: {full_path}")


if __name__ == "__main__":
    main()
