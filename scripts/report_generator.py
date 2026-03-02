import json
import os
from datetime import datetime
from typing import List, Dict


class ReportGenerator:
    """日报生成器"""

    def __init__(self):
        self.categories = {
            "breaking": "🚨 突发新闻",
            "hot": "🔥 热门话题",
            "new": "🆕 新品发布",
            "deep": "💡 深度分析",
        }

    def generate(self, articles: List[Dict], output_path: str):
        categorized = {cat: [] for cat in self.categories}
        for article in articles:
            cat = article.get("category", "new")
            if cat in categorized:
                categorized[cat].append(article)
        total = len(articles)
        md = f"""# AI Daily Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"""
        md += "## 📊 统计概览\n\n"
        md += f"- **总文章数**: {total}\n"
        for cat, title in self.categories.items():
            md += f"- **{title}**: {len(categorized[cat])} 篇\n"
        md += "\n---\n\n"
        for cat, title in self.categories.items():
            if categorized[cat]:
                md += f"## {title}\n\n"
                for article in categorized[cat]:
                    md += f"### {article['title']}\n\n"
                    md += f"- **来源**: {article.get('source', '未知')}\n"
                    md += f"- **标签**: {', '.join(article.get('tags', [])) or '无'}\n"
                    md += f"- **摘要**: {article.get('summary', '')[:200]}...\n"
                    md += f"[原文]({article['url']})\n\n---\n"
        # Ensure directory exists
        parent_dir = os.path.dirname(output_path)
        os.makedirs(parent_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"日报已生成: {output_path}")
