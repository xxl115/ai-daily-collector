# -*- coding: utf-8 -*-
"""
关键词过滤模块

参考 TrendRadar 的 frequency_words.txt 设计:
- 必须词 (+开头): 必须全部匹配
- 普通词: 任意匹配
- 过滤词 (-/!开头): 排除匹配
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class WordGroup:
    """词组配置"""
    name: str  # 分组名称
    required: List[str] = field(default_factory=list)  # 必须词
    normal: List[str] = field(default_factory=list)  # 普通词
    filter: List[str] = field(default_factory=list)  # 过滤词
    
    def matches(self, text: str) -> bool:
        """检查文本是否匹配此词组"""
        text_lower = text.lower()
        
        # 过滤词检查 - 任何过滤词匹配就排除
        for word in self.filter:
            if word.lower() in text_lower:
                return False
        
        # 必须词检查 - 所有必须词都必须匹配
        for word in self.required:
            if word.lower() not in text_lower:
                return False
        
        # 普通词检查 - 至少一个普通词匹配
        if self.normal:
            for word in self.normal:
                if word.lower() in text_lower:
                    return True
            return False
        
        # 没有普通词时，只要有必须词匹配即可
        return True


class KeywordFilter:
    """关键词过滤器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化过滤器
        
        Args:
            config_path: 配置文件路径 (frequency_words.txt)
        """
        self.groups: List[WordGroup] = []
        self.all_filter_words: Set[str] = set()
        self._load_config(config_path)
    
    def _load_config(self, config_path: str = None):
        """加载配置文件"""
        if config_path is None:
            config_path = os.environ.get(
                "KEYWORD_FILTER_PATH",
                "config/frequency_words.txt"
            )
        
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"关键词配置文件不存在: {config_path}")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 按空行分割多个词组
            blocks = content.split("\n\n")
            
            for block in blocks:
                if not block.strip():
                    continue
                
                lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
                if not lines:
                    continue
                
                # 第一行是分组名称
                group_name = lines[0].replace("#", "").strip()
                
                required = []
                normal = []
                filter_words = []
                
                for line in lines[1:]:
                    if line.startswith("+"):
                        # 必须词
                        required.append(line[1:].strip())
                    elif line.startswith("!") or line.startswith("-"):
                        # 过滤词
                        word = line[1:].strip()
                        filter_words.append(word)
                        self.all_filter_words.add(word.lower())
                    else:
                        # 普通词
                        normal.append(line)
                
                if required or normal or filter_words:
                    self.groups.append(WordGroup(
                        name=group_name,
                        required=required,
                        normal=normal,
                        filter=filter_words,
                    ))
            
            logger.info(f"加载关键词配置: {len(self.groups)} 个词组, {len(self.all_filter_words)} 个过滤词")
            
        except Exception as e:
            logger.error(f"加载关键词配置失败: {e}")
    
    def matches_any_group(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        检查文本是否匹配任意词组
        
        Returns:
            (是否匹配, 匹配的分组名称)
        """
        for group in self.groups:
            if group.matches(text):
                return True, group.name
        return False, None
    
    def should_filter(self, text: str) -> bool:
        """检查文本是否应该被过滤"""
        # 如果没有配置词组，不过滤任何内容
        if not self.groups:
            return False
        
        matches, _ = self.matches_any_group(text)
        return not matches
    
    def filter_articles(
        self,
        articles: List[Dict],
        title_field: str = "title",
        require_all: bool = False,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        过滤文章列表
        
        Args:
            articles: 文章列表
            title_field: 标题字段名
            require_all: 是否所有词组都必须匹配 (False=任一词组匹配即可)
        
        Returns:
            (匹配的文章, 被过滤的文章)
        """
        matched = []
        filtered = []
        
        for article in articles:
            title = article.get(title_field, "")
            if not title:
                # 没有标题的文章默认保留
                matched.append(article)
                continue
            
            # 检查是否匹配任意词组
            matches, group_name = self.matches_any_group(title)
            
            if matches:
                article["_matched_group"] = group_name
                matched.append(article)
            else:
                filtered.append(article)
        
        return matched, filtered
    
    def calculate_weight(
        self,
        title: str,
        rank: int = 99,
        count: int = 1,
        rank_threshold: int = 5,
        rank_weight: float = 0.6,
        frequency_weight: float = 0.3,
        hotness_weight: float = 0.1,
    ) -> float:
        """
        计算新闻权重 (参考 TrendRadar 算法)
        
        Args:
            title: 新闻标题
            rank: 当前排名
            count: 出现次数
            rank_threshold: 高排名阈值
            rank_weight: 排名权重
            frequency_weight: 频次权重
            hotness_weight: 热度权重
        
        Returns:
            权重值
        """
        # 排名得分: 11 - min(rank, 10)
        rank_score = 11 - min(rank, 10)
        rank_contrib = rank_score * rank_weight
        
        # 频次得分: min(count, 10) * 10
        frequency_score = min(count, 10) * 10
        frequency_contrib = frequency_score * frequency_weight
        
        # 热度得分: 进入前 threshold 的比例 * 100
        high_rank_count = 1 if rank <= rank_threshold else 0
        hotness_ratio = high_rank_count
        hotness_contrib = hotness_ratio * 100 * hotness_weight
        
        return rank_contrib + frequency_contrib + hotness_contrib
    
    def sort_by_weight(
        self,
        articles: List[Dict],
        rank_field: str = "rank",
        count_field: str = "count",
        **kwargs,
    ) -> List[Dict]:
        """
        按权重排序文章
        
        Args:
            articles: 文章列表
            rank_field: 排名字段名
            count_field: 出现次数字段名
            **kwargs: calculate_weight 的其他参数
        """
        for article in articles:
            rank = article.get(rank_field, 99)
            count = article.get(count_field, 1)
            title = article.get("title", "")
            article["_weight"] = self.calculate_weight(
                title, rank, count, **kwargs
            )
        
        return sorted(
            articles,
            key=lambda x: (
                -x.get("_weight", 0),
                x.get(rank_field, 999),
                -x.get(count_field, 0),
            ),
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "group_count": len(self.groups),
            "filter_word_count": len(self.all_filter_words),
            "groups": [
                {
                    "name": g.name,
                    "required_count": len(g.required),
                    "normal_count": len(g.normal),
                    "filter_count": len(g.filter),
                }
                for g in self.groups
            ],
        }


# 全局过滤器实例
keyword_filter = KeywordFilter()


def filter_articles(
    articles: List[Dict],
    title_field: str = "title",
) -> Tuple[List[Dict], List[Dict]]:
    """过滤文章"""
    return keyword_filter.filter_articles(articles, title_field)


def sort_by_hotness(
    articles: List[Dict],
    rank_field: str = "rank",
    count_field: str = "count",
) -> List[Dict]:
    """按热度排序"""
    return keyword_filter.sort_by_weight(
        articles,
        rank_field=rank_field,
        count_field=count_field,
    )


# 导入 logger
from .logger import get_logger
logger = get_logger(__name__)
