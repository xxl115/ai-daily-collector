#!/usr/bin/env python3
"""
生成 AI 日报

根据已有数据筛选 AI 相关文章，生成日报
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# AI 关键词库
AI_KEYWORDS = [
    'AI', '人工智能', 'LLM', 'GPT', '大模型', '模型', '机器学习', '深度学习',
    '神经网络', 'OpenAI', 'Claude', 'Gemini', '文心', '通义', '智谱',
    '芯片', 'GPU', '算力', '自动驾驶', '机器人', '智能驾驶', '智能汽车',
    '论文', 'arXiv', '研究', '算法', '训练', '推理', 'RAG', 'Embedding',
    'Agent', '多模态', 'Sora', '视频生成', '图像生成', 'AIGC', 'AGI',
    '千问', '通义', '文心', '智谱', 'MiniMax', '阶跃', '月之暗面',
    'Sora', 'Runway', 'Pika', 'Midjourney', 'DALL-E',
    '自动驾驶', '智能驾驶', 'FSD', 'NOA',
    '大模型', '参数', '训练', '推理', '微调', 'RAG', '向量数据库'
]

# 预设分类
CATEGORIES = ['大厂', '人物', '产品', '技术', '商业', '学术', '其他']

# 配置
WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev"
DEFAULT_DATE = datetime.now().strftime('%Y-%m-%d')
DEFAULT_LIMIT = 100
MAX_SUMMARY_LENGTH = 50
MAX_TAGS = 3

def is_ai_related(title: str) -> bool:
    """判断文章是否为 AI 相关"""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in AI_KEYWORDS)

def generate_summary(title: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """生成摘要（使用标题作为摘要）"""
    return title[:max_length] + ('...' if len(title) > max_length else '')

def classify_article(title: str) -> str:
    """简单的规则分类"""
    title_lower = title.lower()

    if any(kw in title for kw in ['融资', '投资', '上市', '股价', '财报', '营收', '利润']):
        return '商业'

    if any(kw in title for kw in ['发布', '推出', '新品', '开售', '上市', '发布']):
        return '产品'

    if any(kw in title for kw in ['论文', '研究', '发布', '实验', '数据', '算法']):
        return '技术'

    if any(kw in title for kw in ['教授', 'CEO', '创始人', 'CTO', '副总裁', '总监']):
        return '人物'

    if any(kw in title for kw in ['大学', '研究院', '实验室', 'arXiv']):
        return '学术'

    if any(kw in title for kw in ['阿里', '腾讯', '百度', '字节', '华为', '小米', 'OpenAI', 'Google']):
        return '大厂'

    return '其他'

def extract_tags(title: str, max_tags: int = MAX_TAGS) -> List[str]:
    """提取标签（只从标题提取）"""
    tags = []

    # 从标题中提取关键词
    for kw in AI_KEYWORDS:
        if kw.lower() in title.lower() and kw not in tags:
            tags.append(kw)
        if len(tags) >= max_tags:
            break

    return tags[:max_tags]

def generate_report(articles: List[Dict[str, Any]], date: str) -> str:
    """生成 Markdown 日报"""

    # 统计
    category_count = {}
    for a in articles:
        cat = a.get('category', '其他')
        category_count[cat] = category_count.get(cat, 0) + 1

    # 生成报告
    report = f"""# {date} AI 日报

## 统计

| 指标 | 数值 |
|------|------|
| 总文章数 | {len(articles)} 篇 |

## 分类统计

| 分类 | 数量 |
|------|------|
"""
    for cat, count in sorted(category_count.items(), key=lambda x: -x[1]):
        report += f"| {cat} | {count} |\n"

    # 按分类组织文章
    for cat in CATEGORIES:
        cat_articles = [a for a in articles if a.get('category') == cat]
        if not cat_articles:
            continue

        report += f"\n## {cat}\n\n"
        for a in cat_articles:
            report += f"- **{a.get('title', '无标题')}**\n"
            report += f"  - 摘要: {a.get('summary', '无摘要')}\n"
            report += f"  - 标签: {', '.join(a.get('tags', []))}\n"
            report += f"  - 来源: {a.get('source', '未知')}\n\n"

    return report

def update_database(article: Dict[str, Any]) -> bool:
    """更新数据库中的文章"""
    try:
        import requests
    except ImportError:
        print("Error: requests not installed")
        return False

    response = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "update_article_summary_and_category",
            "arguments": {
                "article_id": article['id'],
                "summary": article['summary'],
                "category": article['category'],  # MCP 使用 category（单数）
                "tags": article['tags'],
                "auto_classify": False  # 使用手动指定的分类和标签
            }
        },
        timeout=30
    )

    if response.status_code != 200:
        print(f"更新失败 [{article['id'][:30]}...]: {response.status_code}")
        return False

    result = response.json()
    if result.get('success'):
        print(f"✓ 更新成功: {article['title'][:40]}")
        return True
    else:
        print(f"✗ 更新失败 [{article['id'][:30]}...]: {result.get('error', '未知错误')}")
        return False

def main():
    """主函数"""
    try:
        import requests
    except ImportError:
        print("Error: requests not installed")
        print("Install: pip install requests")
        sys.exit(1)

    # 解析参数
    date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATE
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LIMIT

    print(f"获取 {date} 的文章...")

    # 调用 MCP API
    response = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "get_articles_by_date",
            "arguments": {
                "date": date,
                "limit": limit
            }
        },
        timeout=30
    )

    if response.status_code != 200:
        print(f"API 调用失败: {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()
    articles = data.get('articles', [])

    print(f"共获取 {len(articles)} 篇文章")

    # 筛选 AI 相关文章
    ai_articles = []
    for a in articles:
        title = a.get('title', '')
        if is_ai_related(title):
            # 处理文章
            article_data = {
                'id': a.get('id', ''),
                'title': title,
                'url': a.get('url', ''),
                'source': a.get('source', ''),
                'summary': generate_summary(title),
                'category': classify_article(title),
                'tags': extract_tags(title)
            }
            ai_articles.append(article_data)

    print(f"筛选出 {len(ai_articles)} 篇 AI 相关文章")

    if len(ai_articles) == 0:
        print("没有 AI 相关文章，退出")
        sys.exit(0)

    # 创建输出目录
    reports_dir = Path("~/code/ai-daily-collector/docs/reports").expanduser()
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 生成报告
    report = generate_report(ai_articles, date)

    # 保存报告
    report_path = reports_dir / f"daily_report_{date.replace('-', '')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"报告已保存到: {report_path}")

    # 保存处理后的文章（可选，用于更新数据库）
    processed_path = reports_dir / f"processed_articles_{date.replace('-', '')}.json"
    with open(processed_path, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, ensure_ascii=False, indent=2)

    print(f"处理后的文章已保存到: {processed_path}")

    # 更新数据库
    print(f"\n开始更新数据库...")
    success_count = 0
    for article in ai_articles:
        if update_database(article):
            success_count += 1

    print(f"\n更新完成: {success_count}/{len(ai_articles)} 篇文章")
    print(f"\n全部完成！")

if __name__ == '__main__':
    main()
