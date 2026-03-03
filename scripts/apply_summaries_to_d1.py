#!/usr/bin/env python3
"""批量应用摘要到 D1 数据库"""

import json
import subprocess
import time

WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev/mcp"


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

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        response = json.loads(result.stdout)
        return response
    except:
        return {"error": result.stdout}


def main():
    """主函数"""
    # 读取摘要文件
    with open("summaries_batch5.json", "r") as f:
        summaries = json.load(f)

    print(f"📊 共 {len(summaries)} 篇文章待处理")
    print()

    success_count = 0
    failed_count = 0

    for i, item in enumerate(summaries, 1):
        article_id = item["id"]
        summary = item["summary"]

        # 显示进度
        aid_short = article_id[:50] + "..." if len(article_id) > 50 else article_id
        print(f"[{i}/{len(summaries)}] {aid_short}")
        print(f"  摘要: {summary}")

        # 更新文章
        result = update_article(article_id, summary)

        if result.get("success"):
            category = result.get("category", "")
            tags = result.get("tags", [])
            print(f"  ✅ 分类: {category} | 标签: {tags}")
            success_count += 1
        else:
            print(f"  ❌ 失败: {result.get('error', 'Unknown error')}")
            failed_count += 1

        print()

        # 避免请求过快
        time.sleep(0.5)

    print("=" * 50)
    print(f"✅ 处理完成！")
    print(f"   成功: {success_count} 篇")
    print(f"   失败: {failed_count} 篇")
    print("=" * 50)


if __name__ == "__main__":
    main()
