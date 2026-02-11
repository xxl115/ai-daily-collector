"""
文章数据转换工具
将原始 Markdown 文章数据转换为前端需要的 Article 模型
"""
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..models import ArticleModel, ArticleCategory
from .category_classifier import CategoryClassifier
from .tag_extractor import TagExtractor


class ArticleTransformer:
    """文章数据转换器"""

    def __init__(self):
        self.category_classifier = CategoryClassifier()
        self.tag_extractor = TagExtractor()

    def transform_from_file(self, filepath: Path) -> Optional[ArticleModel]:
        """
        从文章文件转换为 ArticleModel

        Args:
            filepath: Markdown 文件路径

        Returns:
            ArticleModel 或 None（解析失败）
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            # 解析 YAML frontmatter
            metadata = self._parse_frontmatter(content)

            # 提取内容
            summary_match = re.search(r'## 中文总结\s*\n(.+?)(?:\n---|\Z)', content, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else ""

            # 生成 ID
            article_id = self._generate_id(
                metadata.get('source', 'unknown'),
                metadata.get('title', filepath.stem)
            )

            # 推断分类
            title = metadata.get('title', '')
            source = metadata.get('source', '')
            category = self.category_classifier.classify(title, summary, source)

            # 提取标签
            tags = self.tag_extractor.extract(title, summary, source)

            # 生成浏览数和评论数
            view_count, comment_count = self._generate_engagement_counts(category)

            # 处理发布时间
            published_at = metadata.get('date', datetime.now().strftime('%Y-%m-%d'))
            if isinstance(published_at, str):
                published_at = f"{published_at}T00:00:00Z"
            else:
                published_at = datetime.now().isoformat() + "Z"

            # 构建数据
            return ArticleModel(
                id=article_id,
                title=title or filepath.stem,
                summary=summary,
                category=category,
                source=self._normalize_source(source),
                publishedAt=published_at,
                viewCount=view_count,
                commentCount=comment_count,
                tags=tags,
                url=metadata.get('original_url'),
            )
        except Exception as e:
            print(f"Error transforming file {filepath}: {e}")
            return None

    def transform_from_dict(self, article_dict: Dict) -> Optional[ArticleModel]:
        """
        从字典转换为 ArticleModel

        Args:
            article_dict: 原始文章数据字典

        Returns:
            ArticleModel 或 None
        """
        try:
            title = article_dict.get('title', '')
            summary = article_dict.get('summary', '')
            source = article_dict.get('source', '')

            # 生成 ID
            article_id = self._generate_id(source, title)

            # 推断分类
            category = self.category_classifier.classify(title, summary, source)

            # 提取标签
            tags = self.tag_extractor.extract(title, summary, source)

            # 生成浏览数和评论数
            view_count, comment_count = self._generate_engagement_counts(category)

            # 处理发布时间
            published_at = article_dict.get('date', datetime.now().strftime('%Y-%m-%d'))
            if isinstance(published_at, str):
                if 'T' not in published_at:
                    published_at = f"{published_at}T00:00:00Z"
            else:
                published_at = datetime.now().isoformat() + "Z"

            return ArticleModel(
                id=article_id,
                title=title,
                summary=summary,
                category=category,
                source=self._normalize_source(source),
                publishedAt=published_at,
                viewCount=view_count,
                commentCount=comment_count,
                tags=tags,
                url=article_dict.get('url') or article_dict.get('original_url'),
            )
        except Exception as e:
            print(f"Error transforming dict: {e}")
            return None

    def batch_transform(self, filepaths: List[Path]) -> List[ArticleModel]:
        """
        批量转换文章文件

        Args:
            filepaths: Markdown 文件路径列表

        Returns:
            ArticleModel 列表
        """
        articles = []
        for filepath in filepaths:
            article = self.transform_from_file(filepath)
            if article:
                articles.append(article)
        return articles

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """
        解析 YAML frontmatter

        Args:
            content: Markdown 内容

        Returns:
            元数据字典
        """
        metadata = {}
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # 简单的键值对解析
            for line in frontmatter.split('\n'):
                match = re.match(r'^(\w+):\s*"?(.+?)"?$', line)
                if match:
                    key, value = match.groups()
                    metadata[key] = value.strip('"')

        return metadata

    def _generate_id(self, source: str, title: str) -> str:
        """
        生成文章 ID

        使用 MD5 hash 生成唯一 ID

        Args:
            source: 来源
            title: 标题

        Returns:
            文章 ID（如 "openai-a1b2c3d4"）
        """
        hash_str = hashlib.md5(f"{source}:{title}".encode()).hexdigest()[:8]
        normalized_source = source.lower().replace(' ', '-').replace('_', '-')
        return f"{normalized_source}-{hash_str}"

    def _normalize_source(self, source: str) -> str:
        """
        标准化来源名称

        将各种来源名称统一为标准格式

        Args:
            source: 原始来源名称

        Returns:
            标准化后的来源
        """
        source_lower = source.lower().strip()

        # 来源映射表
        source_mapping = {
            'openai': 'openai',
            'google ai': 'google',
            'google': 'google',
            'anthropic': 'anthropic',
            'mit tech review': 'mit',
            'mit': 'mit',
            'wired': 'wired',
            'the verge': 'verge',
            'verge': 'verge',
            'techcrunch': 'techcrunch',
            'product hunt': 'product-hunt',
            'arxiv ai': 'arxiv',
            'arxiv': 'arxiv',
        }

        # 尝试精确匹配
        if source_lower in source_mapping:
            return source_mapping[source_lower]

        # 尝试模糊匹配
        for key, value in source_mapping.items():
            if key in source_lower:
                return value

        # 返回原值的规范化版本
        return source_lower.replace(' ', '-').replace('_', '-')

    def _generate_engagement_counts(self, category: ArticleCategory) -> Tuple[int, int]:
        """
        生成浏览数和评论数

        基于分类生成合理的模拟数据

        Args:
            category: 文章分类

        Returns:
            (viewCount, commentCount)
        """
        import random

        # 基础范围（根据分类）
        ranges = {
            ArticleCategory.hot: (2000, 5000),      # 热门内容
            ArticleCategory.breaking: (3000, 8000),  # 突发新闻
            ArticleCategory.new: (1000, 3000),       # 新品发布
            ArticleCategory.deep: (500, 2000),       # 深度内容
        }

        min_view, max_view = ranges.get(category, (500, 2000))
        view_count = random.randint(min_view, max_view)
        comment_count = int(view_count * random.uniform(0.02, 0.1))  # 2%-10% 的评论率

        return view_count, comment_count
