#!/usr/bin/env python3
"""
AI 日报生成 - 分步执行（全部通过数据库）

步骤 1: 筛选 AI 相关文章，更新数据库标记
步骤 2: 从数据库获取已标记文章，生成摘要、分类、标签并更新
步骤 3: 从数据库获取已处理文章，生成 AI 日报
"""

import json
import sys
import subprocess
import re
import requests
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

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

# 配置
WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev"
OPENCODE_CLI = "/home/young/.opencode/bin/opencode"
DEFAULT_DATE = datetime.now().strftime('%Y-%m-%d')

# 可用模型列表（按优先级）
LLM_MODELS = [
    "opencode/mimo-v2-flash-free",  # 最快
    "opencode/minimax-m2.5-free",  # 备用
    "google/gemini-2.0-flash",     # 备用（需要 API key）
]

def call_llm_with_fallback(prompt: str) -> str:
    """尝试多个模型，自动切换"""
    for model in LLM_MODELS:
        try:
            result = subprocess.run(
                [OPENCODE_CLI, "run", "--model", model, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except Exception as e:
            print(f"  模型 {model} 失败: {e}")
            continue
    return ""

# ==================== 辅助函数 ====================

def is_ai_related(title: str) -> bool:
    """使用 LLM 判断文章是否为 AI 相关"""
    prompt = '判断以下标题是否为AI相关文章（AI、大模型、GPT、机器学习、自动驾驶、机器人等）：' + title + '回答格式：{"is_ai": true/false}'
    
    try:
        result = subprocess.run(
            [OPENCODE_CLI, "run", "--model", "opencode/mimo-v2-flash-free", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            import re, json
            match = re.search(r'\{.*?\}', result.stdout)
            if match:
                data = json.loads(match.group(0))
                if data.get('is_ai'):
                    return True
    except:
        pass
    
    # 失败时回退到关键词匹配
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in AI_KEYWORDS)

def generate_summary_with_llm(content: str, title: str) -> Tuple[str, str, List[str]]:
    """优先使用规则方法生成摘要、分类和标签（更快）"""
    # 清理内容（只保留前 3000 字）
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'https?://[^\s]+', '', content)
    content = content[:1500]

    # 调用 OpenCode CLI (使用 run 命令）
    prompt = f"""分析文章，返回JSON结果：

标题：{title}

内容：{content}

输出格式（直接输出JSON，无其他文字）：
{{"summary":"30字摘要","category":"分类","tags":["标签1","标签2"]}}

分类选项：大厂、人物、产品、技术、商业、学术、其他"""

    try:
        result = subprocess.run(
            [OPENCODE_CLI, "run", "--model", "opencode/mimo-v2-flash-free", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0 and result.stdout:
            content_text = result.stdout.strip()

            # 提取 JSON 部分（更宽松的匹配）
            json_match = re.search(r'\{[^{}]+\}', content_text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                summary = data.get('summary', title[:50])
                category = data.get('category', '其他')
                tags = data.get('tags', [])

                print(f"  ✓ LLM 处理: {title[:30]}")
                return summary, category, tags

    except Exception as e:
        print(f"  ✗ LLM 调用失败: {e}")

    # 失败时回退到规则
    print(f"  → 回退到规则: {title[:30]}")
    return (
        generate_summary_rule(content, title),
        classify_article_rule(title),
        extract_tags_rule(title)
    )

def generate_summary_with_llm_old(content: str, title: str) -> Tuple[str, str, List[str]]:
    """使用 LLM 生成摘要、分类和标签（备用）"""

def generate_summary_rule(content: str, title: str, max_length: int = 50) -> str:
    """规则：生成摘要（从文章内容提取）"""
    if not content:
        return title[:max_length] + ('...' if len(title) > max_length else '')

    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'https?://[^\s]+', '', content)
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'!\[.*?\]\([^)]+\)', '', content)

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
        if len(line) < 10:
            continue
        content_lines.append(line)

    content = ' '.join(content_lines)

    sentences = [s.strip() for s in content.replace('！', '。').replace('？', '。').split('。') if s.strip()]

    candidates = []

    for s in sentences:
        if len(s) < 20 or len(s) > 300:
            continue
        if '强烈建议' in s or '浏览器' in s or '登录' in s:
            continue

        score = 0

        if re.search(r'\d+', s):
            score += 3

        if re.search(r'[¥$€]\s*\d+|\d+\s*%', s):
            score += 5

        if any('\u4e00' <= c <= '\u9fff' for c in s):
            score += 2

        action_words = ['发布', '推出', '宣布', '推出', '完成', '实现', '获得', '达成',
                       '突破', '增长', '提升', '研发', '开发', '上线', '启动']
        if any(w in s for w in action_words):
            score += 4

        org_words = ['公司', '集团', '科技', '实验室', '研究院', '大学', 'AI', 'OpenAI']
        if any(w in s for w in org_words):
            score += 3

        if score > 0:
            candidates.append((score, s))

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        summary = candidates[0][1]
        return summary[:max_length] + ('...' if len(summary) > max_length else '')

    for s in sentences:
        if 50 <= len(s) <= 200 and any('\u4e00' <= c <= '\u9fff' for c in s):
            return s[:max_length] + ('...' if len(s) > max_length else '')

    return title[:max_length] + ('...' if len(title) > max_length else '')

def classify_article_rule(title: str) -> str:
    """规则：简单的规则分类"""
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

def extract_tags_rule(title: str, max_tags: int = 3) -> list:
    """规则：提取标签（只从标题提取）"""
    tags = []

    for kw in AI_KEYWORDS:
        if kw.lower() in title.lower() and kw not in tags:
            tags.append(kw)
        if len(tags) >= max_tags:
            break

    return tags[:max_tags]

# ==================== 主步骤函数 ====================

def step1_mark_ai_articles(date: str, limit: int = 100) -> List[Dict]:
    """步骤 1: 筛选 AI 相关文章，更新数据库标记"""
    print(f"\n{'='*60}")
    print(f"步骤 1: 筛选 AI 相关文章并标记到数据库")
    print(f"{'='*60}")

    # 获取文章
    print(f"\n获取 {date} 的文章...")
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

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
        print(f"获取失败: {response.status_code}")
        return []

    data = response.json()
    articles = data.get('articles', [])

    print(f"共获取 {len(articles)} 篇文章")

    # 筛选 AI 相关并立即标记到数据库
    ai_articles = []
    success_count = 0
    for a in articles:
        title = a.get('title', '')
        if is_ai_related(title):
            # 立即更新数据库标记
            if update_ai_related_flag(a):
                success_count += 1
                ai_articles.append({
                    'id': a.get('id', ''),
                    'title': title,
                    'content': a.get('content', '')
                })

    print(f"筛选出 {len(ai_articles)} 篇 AI 相关文章")
    print(f"\n✅ 步骤 1 完成，共标记 {success_count}/{len(ai_articles)} 篇文章到数据库")

    return ai_articles

def update_ai_related_flag(article: Dict) -> bool:
    """更新数据库中的 AI 相关标记 - 使用 is_ai_related 字段"""
    import time
    
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

    # 重试 3 次
    for attempt in range(3):
        try:
            response = requests.post(
                f"{WORKER_URL}/mcp",
                json={
                    "tool": "update_article_summary_and_category",
                    "arguments": {
                        "article_id": article['id'],
                        "summary": "",  # 空摘要
                        "is_ai_related": True,  # 新字段
                        "auto_classify": False
                    }
                },
                timeout=30,
                proxies=None,
                verify=True
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)  # 等待 2 秒后重试
            else:
                print(f"  ✗ 更新失败: {article['id'][:30]} - {e}")
                return False
    
    time.sleep(1)  # 每请求间隔 1 秒

    if response.status_code != 200:
        print(f"  ✗ 更新失败: {article['id'][:30]}")
        return False

    result = response.json()
    if result.get('success'):
        print(f"  ✓ 标记 AI 相关: {article['title'][:40]}")
        return True
    else:
        print(f"  ✗ 更新失败: {result.get('error', '未知错误')}")
        return False

def step2_process_articles(date: str) -> List[Dict]:
    """步骤 2: 从数据库获取已标记文章，处理并更新"""
    print(f"\n{'='*60}")
    print(f"步骤 2: 从数据库获取已标记文章，生成摘要、分类、标签并更新")
    print(f"{'='*60}")

    # 从数据库获取指定日期的所有文章
    print(f"\n获取 {date} 的文章...")
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

    response = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "get_articles_by_date",
            "arguments": {
                "date": date,
                "limit": 100
            }
        },
        timeout=30,
        proxies=None,
        verify=True
    )

    if response.status_code != 200:
        print(f"获取失败: {response.status_code}")
        return []

    data = response.json()
    articles = data.get('articles', [])

    print(f"共获取 {len(articles)} 篇文章")

    # 筛选 AI 相关文章（检查 [AI] 标记或标题匹配）
    ai_articles = []
    for a in articles:
        title = a.get('title', '')
        summary = a.get('summary', '') or ''
        is_ai_flag = a.get('is_ai_related', False)
        
        # 两种情况：
        # 1. 已经被标记（is_ai_related = True）
        # 2. 标题匹配 AI 关键词
        is_marked = is_ai_flag  # 从数据库读取
        is_ai_keyword = is_ai_related(title)
        
        if is_marked or is_ai_keyword:
            # 去掉 [AI] 前缀获取真实摘要
            real_summary = summary[4:].strip() if summary.startswith('[AI]') else summary
            
            ai_articles.append({
                'id': a.get('id', ''),
                'title': title,
                'content': a.get('content', ''),
                'existing_summary': real_summary
            })

    print(f"找到 {len(ai_articles)} 篇 AI 相关文章")

    # 处理每篇文章
    processed_articles = []
    for article in ai_articles:
        title = article.get('title', '')
        content = article.get('content', '')

        # 如果已有摘要（已处理过），跳过
        if article.get('existing_summary'):
            print(f"  → 跳过（已处理）: {title[:30]}")
            continue

        # 使用规则方法
        summary = title[:50]
        category = classify_article_rule(title)
        tags = extract_tags_rule(title)

        # 更新数据库
        if update_article_to_database(article['id'], summary, category, tags):
            processed_articles.append({
                'id': article['id'],
                'title': title,
                'summary': summary,
                'category': category,
                'tags': tags
            })

    print(f"\n✅ 步骤 2 完成，已处理并更新 {len(processed_articles)} 篇文章到数据库")

    return processed_articles

def update_article_to_database(article_id: str, summary: str, category: str, tags: List) -> bool:
    """更新文章的摘要、分类、标签到数据库"""
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

    response = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "update_article_summary_and_category",
            "arguments": {
                "article_id": article_id,
                "summary": summary,
                "category": category,
                "tags": tags,
                "auto_classify": False  # 使用手动指定的分类和标签
            }
        },
        timeout=30,
        proxies=None,
        verify=True
    )

    if response.status_code != 200:
        print(f"  ✗ 更新失败: {article_id[:30]}")
        return False

    result = response.json()
    if result.get('success'):
        print(f"  ✓ 更新成功")
        return True
    else:
        print(f"  ✗ 更新失败: {result.get('error', '未知错误')}")
        return False

