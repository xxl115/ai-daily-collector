# -*- coding: utf-8 -*-
"""
日报统计模块

功能:
- 自动生成日报统计
- 数据源分布分析
- 关键词提取和趋势
- 可视化图表生成
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class DailyStatsAnalyzer:
    """日报统计分析器"""
    
    def __init__(self, daily_dir: str = "ai/daily"):
        """
        初始化
        
        Args:
            daily_dir: 日报目录
        """
        self.daily_dir = Path(daily_dir)
        self.cache_dir = Path(".cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_daily_report(self, date: str = None) -> Optional[Dict]:
        """
        加载日报
        
        Args:
            date: 日期，格式 YYYY-MM-DD，默认今天
        
        Returns:
            日报数据
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        file_path = self.daily_dir / f"ai-hotspot-{date}.md"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "date": date,
            "content": content,
            "file_path": str(file_path),
        }
    
    def parse_sections(self, content: str) -> List[Dict]:
        """
        解析日报 sections
        
        Args:
            content: 日报内容
        
        Returns:
            Section 列表
        """
        sections = []
        
        # 匹配 ## 开头的章节
        pattern = r"##\s*(\d+️⃣)?\s*(.+?)\n(.*?)(?=##\s|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for num, title, body in matches:
            # 提取文章列表
            articles = self._parse_articles(body)
            
            sections.append({
                "title": title.strip(),
                "articles": articles,
                "article_count": len(articles),
            })
        
        return sections
    
    def _parse_articles(self, body: str) -> List[Dict]:
        """解析文章列表"""
        articles = []
        
        # 匹配 ### 开头的文章
        pattern = r"###\s+(.+?)\n.*?来源:\s*(\S+).*?总结:\s*(.+?)(?=###|---|\Z)"
        matches = re.findall(pattern, body, re.DOTALL)
        
        for title, source, summary in matches:
            # 提取链接
            link_match = re.search(r"\[链接\]\((.+?)\)", body)
            link = link_match.group(1) if link_match else ""
            
            articles.append({
                "title": title.strip()[:200],
                "source": source,
                "summary": summary.strip()[:500],
                "link": link,
            })
        
        return articles
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        提取关键词
        
        Args:
            text: 文本
            top_n: 返回数量
        
        Returns:
            关键词列表 (词, 频率)
        """
        # 停用词
        stopwords = {
            "的", "是", "在", "和", "与", "或", "等", "了", "为", "于",
            "the", "a", "an", "is", "are", "was", "were", "and", "or",
            "to", "of", "in", "on", "for", "with", "by", "from",
            "ai", "an", "this", "that", "it", "be", "as", "at",
        }
        
        # 提取词
        words = re.findall(r"[一-龥]{2,}|[a-zA-Z]{3,}", text.lower())
        
        # 过滤停用词
        words = [w for w in words if w not in stopwords and len(w) < 20]
        
        # 统计
        counter = Counter(words)
        return counter.most_common(top_n)
    
    def analyze_source_distribution(self, sections: List[Dict]) -> Dict:
        """
        分析数据源分布
        
        Returns:
            源分布统计
        """
        sources = []
        
        for section in sections:
            for article in section["articles"]:
                sources.append(article["source"])
        
        counter = Counter(sources)
        total = sum(counter.values())
        
        return {
            "sources": [
                {
                    "name": source,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for source, count in counter.most_common()
            ],
            "total": total,
            "unique_sources": len(counter),
        }
    
    def analyze_trends(self, days: int = 7) -> Dict:
        """
        分析趋势（最近 N 天）
        
        Args:
            days: 天数
        
        Returns:
            趋势数据
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        stats = []
        keywords = []
        
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            report = self.load_daily_report(date)
            
            if report:
                sections = self.parse_sections(report["content"])
                
                # 文章数
                total_articles = sum(len(s["articles"]) for s in sections)
                stats.append({
                    "date": date,
                    "articles": total_articles,
                    "sections": len(sections),
                })
                
                # 关键词
                daily_keywords = self.extract_keywords(report["content"], 10)
                for word, count in daily_keywords:
                    keywords.append((word, date, count))
        
        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            "daily_stats": stats,
            "keyword_trends": self._aggregate_keyword_trends(keywords),
        }
    
    def _aggregate_keyword_trends(
        self,
        keywords: List[Tuple[str, str, int]],
    ) -> Dict[str, List[Dict]]:
        """聚合关键词趋势"""
        trends = {}
        
        for word, date, count in keywords:
            if word not in trends:
                trends[word] = []
            trends[word].append({
                "date": date,
                "count": count,
            })
        
        # 返回出现频率高的词
        frequent = sorted(trends.keys(), key=lambda x: sum(
            d["count"] for d in trends[x]
        ), reverse=True)[:20]
        
        return {
            word: trends[word] for word in frequent
        }
    
    def generate_summary(self, report: Dict) -> Dict:
        """
        生成统计摘要
        
        Args:
            report: 日报数据
        
        Returns:
            统计摘要
        """
        sections = self.parse_sections(report["content"])
        
        # 基础统计
        total_articles = sum(len(s["articles"]) for s in sections)
        
        # 关键词
        keywords = self.extract_keywords(report["content"], 20)
        
        # 数据源
        source_dist = self.analyze_source_distribution(sections)
        
        # 分类统计
        category_stats = [
            {
                "category": s["title"],
                "count": s["article_count"],
                "percentage": round(s["article_count"] / total_articles * 100, 1),
            }
            for s in sections
        ]
        
        return {
            "date": report["date"],
            "total_articles": total_articles,
            "total_sections": len(sections),
            "categories": category_stats,
            "sources": source_dist["sources"],
            "keywords": [{"word": w, "count": c} for w, c in keywords],
            "generated_at": datetime.now().isoformat(),
        }
    
    def generate_markdown_report(self, report: Dict) -> str:
        """
        生成 Markdown 统计报告
        
        Args:
            report: 日报数据
        
        Returns:
            Markdown 格式统计报告
        """
        summary = self.generate_summary(report)
        
        lines = [
            "---",
            "title: AI 日报统计",
            f"date: {summary['date']}",
            "tags: [统计, 日报, 分析]",
            "---",
            "",
            f"# 📊 AI 日报统计 {summary['date']}",
            "",
            "> 自动生成统计报告",
            "",
            "---",
            "",
            "## 1️⃣ 基础统计",
            "",
            f"- **文章总数**: {summary['total_articles']} 篇",
            f"- **分类数**: {summary['total_sections']} 个",
            f"- **数据源**: {summary['sources'][0]['name']} 为主 ({summary['sources'][0]['percentage']}%)",
            f"- **独立来源**: {summary['sources'][-1]['name']} 等 {len(summary['sources'])} 个",
            "",
            "## 2️⃣ 分类分布",
            "",
            "| 分类 | 文章数 | 占比 |",
            "|------|--------|------|",
        ]
        
        for cat in summary["categories"]:
            lines.append(f"| {cat['category']} | {cat['count']} | {cat['percentage']}% |")
        
        lines.extend([
            "",
            "## 3️⃣ 数据源分布",
            "",
            "| 来源 | 数量 | 占比 |",
            "|------|------|------|",
        ])
        
        for source in summary["sources"]:
            lines.append(f"| {source['name']} | {source['count']} | {source['percentage']}% |")
        
        lines.extend([
            "",
            "## 4️⃣ 热门关键词",
            "",
            "```",
        ])
        
        for kw in summary["keywords"][:15]:
            lines.append(f"  {kw['word']}: {kw['count']}")
        
        lines.extend([
            "```",
            "",
            f"_统计生成时间: {summary['generated_at']}_",
        ])
        
        return "\n".join(lines)
    
    def save_stats_report(self, date: str = None) -> str:
        """
        保存统计报告
        
        Args:
            date: 日期
        
        Returns:
            保存路径
        """
        report = self.load_daily_report(date)
        if not report:
            return None
        
        md_report = self.generate_markdown_report(report)
        
        stats_path = self.daily_dir / f"stats-{report['date']}.md"
        with open(stats_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        return str(stats_path)


def analyze_daily_stats(date: str = None) -> Dict:
    """
    快速分析日报统计
    
    Usage:
        stats = analyze_daily_stats("2026-02-03")
        print(stats['total_articles'])
        print(stats['keywords'])
    """
    analyzer = DailyStatsAnalyzer()
    report = analyzer.load_daily_report(date)
    
    if not report:
        return {"error": f"未找到 {date} 的日报"}
    
    return analyzer.generate_summary(report)


def generate_stats_markdown(date: str = None) -> str:
    """
    生成 Markdown 统计报告
    
    Usage:
        md = generate_stats_markdown("2026-02-03")
        print(md)
    """
    analyzer = DailyStatsAnalyzer()
    report = analyzer.load_daily_report(date)
    
    if not report:
        return f"# 未找到 {date} 的日报"
    
    return analyzer.generate_markdown_report(report)


if __name__ == "__main__":
    # 示例
    print("=== AI 日报统计 ===")
    
    # 分析今天
    stats = analyze_daily_stats()
    if "error" in stats:
        print(stats["error"])
    else:
        print(f"日期: {stats['date']}")
        print(f"文章数: {stats['total_articles']}")
        print(f"分类: {stats['total_sections']}")
        print()
        print("分类分布:")
        for cat in stats["categories"]:
            print(f"  {cat['category']}: {cat['count']} ({cat['percentage']}%)")
        print()
        print("数据源:")
        for source in stats["sources"][:5]:
            print(f"  {source['name']}: {source['count']} ({source['percentage']}%)")
        print()
        print("关键词:")
        for kw in stats["keywords"][:10]:
            print(f"  {kw['word']}: {kw['count']}")
