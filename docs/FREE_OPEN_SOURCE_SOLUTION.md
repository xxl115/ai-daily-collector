# 免费开源内容处理方案

## 方案概述

完全免费的开源方案，无需调用付费 API：
- ✅ 内容抓取：开源库
- ✅ 内容清洗：开源工具
- ✅ 文本摘要：本地 LLM (Ollama) 或开源算法
- ✅ 智能分类：规则 + 关键词 + 免费 Embedding
- ✅ 存储：D1 免费额度

**预计成本：0 元**

---

## 1. 内容抓取（免费）

### 技术选型

| 工具 | 用途 | 优点 |
|------|------|------|
| `newspaper3k` | 新闻文章提取 | 专门针对新闻优化，自动提取标题、作者、正文、图片 |
| `trafilatura` | 通用网页正文提取 | 准确率高，速度快，支持多语言 |
| `readability-lxml` | 类似浏览器阅读模式 | 提取主要内容，去除广告 |

### 推荐方案：newspaper3k + trafilatura 组合

```python
# ingestor/content_fetcher.py

import requests
from newspaper import Article
import trafilatura
from typing import Optional
import time

class FreeContentFetcher:
    """免费内容抓取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_content(self, url: str) -> Optional[dict]:
        """
        抓取网页内容，返回结构化数据
        
        Returns:
            {
                'title': str,
                'content': str,
                'summary': str,
                'authors': list,
                'publish_date': str,
                'top_image': str
            }
        """
        try:
            # 方案1: 使用 newspaper3k（适合新闻网站）
            article = Article(url, language='zh')
            article.download()
            article.parse()
            article.nlp()  # 自动提取关键词和摘要
            
            if article.text and len(article.text) > 200:
                return {
                    'title': article.title or '',
                    'content': article.text,
                    'summary': article.summary or article.text[:300],
                    'authors': article.authors or [],
                    'publish_date': str(article.publish_date) if article.publish_date else '',
                    'top_image': article.top_image or '',
                    'keywords': article.keywords or []
                }
        except Exception as e:
            print(f"newspaper3k failed: {e}")
        
        # 方案2: 使用 trafilatura（通用网页）
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, 
                                              include_comments=False,
                                              include_tables=False,
                                              deduplicate=True,
                                              target_language="zh")
                if content and len(content) > 200:
                    return {
                        'title': '',  # 需要另外提取
                        'content': content,
                        'summary': content[:300],
                        'authors': [],
                        'publish_date': '',
                        'top_image': '',
                        'keywords': []
                    }
        except Exception as e:
            print(f"trafilatura failed: {e}")
        
        return None
    
    def batch_fetch(self, urls: list, delay: float = 1.0) -> list:
        """批量抓取，带延迟防止被封"""
        results = []
        for url in urls:
            result = self.fetch_content(url)
            if result:
                results.append(result)
            time.sleep(delay)  # 礼貌爬取
        return results
```

### 安装依赖

```bash
pip install newspaper3k trafilatura readability-lxml
python -m nltk.downloader punkt  # newspaper3k 需要
```

---

## 2. 文本摘要（免费）

### 方案 A: 基于 TextRank 的抽取式摘要（完全免费）

不需要 AI，用算法从文章中提取关键句子。

```python
# ingestor/summarizer.py

import re
from collections import Counter
import math
from typing import List

class TextRankSummarizer:
    """基于 TextRank 的免费摘要生成"""
    
    def __init__(self):
        self.stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 中文分句
        sentences = re.split('[。！？\n]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _split_words(self, text: str) -> List[str]:
        """分词 - 简单实现"""
        # 使用 jieba 或简单字符分割
        import jieba
        words = jieba.cut(text)
        return [w for w in words if len(w) > 1 and w not in self.stopwords]
    
    def _sentence_similarity(self, sent1: str, sent2: str) -> float:
        """计算句子相似度"""
        words1 = set(self._split_words(sent1))
        words2 = set(self._split_words(sent2))
        
        if not words1 or not words2:
            return 0
        
        intersection = words1 & words2
        return len(intersection) / (math.log(len(words1)) + math.log(len(words2)) + 1)
    
    def summarize(self, text: str, num_sentences: int = 3) -> str:
        """生成摘要"""
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return '。'.join(sentences) + '。'
        
        # 构建相似度矩阵
        n = len(sentences)
        sim_matrix = [[0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    sim_matrix[i][j] = self._sentence_similarity(sentences[i], sentences[j])
        
        # 计算句子得分（简单版 PageRank）
        scores = [1.0] * n
        damping = 0.85
        iterations = 30
        
        for _ in range(iterations):
            new_scores = [0.0] * n
            for i in range(n):
                for j in range(n):
                    if i != j and sim_matrix[j][i] > 0:
                        new_scores[i] += sim_matrix[j][i] * scores[j]
                new_scores[i] = (1 - damping) + damping * new_scores[i]
            scores = new_scores
        
        # 选择得分最高的句子
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        selected_indices = sorted([idx for idx, _ in ranked[:num_sentences]])
        
        summary = '。'.join([sentences[i] for i in selected_indices])
        return summary + '。'

# 使用示例
summarizer = TextRankSummarizer()
summary = summarizer.summarize(long_article_text, num_sentences=2)
```

