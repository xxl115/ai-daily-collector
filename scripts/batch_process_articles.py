#!/usr/bin/env python3
"""批量为文章生成摘要并更新到 D1（使用 Claude）"""

import json
import asyncio
import aiohttp
from datetime import datetime

WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev/mcp"


async def get_articles_with_empty_summary(limit=200):
    """获取所有 summary 为空的文章"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "tool": "get_articles_with_empty_summary",
            "arguments": {"limit": limit},
        }
        async with session.post(WORKER_URL, json=payload) as resp:
            result = await resp.json()
            return result.get("articles", [])


async def update_article(article_id, summary, category=None, tags=None):
    """更新文章摘要并自动分类"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "tool": "update_article_summary_and_category",
            "arguments": {
                "article_id": article_id,
                "summary": summary,
                "auto_classify": True,
            },
        }

        if category:
            payload["arguments"]["category"] = category
            payload["arguments"]["auto_classify"] = False
        if tags:
            payload["arguments"]["tags"] = tags

        async with session.post(WORKER_URL, json=payload) as resp:
            return await resp.json()


async def main():
    """主函数"""
    print("📥 获取需要处理的文章...")
    articles = await get_articles_with_empty_summary(limit=200)

    if not articles:
        print("✅ 没有需要处理的文章")
        return

    print(f"📊 找到 {len(articles)} 篇需要处理的文章")
    print()

    # 输出文章列表供 Claude 处理
    print("=" * 60)
    print("请为以下文章生成摘要（JSON 格式）：")
    print("=" * 60)

    articles_data = []
    for i, a in enumerate(articles[:50], 1):  # 每次处理 50 篇
        aid = a.get("id", "")
        title = a.get("title", "")
        source = a.get("source", "")
        content = a.get("content", "")
        url = a.get("url", "")

        # 内容预览
        if content and len(content) > 500:
            preview = content[:500] + "..."
        else:
            preview = content

        articles_data.append(
            {
                "index": i,
                "id": aid,
                "title": title,
                "source": source,
                "url": url,
                "content_preview": preview,
            }
        )

    # 输出为 JSON 文件
    with open("articles_to_summarize.json", "w") as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已导出 {len(articles_data)} 篇文章到 articles_to_summarize.json")
    print()
    print("请处理 articles_to_summarize.json，添加 summary 字段，然后运行:")
    print("  python3 scripts/apply_summaries.py")


if __name__ == "__main__":
    asyncio.run(main())
