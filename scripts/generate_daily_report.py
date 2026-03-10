#!/usr/bin/env python3
"""
生成 AI 日报

根据已有数据筛选 AI 相关文章，生成日报
"""

import json
from datetime import datetime
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

def is_ai_related(title: str) -> bool:
    """判断文章是否为 AI 相关"""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in AI_KEYWORDS)

def generate_summary(content: str, title: str, max_length: int = 50) -> str:
    """生成摘要（使用标题作为摘要）"""
    # 简单处理：直接使用标题
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

def extract_tags(title: str, content: str, max_tags: int = 3) -> List[str]:
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
            report += f"  - 标签: {', '.join(a.get('tags', []))}\n\n"

    return report

def main():
    """主函数"""
    import requests

    # 获取今日文章
    date = datetime.now().strftime('%Y-%m-%d')

    print(f"获取 {date} 的文章...")

    # 调用 MCP API
    response = requests.post(
        "https://ai-daily-collector.xxl185.workers.dev/mcp",
        json={
            "tool": "get_articles_by_date",
            "arguments": {
                "date": date,
                "limit": 100
            }
        },
        timeout=30
    )

    if response.status_code != 200:
        print(f"API 调用失败: {response.status_code}")
        return

    data = response.json()
    articles = data.get('articles', [])

    print(f"共获取 {len(articles)} 篇文章")

    # 筛选 AI 相关文章
    ai_articles = []
    for a in articles:
        title = a.get('title', '')
        if is_ai_related(title):
            content = a.get('content', '')

            # 处理文章
            article_data = {
                'id': a.get('id', ''),
                'title': title,
                'url': a.get('url', ''),
                'source': a.get('source', ''),
                'summary': generate_summary(content, title),
                'category': classify_article(title),
                'tags': extract_tags(title, content)
            }
            ai_articles.append(article_data)

    print(f"筛选出 {len(ai_articles)} 篇 AI 相关文章")

    # 生成报告
    report = generate_report(ai_articles, date)

    # 保存报告
    report_path = f"docs/reports/daily_report_{date.replace('-', '')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"报告已保存到: {report_path}")

    # 保存处理后的文章（可选，用于更新数据库）
    processed_path = f"docs/reports/processed_articles_{date.replace('-', '')}.json"
    with open(processed_path, 'w', encoding='utf-8') as f:
        json.dump(ai_articles, f, ensure_ascii=False, indent=2)

    print(f"处理后的文章已保存到: {processed_path}")

if __name__ == '__main__':
    main()
