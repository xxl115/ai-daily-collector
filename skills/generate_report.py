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
OPENCODE_CLI = "/home/young/.opencode/bin/opencode"
DEFAULT_DATE = datetime.now().strftime('%Y-%m-%d')
DEFAULT_LIMIT = 100
MAX_SUMMARY_LENGTH = 50
MAX_TAGS = 3

def is_ai_related(title: str) -> bool:
    """判断文章是否为 AI 相关"""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in AI_KEYWORDS)

def generate_summary_with_llm(content: str, title: str) -> tuple:
    """使用 LLM 生成摘要、分类和标签"""
    import subprocess
    import json

    # 清理内容（只保留前 3000 字）
    import re
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'https?://[^\s]+', '', content)
    content = content[:3000]

    # 调用 OpenCode CLI (使用 run 命令）
    prompt = f"""分析文章，返回JSON结果：

标题：{title}

内容：{content}

输出格式（直接输出JSON，无其他文字）：
{{"summary":"30字摘要","category":"分类","tags":["标签1","标签2"]}}

分类选项：大厂、人物、产品、技术、商业、学术、其他"""

    try:
        result = subprocess.run(
            [OPENCODE_CLI, "run", "--model", "opencode/minimax-m2.5-free", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout:
            content_text = result.stdout.strip()

            # 提取 JSON 部分（更宽松的匹配）
            import re
            json_match = re.search(r'\{[^{}]+\}', content_text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                summary = data.get('summary', title[:50])
                category = data.get('category', '其他')
                tags = data.get('tags', [])

                print(f"✓ LLM 处理: {title[:30]}")
                return summary, category, tags

    except Exception as e:
        print(f"LLM 调用失败: {e}")

    # 失败时回退到规则
    print(f"→ 回退到规则: {title[:30]}")
    return generate_summary(content, title), classify_article(title), extract_tags(title)

def generate_summary(content: str, title: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """生成摘要（从文章内容提取关键信息）"""
    if not content:
        return title[:max_length] + ('...' if len(title) > max_length else '')

    # 清理内容
    import re
    content = re.sub(r'<[^>]+>', '', content)  # 去除 HTML
    content = re.sub(r'https?://[^\s]+', '', content)  # 去除链接
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)  # 去除 MD 链接
    content = re.sub(r'!\[.*?\]\([^)]+\)', '', content)  # 去除图片

    # 去除明显的导航元素
    lines = content.split('\n')
    content_lines = []
    skip_prefixes = ['首页', '登录', '注册', '搜索', '百度', '推荐', 'V2EX', 'way to explore',
                     'Skip to', 'Promoted', 'PRO', 'Copyright', '版权']

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        if len(line) < 10:  # 太短的行
            continue
        content_lines.append(line)

    content = ' '.join(content_lines)

    # 提取关键句子的优先级
    candidates = []

    # 1. 找包含数字和具体信息的句子（通常是关键信息）
    import re
    sentences = [s.strip() for s in content.replace('！', '。').replace('？', '。').split('。') if s.strip()]

    for s in sentences:
        if len(s) < 20 or len(s) > 300:
            continue
        if '强烈建议' in s or '浏览器' in s or '登录' in s:
            continue

        score = 0

        # 包含数字（加权重）
        if re.search(r'\d+', s):
            score += 3

        # 包含金额/百分比（高权重）
        if re.search(r'[¥$€]\s*\d+|\d+\s*%', s):
            score += 5

        # 包含中文（保证内容质量）
        if any('\u4e00' <= c <= '\u9fff' for c in s):
            score += 2

        # 包含关键动词
        action_words = ['发布', '推出', '宣布', '推出', '完成', '实现', '获得', '达成',
                       '突破', '增长', '提升', '研发', '开发', '上线', '启动']
        if any(w in s for w in action_words):
            score += 4

        # 包含公司/机构
        org_words = ['公司', '集团', '科技', '实验室', '研究院', '大学', 'AI', 'OpenAI']
        if any(w in s for w in org_words):
            score += 3

        if score > 0:
            candidates.append((score, s))

    # 按评分排序，取最高分的
    if candidates:
        candidates.sort(key=lambda x: -x[0])
        summary = candidates[0][1]
        return summary[:max_length] + ('...' if len(summary) > max_length else '')

    # 都没找到，找第一个长句子
    for s in sentences:
        if 50 <= len(s) <= 200 and any('\u4e00' <= c <= '\u9fff' for c in s):
            return s[:max_length] + ('...' if len(s) > max_length else '')

    # 最后，用标题
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

    # 去除代理环境变量
    import os
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

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
        timeout=30,
        proxies=None,  # 不使用代理
        verify=True  # 验证 SSL
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

    # 去除代理
    import os
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

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
        timeout=30,
        proxies=None,
        verify=True
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
        content = a.get('content', '')
        if is_ai_related(title):
            # 使用 LLM 生成摘要、分类、标签
            summary, category, tags = generate_summary_with_llm(content, title)

            # 处理文章
            article_data = {
                'id': a.get('id', ''),
                'title': title,
                'url': a.get('url', ''),
                'source': a.get('source', ''),
                'summary': summary,
                'category': category,
                'tags': tags
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