def step3_generate_report_from_database(date: str):
    """步骤 3: 从数据库获取文章并生成 AI 日报"""
    print(f"\n{'='*60}")
    print(f"步骤 3: 从数据库获取文章并生成 AI 日报")
    print(f"{'='*60}")

    # 从数据库获取指定日期的所有文章
    print(f"\n获取 {date} 的文章...")
    env = os.environ.copy()
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

    response = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "get_articles_by_date",
            "arguments": {
                "date": date,
                "limit": 100
            }
        },
        timeout=30,
        proxies=None,
        verify=True
    )

    if response.status_code != 200:
        print(f"获取失败: {response.status_code}")
        return

    data = response.json()
    articles = data.get('articles', [])

    print(f"共获取 {len(articles)} 篇文章")

    # 筛选有摘要的文章（已处理过的 AI 相关文章）
    processed_articles = []
    for a in articles:
        title = a.get('title', '')
        summary = a.get('summary', '')
        if summary and summary != 'None' and summary.strip() and is_ai_related(title):
            processed_articles.append({
                'id': a.get('id', ''),
                'title': title,
                'url': a.get('url', ''),
                'source': a.get('source', ''),
                'summary': summary,
                'category': a.get('categories', ['其他'])[0] if a.get('categories') else '其他',
                'tags': a.get('tags', [])
            })

    print(f"找到 {len(processed_articles)} 篇已处理的文章")

    if not processed_articles:
        print("没有已处理的文章，请先运行步骤 2")
        return

    # 统计
    category_count = {}
    for a in processed_articles:
        cat = a.get('category', '其他')
        category_count[cat] = category_count.get(cat, 0) + 1

    # 生成报告
    report = f"""# {date} AI 日报

## 统计

| 指标 | 数值 |
|------|------|
| 总文章数 | {len(processed_articles)} 篇 |

## 分类统计

| 分类 | 数量 |
|------|------|
"""
    for cat, count in sorted(category_count.items(), key=lambda x: -x[1]):
        report += f"| {cat} | {count} |\n"

    # 按分类组织
    categories = ['大厂', '人物', '产品', '技术', '商业', '学术', '其他']
    for cat in categories:
        cat_articles = [a for a in processed_articles if a.get('category') == cat]
        if not cat_articles:
            continue

        report += f"\n## {cat}\n\n"
        for a in cat_articles:
            report += f"- **{a.get('title', '无标题')}**\n"
            report += f"  - 摘要: {a.get('summary', '无摘要')}\n"
            report += f"  - 标签: {', '.join(a.get('tags', []))}\n\n"

    # 保存报告
    reports_dir = Path("~/code/ai-daily-collector/docs/reports").expanduser()
    report_file = reports_dir / f"daily_report_{date.replace('-', '')}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 步骤 3 完成")
    print(f"日报已保存到: {report_file}")

# ==================== 主函数 ====================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='AI 日报生成 - 全部通过数据库')
    parser.add_argument('--step', type=int, choices=[1, 2, 3],
                       help='执行步骤 (1: 标记, 2: 处理, 3: 日报)')
    parser.add_argument('--date', type=str, default=DEFAULT_DATE,
                       help=f'日期 (默认: {DEFAULT_DATE})')
    parser.add_argument("--limit", type=int, default=100,
                       help='文章数量 (默认: 100)')

    args = parser.parse_args()

    if args.step == 1:
        ai_articles = step1_mark_ai_articles(args.date, args.limit)
        print(f"\n✅ 步骤 1 完成")
    elif args.step == 2:
        processed_articles = step2_process_articles(args.date)
    elif args.step == 3:
        step3_generate_report_from_database(args.date)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
