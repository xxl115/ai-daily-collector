#!/usr/bin/env python3
"""批量处理所有文章：生成摘要并更新到 D1"""

import json
import subprocess
import time
from pathlib import Path

WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev/mcp"


def generate_summary(article):
    """基于规则生成摘要"""
    title = article.get("title", "")
    content = article.get("content", "")
    source = article.get("source", "")

    # 内容预览
    if content and len(content) > 1000:
        preview = content[:1000]
    else:
        preview = content

    # 对于不同来源使用不同的摘要策略
    if source == "ArXiv":
        # 提取论文摘要
        if "Abstract:" in content:
            abstract = content.split("Abstract:")[1].split("\n")[0].strip()
            return abstract[:200] + "..." if len(abstract) > 200 else abstract
        elif "摘要" in content:
            abstract = content.split("摘要")[1].split("\n")[0].strip()
            return abstract[:200] + "..." if len(abstract) > 200 else abstract
        else:
            return f"{title} - ArXiv 论文"

    elif source in [
        "Hacker News",
        "TechCrunch",
        "VentureBeat",
        "MIT Technology Review",
    ]:
        # 英文文章 - 提取第一句或摘要
        if preview:
            first_sentence = preview.split(".")[0] + "."
            return f"{title}: {first_sentence[:150]}..."
        return title[:150]

    elif source == "36氪":
        # 36氪快讯 - 提取核心信息
        if "36氪获悉" in content:
            news = content.split("36氪获悉")[1].split("原文")[0].strip()
            return news[:150] + "..." if len(news) > 150 else news
        elif "｜" in title:
            # 标题格式：公司名｜内容
            return title.split("｜")[1].strip() if "｜" in title else title[:100]
        return title[:100]

    elif source == "V2EX":
        # V2EX 帖子 - 提取主要讨论点
        if preview:
            lines = preview.split("\n")[:3]
            return " | ".join([l.strip() for l in lines if l.strip()])[:150]
        return title[:100]

    elif source == "钛媒体：引领未来商业与生活新知":
        # 钛媒体
        if "文 |" in content:
            # 提取正文第一段
            body = content.split("文 |")[1].split("\n\n")[0].strip()
            return body[:150] + "..." if len(body) > 150 else body
        return title[:100]

    else:
        # 默认策略
        if preview:
            return preview[:150] + "..."
        return title[:100]


def update_article(article_id, summary):
    """更新单篇文章"""
    payload = {
        "tool": "update_article_summary_and_category",
        "arguments": {
            "article_id": article_id,
            "summary": summary,
            "auto_classify": True,
        },
    }

    cmd = [
        "curl",
        "-s",
        "-X",
        "POST",
        WORKER_URL,
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(payload),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        response = json.loads(result.stdout)
        return response
    except Exception as e:
        return {"error": str(e)}


def main():
    """主函数"""
    # 读取文章
    with open("all_articles_500.json", "r") as f:
        articles = json.load(f)

    print(f"📊 共 {len(articles)} 篇文章待处理")
    print()

    # 可以指定开始索引（用于断点续传）
    start_index = 450
    batch_size = 100  # 每批处理数量

    success_count = 0
    failed_count = 0

    for i in range(start_index, min(start_index + batch_size, len(articles))):
        article = articles[i]
        article_id = article.get("id", "")
        title = article.get("title", "")[:60]
        source = article.get("source", "")

        print(f"[{i + 1}/{len(articles)}] {source} | {title}...")

        # 生成摘要
        summary = generate_summary(article)
        print(f"  摘要: {summary[:100]}...")

        # 更新文章
        result = update_article(article_id, summary)

        if result.get("success"):
            category = result.get("category", "")
            tags = result.get("tags", [])
            print(f"  ✅ 分类: {category} | 标签: {tags}")
            success_count += 1
        else:
            print(f"  ❌ 失败: {result.get('error', 'Unknown')}")
            failed_count += 1

        print()
        time.sleep(0.3)  # 避免请求过快

    print("=" * 50)
    print(f"✅ 批次处理完成！")
    print(f"   成功: {success_count} 篇")
    print(f"   失败: {failed_count} 篇")
    print(f"   进度: {start_index + batch_size}/{len(articles)}")
    print("=" * 50)
    print(f"\n继续处理下一批，请修改 start_index = {start_index + batch_size}")


if __name__ == "__main__":
    main()