### 安装依赖

```bash
pip install jieba
```

### 方案 B: 本地 LLM (Ollama)

如果有服务器资源，可以本地运行小模型。

```bash
# 安装 Ollama
ollama pull llama2-chinese:7b  # 中文模型
ollama pull qwen:7b  # 阿里通义千问
```

```python
import requests

class LocalLLMProcessor:
    """本地 Ollama LLM"""
    
    def __init__(self, model: str = "qwen:7b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
    
    def summarize(self, text: str) -> str:
        """本地模型生成摘要"""
        prompt = f"请用50字概括以下内容：\n{text[:1000]}"
        
        response = requests.post(f"{self.host}/api/generate", json={
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return response.json().get('response', '')
    
    def classify(self, title: str, content: str) -> dict:
        """本地模型分类"""
        prompt = f"分类以下文章（hot/deep/new/breaking），只输出分类词：\n标题：{title}\n内容：{content[:500]}"
        
        response = requests.post(f"{self.host}/api/generate", json={
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        category = response.json().get('response', '').strip().lower()
        return {"category": category, "tags": []}
```

---

## 3. 智能分类（免费）

### 方案 A: 规则 + 关键词（完全免费）

```python
# ingestor/classifier.py

import re
from typing import List, Dict

class RuleClassifier:
    """基于规则的免费分类器"""
    
    # 分类规则
    CATEGORIES = {
        'breaking': {
            'keywords': ['突发', '紧急', '刚刚', '重磅', '震惊', '紧急发布', '快讯', 'Breaking'],
            'weight': 10
        },
        'hot': {
            'keywords': ['热门', '热议', '火了', '爆火', '刷屏', '热搜', ' trending', 'viral'],
            'weight': 8
        },
        'new': {
            'keywords': ['发布', '新品', '推出', '上线', '问世', '亮相', '官宣', '登场', '发布'],
            'weight': 6
        },
        'deep': {
            'keywords': ['研究', '论文', '深度', '分析', '解读', '综述', '技术细节', '原理', '方法论'],
            'weight': 5
        }
    }
    
    # 标签规则
    TAGS = {
        'AI绘画': ['midjourney', 'dalle', 'stable diffusion', '绘画', '生图', '图像生成', 'ai art', '生成图片'],
        'LLM': ['gpt', 'llama', 'claude', '大模型', '语言模型', 'chatgpt', 'bert', 'transformer'],
        '产品发布': ['发布', '新品', '推出', '上线', 'v1.', 'v2.', '版本更新', '正式版'],
        '研究': ['论文', 'arxiv', 'research', '研究', 'novel', 'method', 'approach', '实验'],
        '工具': ['工具', 'plugin', '插件', '扩展', 'cursor', 'ide', 'vscode', '开源'],
        '安全': ['安全', '风险', '漏洞', '隐私', '攻击', '防护', 'hack', 'security'],
        '商业': ['融资', '收购', '财报', '市场', '商业', '投资', '估值', 'ipo', 'startup'],
        '伦理': ['伦理', '监管', '政策', '法律', '版权', 'ai法案', '治理'],
        '硬件': ['芯片', 'gpu', 'tpu', 'nvidia', 'apple silicon', '推理芯片']
    }
    
    def classify(self, title: str, content: str) -> Dict:
        """分类文章"""
        text = (title + ' ' + content).lower()
        
        # 计算每个分类的得分
        scores = {}
        for cat, config in self.CATEGORIES.items():
            score = 0
            for keyword in config['keywords']:
                count = len(re.findall(keyword.lower(), text))
                score += count * config['weight']
            scores[cat] = score
        
        # 选择得分最高的分类
        if max(scores.values()) > 0:
            category = max(scores, key=scores.get)
        else:
            category = 'new'  # 默认分类
        
        # 提取标签
        tags = []
        for tag, keywords in self.TAGS.items():
            if any(kw.lower() in text for kw in keywords):
                tags.append(tag)
        
        return {
            'category': category,
            'tags': tags[:3]  # 最多3个标签
        }
```

### 方案 B: 免费 Embedding + 相似度（需要一点计算资源）

使用开源的 sentence-transformers 生成 embedding，然后与预定义的分类模板比较相似度。

