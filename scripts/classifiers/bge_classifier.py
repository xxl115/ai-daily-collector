import numpy as np
from typing import Dict, List

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore


class BGEClassifier:
    """BGE Embedding 智能分类器（带降级兜底）"""

    def __init__(self):
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer('BAAI/bge-m3')
            except Exception:
                self.model = None
        # 分类模板
        self.templates = {
            'breaking': ['突发新闻', '紧急快讯', '重磅消息', 'Breaking News'],
            'hot': ['热门话题', '热议', 'trending', '热搜'],
            'new': ['新品发布', '新版本', '正式上线', '发布公告'],
            'deep': ['深度分析', '技术解读', '研究论文', '原理解析']
        }
        # 标签关键词
        self.tag_keywords = {
            'LLM': ['GPT', 'Claude', 'Llama', '大模型', '语言模型'],
            'AI绘画': ['Midjourney', 'DALL-E', 'Stable Diffusion', '图像生成'],
            'Agent': ['Agent', '智能体', 'AutoGPT', '工作流'],
            '安全': ['安全漏洞', '攻击', '隐私', '风险'],
            '产品': ['发布', '上线', '版本更新', '新功能'],
            '研究': ['论文', 'arXiv', '研究', '实验'],
        }
        # 预计算 embeddings
        self.template_embs = {}
        self._precompute_embeddings()

    def _precompute_embeddings(self):
        self.template_embs = {}
        if self.model is None:
            return
        for cat, texts in self.templates.items():
            embs = self.model.encode(texts)
            self.template_embs[cat] = np.mean(embs, axis=0)

    def classify(self, text: str) -> Dict[str, object]:
        if not text:
            return {'category': 'new', 'tags': [], 'scores': {}}
        text = text[:1000]
        if self.model is None:
            return {'category': 'new', 'tags': [], 'scores': {}}
        text_emb = self.model.encode([text])
        scores: Dict[str, float] = {}
        for cat, template_emb in self.template_embs.items():
            sim = float(np.dot(text_emb, template_emb.T)[0])
            scores[cat] = sim
        category = max(scores, key=scores.get) if scores else 'new'
        if scores.get(category, 0) < 0.3:
            category = 'new'
        tags = self._extract_tags(text)
        return {'category': category, 'tags': tags[:3], 'scores': scores}

    def _extract_tags(self, text: str) -> List[str]:
        text_lower = text.lower()
        tags: List[str] = []
        for tag, keywords in self.tag_keywords.items():
            if any(kw.lower() in text_lower for kw in keywords):
                tags.append(tag)
        return tags
