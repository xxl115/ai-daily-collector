"""
分类推断工具
根据文章内容推断文章分类（hot/deep/new/breaking）
"""
import re
from typing import Optional
from ..models import ArticleCategory


class CategoryClassifier:
    """文章分类器"""

    # 关键词映射到分类
    KEYWORD_RULES = {
        ArticleCategory.hot: {
            'keywords': [
                'openai', 'anthropic', 'google', 'nvidia', 'microsoft',
                'gpt', 'claude', 'gemini', 'llm', '大模型',
                '发布', '发布版', '预览版', 'beta', 'alpha',
                'agent', 'mcp', 'workflow', 'autogen', 'a2a',
            ],
            'sources': ['openai', 'google', 'anthropic', 'nvidia'],
            'priority': 1
        },
        ArticleCategory.breaking: {
            'keywords': [
                '突破', '重大', '首次', '发布', '发布版',
                '超越', '击败', '新纪录', '里程碑',
                'security', 'vulnerability', 'deepfake', '攻击',
                'image', 'video', 'audio', '生成', '合成',
            ],
            'sources': ['techcrunch', 'wired', 'the verge'],
            'priority': 2
        },
        ArticleCategory.new: {
            'keywords': [
                'v6', 'v7', 'v8', 'v5', 'v4',
                'version', '新版', '升级', '更新',
                'cursor', 'windsurf', 'copilot', 'ide',
                'product', 'hunt', 'launch', '发布',
            ],
            'sources': ['product-hunt'],
            'priority': 3
        },
        ArticleCategory.deep: {
            'keywords': [
                '研究', '论文', 'arxiv', '分析',
                '评估', '基准', 'benchmark', '实验',
                '方法', '算法', 'framework', 'sdk',
                'langchain', 'openclaw', '工具',
            ],
            'sources': ['arxiv', 'mit', 'wired'],
            'priority': 4
        }
    }

    # 特殊规则（优先级最高）
    SPECIAL_RULES = [
        # OpenAI 发布 → hot（优先级最高）
        (
            lambda title, summary, source: (
                'openai' in source.lower() and
                ('发布' in title or 'release' in title.lower() or
                 'preview' in title.lower() or 'beta' in title.lower() or
                 'alpha' in title.lower())
            ),
            ArticleCategory.hot
        ),
        # ArXiv 论文 → deep
        (
            lambda title, summary, source: 'arxiv' in source.lower(),
            ArticleCategory.deep
        ),
        # 产品版本发布（v6, v7, v8等）→ new
        (
            lambda title, summary, source: bool(re.search(r'\bv[6-9]\b', title.lower())) or
                                         bool(re.search(r'\bv\d+\.\d+\b', title.lower())),
            ArticleCategory.new
        ),
        # Product Hunt → new
        (
            lambda title, summary, source: 'product-hunt' in source.lower(),
            ArticleCategory.new
        ),
        # 突发新闻（breaking）→ breaking
        (
            lambda title, summary, source: (
                'breaking' in title.lower() or
                '重大突破' in title or '首次' in title or
                '新纪录' in title or '里程碑' in title
            ),
            ArticleCategory.breaking
        ),
        # 深度研究（论文、研究）→ deep
        (
            lambda title, summary, source: (
                '研究' in title or '论文' in title or
                'study' in title.lower() or 'paper' in title.lower()
            ),
            ArticleCategory.deep
        ),
    ]

    def classify(self, title: str, summary: str, source: str) -> ArticleCategory:
        """
        推断文章分类

        Args:
            title: 文章标题
            summary: 文章摘要
            source: 文章来源

        Returns:
            推断的分类
        """
        # 合并所有文本
        text = f"{title} {summary} {source}".lower()

        # 1. 优先检查特殊规则
        for rule, category in self.SPECIAL_RULES:
            if rule(title, summary, source):
                return category

        # 2. 基于关键词匹配
        scores = {}
        for category, rules in self.KEYWORD_RULES.items():
            score = 0

            # 关键词匹配
            for keyword in rules['keywords']:
                if keyword in text:
                    score += 1

            # 来源匹配
            if any(s in source.lower() for s in rules['sources']):
                score += 2

            # 优先级加权
            score += (5 - rules['priority'])  # 优先级越高（1），加分越多

            if score > 0:
                scores[category] = score

        # 返回得分最高的分类
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        # 默认分类
        return ArticleCategory.hot

    def classify_batch(self, items: list) -> list:
        """
        批量推断分类

        Args:
            items: 包含 title, summary, source 的字典列表

        Returns:
            分类列表
        """
        return [
            self.classify(
                item.get('title', ''),
                item.get('summary', ''),
                item.get('source', '')
            )
            for item in items
        ]

    def get_category_info(self, category: ArticleCategory) -> dict:
        """
        获取分类信息

        Args:
            category: 分类

        Returns:
            分类信息字典
        """
        info_map = {
            ArticleCategory.hot: {
                'id': 'hot',
                'name': '热门',
                'emoji': '🔥',
                'description': '高热度内容',
                'color': '#FF6154'
            },
            ArticleCategory.deep: {
                'id': 'deep',
                'name': '深度',
                'emoji': '📰',
                'description': '深度研究内容',
                'color': '#42A5F5'
            },
            ArticleCategory.new: {
                'id': 'new',
                'name': '新品',
                'emoji': '🆕',
                'description': '最新发布内容',
                'color': '#10B981'
            },
            ArticleCategory.breaking: {
                'id': 'breaking',
                'name': '突发',
                'emoji': '⚡',
                'description': '突发新闻',
                'color': '#F59E0B'
            }
        }

        return info_map.get(category, {})