```python
# 需要安装：pip install sentence-transformers

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingClassifier:
    """基于免费 Embedding 的分类"""
    
    def __init__(self):
        # 下载免费的开源模型（首次下载约 100MB）
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 预定义分类模板
        self.templates = {
            'breaking': ['突发新闻', '紧急消息', '快讯', '重大事件'],
            'hot': ['热门话题', ' trending', '热搜', '大家都在讨论'],
            'new': ['新产品发布', '新品上市', '新版本', '正式上线'],
            'deep': ['深度研究报告', '技术分析', '原理解析', '综述']
        }
        
        # 预计算模板 embedding
        self.template_embeddings = {}
        for cat, texts in self.templates.items():
            embeddings = self.model.encode(texts)
            self.template_embeddings[cat] = np.mean(embeddings, axis=0)
    
    def classify(self, title: str, content: str) -> str:
        """基于相似度分类"""
        text = title + ' ' + content[:500]
        text_embedding = self.model.encode([text])
        
        # 计算与每个分类的相似度
        similarities = {}
        for cat, template_emb in self.template_embeddings.items():
            sim = cosine_similarity(text_embedding, [template_emb])[0][0]
            similarities[cat] = sim
        
        return max(similarities, key=similarities.get)
```

---

## 4. 完整处理流程

```python
# ingestor/article_processor.py

from content_fetcher import FreeContentFetcher
from summarizer import TextRankSummarizer
from classifier import RuleClassifier

class FreeArticleProcessor:
    """免费文章处理器"""
    
    def __init__(self):
        self.fetcher = FreeContentFetcher()
        self.summarizer = TextRankSummarizer()
        self.classifier = RuleClassifier()
    
    async def process(self, url: str, title: str, rss_description: str = '') -> dict:
        """
        处理单篇文章
        
        Returns:
            {
                'title': str,
                'url': str,
                'content': str,
                'summary': str,
                'category': str,
                'tags': list,
                'source': str
            }
        """
        # 1. 抓取完整内容
        fetched = self.fetcher.fetch_content(url)
        
        if fetched and fetched['content']:
            content = fetched['content']
            # 使用抓取到的标题（通常更完整）
            final_title = fetched['title'] or title
        else:
            # 抓取失败，使用 RSS 的 description
            content = rss_description
            final_title = title
        
        # 2. 生成摘要
        if len(content) > 300:
            summary = self.summarizer.summarize(content, num_sentences=2)
        else:
            summary = content[:200]
        
        # 3. 分类
        classification = self.classifier.classify(final_title, content)
        
        return {
            'title': final_title,
            'url': url,
            'content': content[:2000],  # 限制长度
            'summary': summary,
            'category': classification['category'],
            'tags': classification['tags'],
            'source': self._detect_source(url)
        }
    
    def _detect_source(self, url: str) -> str:
        """从 URL 检测来源"""
        domains = {
            '36kr.com': '36氪',
            'arxiv.org': 'ArXiv',
            'news.ycombinator.com': 'Hacker News',
            'techcrunch.com': 'TechCrunch',
            'v2ex.com': 'V2EX',
            'mit.edu': 'MIT Technology Review',
            'venturebeat.com': 'VentureBeat',
            'jiqizhixin.com': '机器之心',
            'taime.com': '钛媒体',
            'leiphone.com': '雷峰网'
        }
        
        for domain, name in domains.items():
            if domain in url:
                return name
        
        return '其他'
```

---

## 5. 成本对比

| 方案 | 月成本 | 准确率 | 速度 | 推荐场景 |
|------|--------|--------|------|----------|
| **本方案** | **0元** | 中 | 快 | 个人/小项目 |
| OpenAI API | ~$20-50 | 高 | 快 | 商业项目 |
| 智谱 API | ~￥50-200 | 高 | 快 | 中文内容 |

---

## 6. 实施步骤

### 今天就能完成（2小时）

1. **安装依赖**
   ```bash
   pip install newspaper3k trafilatura jieba
   python -m nltk.downloader punkt
   ```

2. **复制代码**
   - 创建 `ingestor/content_fetcher.py`
   - 创建 `ingestor/summarizer.py`
   - 创建 `ingestor/classifier.py`
   - 创建 `ingestor/article_processor.py`

3. **测试运行**
   ```python
   processor = FreeArticleProcessor()
   result = processor.process(
       url='https://36kr.com/p/123456.html',
       title='原标题',
       rss_description='RSS描述'
   )
   print(result)
   ```

### 本周优化

1. **添加更多数据源规则**
2. **优化分类关键词**
3. **处理特殊情况（登录墙、反爬）**
4. **批量处理队列**

---

## 7. 注意事项

### 爬虫礼仪
- ⚠️ 添加延迟（1-2秒）
- ⚠️ 遵守 robots.txt
- ⚠️ 不要并发太高
- ⚠️ 失败时优雅降级（用 RSS 内容）

### 准确性优化
- 📊 根据实际数据调整关键词
- 📊 收集用户反馈改进分类
- 📊 定期更新规则

---

## 下一步

您希望我：
1. **立即复制代码到项目**（今天就能用）
2. **先做简单的 rule-based 分类**（30分钟）
3. **等明天再完整实施**

**推荐**: 先做简单的 rule-based 分类（方案A），让文章有分类标签，内容可以先用 RSS 的 description，后续再抓取完整内容。

请告诉我您的选择！
