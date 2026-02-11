"""
标签提取工具
从文章标题和摘要中提取标签
"""
import re
from typing import List


class TagExtractor:
    """标签提取器"""

    # 预定义标签库（按优先级排序）
    PREDEFINED_TAGS = {
        'llm': {'keywords': ['llm', '大模型', 'large language model'], 'emoji': '🤖'},
        'gpt-4': {'keywords': ['gpt-4', 'gpt4', 'gpt 4'], 'emoji': '🧠'},
        'gpt': {'keywords': ['gpt', 'chatgpt'], 'emoji': '💬'},
        'claude': {'keywords': ['claude', 'anthropic'], 'emoji': '🎯'},
        'ai绘画': {'keywords': ['ai绘画', 'image generation', 'diffusion', 'midjourney', 'stable diffusion', 'dalle'], 'emoji': '🎨'},
        'video': {'keywords': ['视频', 'video', 'movie', 'animation'], 'emoji': '🎬'},
        '研究': {'keywords': ['研究', 'research', 'paper', 'study', 'arxiv'], 'emoji': '📚'},
        '学术': {'keywords': ['学术', 'academic', '论文', 'conference'], 'emoji': '🎓'},
        '开源': {'keywords': ['开源', 'open source', 'github', 'apache', 'mit'], 'emoji': '🔓'},
        '产品': {'keywords': ['产品', 'product', 'tool', 'app', 'application'], 'emoji': '📦'},
        '产品发布': {'keywords': ['发布', 'release', 'launch', 'v6', 'v5', 'version'], 'emoji': '🚀'},
        '工具': {'keywords': ['工具', 'tool', 'framework', 'library', 'sdk', 'api'], 'emoji': '🛠️'},
        '工具评测': {'keywords': ['评测', 'review', 'comparison', 'compare', 'benchmark'], 'emoji': '📊'},
        '行业动态': {'keywords': ['动态', 'news', 'update', '趋势', 'trend'], 'emoji': '📈'},
        '多模态': {'keywords': ['多模态', 'multimodal', 'vision', 'text-to-image'], 'emoji': '👁️'},
        'agent': {'keywords': ['agent', 'mcp', 'a2a', 'workflow'], 'emoji': '🤝'},
        '安全': {'keywords': ['安全', 'security', 'vulnerability', 'attack', 'defense'], 'emoji': '🔒'},
        'google': {'keywords': ['google', 'gemini', 'bard'], 'emoji': '🔍'},
        'nvidia': {'keywords': ['nvidia', 'gpu', 'cuda', 'h100', 'a100'], 'emoji': '💻'},
        'cursor': {'keywords': ['cursor', 'ide', 'editor'], 'emoji': '⌨️'},
        'copilot': {'keywords': ['copilot', 'github copilot'], 'emoji': '✈️'},
    }

    # 需要排除的常见词
    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there',
        'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        's', 't', 'can', 'will', 'just', 'don', 'should', 'now', '的', '了', '是',
    }

    def extract(self, title: str, summary: str, source: str, max_tags: int = 5) -> List[str]:
        """
        提取标签

        Args:
            title: 文章标题
            summary: 文章摘要
            source: 来源
            max_tags: 最大标签数量

        Returns:
            标签列表
        """
        # 合并所有文本
        text = f"{title} {summary} {source}".lower()

        tags = set()
        matched_keywords = set()  # 记录已匹配的关键词

        # 1. 按优先级匹配预定义标签
        # 按标签名称长度倒序（优先匹配更具体的标签）
        sorted_tags = sorted(
            self.PREDEFINED_TAGS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for tag_key, tag_info in sorted_tags:
            for keyword in tag_info['keywords']:
                if keyword in text:
                    display_name = tag_key.upper() if tag_key.replace('-', '').isalpha() else tag_key

                    # 检查是否与已添加的标签冲突（避免重叠匹配）
                    # 例如：如果已添加 "gpt-4"，则跳过 "gpt"
                    is_duplicate = False
                    for existing in tags:
                        existing_normalized = existing.lower().replace('-', '').replace(' ', '')
                        display_normalized = display_name.lower().replace('-', '').replace(' ', '')
                        # 如果现有标签包含当前标签，跳过（如 "GPT-4" 包含 "GPT"）
                        if existing_normalized in display_normalized or \
                           display_normalized in existing_normalized:
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue

                    tags.add(display_name)
                    matched_keywords.add(keyword)
                    break

        # 2. 从文本中提取额外关键词（排除已匹配的）
        extra_keywords = self._extract_keywords(text)
        for keyword in extra_keywords[:5]:
            display_keyword = keyword.upper() if keyword.replace('-', '').isalpha() else keyword

            # 检查是否与已选标签冲突
            is_duplicate = False
            for existing in tags:
                if existing.lower() == display_keyword.lower():
                    is_duplicate = True
                    break

            if not is_duplicate and len(keyword) > 2:
                tags.add(display_keyword)

            if len(tags) >= max_tags:
                break

        # 3. 转换为列表并限制数量
        tag_list = list(tags)

        # 优先级排序
        priority_tags = ['LLM', 'GPT-4', 'AI绘画', 'CLAUDE', '开源', '产品发布', '研究', 'AGENT', 'VIDEO']
        tag_list.sort(key=lambda x: 0 if x.upper() in [t.upper() for t in priority_tags] else 1)

        return tag_list[:max_tags]

    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本
            min_length: 最小词长

        Returns:
            关键词列表
        """
        # 移除特殊字符
        cleaned = re.sub(r'[^\w\s-]', ' ', text)

        # 分词
        words = re.findall(r'\b[\w-]+\b', cleaned.lower())

        # 过滤停用词
        keywords = [word for word in words if word not in self.STOP_WORDS and len(word) >= min_length]

        # 统计词频
        word_counts = {}
        for word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1

        # 按频率排序
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # 返回前 10 个高频词
        return [word for word, count in sorted_words[:10]]

    def get_popular_tags(self, limit: int = 10) -> List[dict]:
        """
        获取热门标签列表

        Args:
            limit: 返回数量

        Returns:
            热门标签列表
        """
        tags = []
        for tag_key, tag_info in list(self.PREDEFINED_TAGS.items())[:limit]:
            tags.append({
                'id': tag_key,
                'name': tag_key.upper() if tag_key.replace('-', '').isalpha() else tag_key,
                'emoji': tag_info['emoji'],
                'keywords': tag_info['keywords']
            })

        return tags

    def search_tags(self, query: str, limit: int = 5) -> List[dict]:
        """
        搜索标签

        Args:
            query: 搜索查询
            limit: 返回数量

        Returns:
            匹配的标签列表
        """
        query = query.lower()
        results = []

        for tag_key, tag_info in self.PREDEFINED_TAGS.items():
            # 搜索标签名称
            if query in tag_key:
                results.append({
                    'id': tag_key,
                    'name': tag_key.upper() if tag_key.replace('-', '').isalpha() else tag_key,
                    'emoji': tag_info['emoji']
                })
                continue

            # 搜索关键词
            for keyword in tag_info['keywords']:
                if query in keyword:
                    results.append({
                        'id': tag_key,
                        'name': tag_key.upper() if tag_key.replace('-', '').isalpha() else tag_key,
                        'emoji': tag_info['emoji']
                    })
                    break

        return results[:limit]
