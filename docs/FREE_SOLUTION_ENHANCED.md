# 免费开源内容处理方案（优化版）

## 发现的新工具

经过深入调研，发现了多个更好的开源替代方案。

---

## 1. 内容提取（更好的方案）

### 方案 A: newspaper4k ⭐ 推荐

**newspaper3k 的活跃 fork，持续维护**

```python
pip install newspaper4k
```

```python
from newspaper import Article

url = 'https://36kr.com/p/123456.html'
article = Article(url, language='zh')
article.download()
article.parse()

print(article.title)      # 标题
print(article.text)       # 正文（完整）
print(article.authors)    # 作者
print(article.publish_date)  # 发布时间
print(article.top_image)  # 封面图
print(article.keywords)   # 关键词（NLP提取）
print(article.summary)    # 摘要（自动提取）
```

**优点**：
- ✅ newspaper3k 的继任者，持续更新
- ✅ 内置 NLP，自动提取关键词和摘要
- ✅ 支持中文
- ✅ 自动识别发布时间、作者
- ✅ 能提取顶部图片

### 方案 B: news-fetch ⭐ 更简单

**开箱即用，内置 NLP**

```python
pip install news-fetch
```

```python
from newsfetch import NewsFetch

news = NewsFetch('https://36kr.com/p/123456.html')
print(news.title)
print(news.content)
print(news.summary)  # 自动生成摘要
print(news.keywords)  # 自动提取关键词
print(news.authors)
```

**优点**：
- ✅ 一行代码搞定
- ✅ 自带摘要和关键词
- ✅ 基于 newspaper3k + NLP 增强

### 方案 C: fundus ⭐ 更适合中文

**专为新闻媒体设计**

```python
pip install fundus
```

```python
from fundus import PublisherCollection, Crawler

# 支持 100+ 新闻源
crawler = Crawler(PublisherCollection.cn)  # 中文新闻源

for article in crawler.crawl(
    max_articles=10,
    only_complete=True  # 只返回完整的文章
):
    print(article.title)
    print(article.body)  # 正文
    print(article.summary)
    print(article.authors)
    print(article.publishing_date)
```

**支持的 中文新闻源**：
- 中国日报 (China Daily)
- 环球时报 (Global Times)
- 人民日报 (People's Daily)
- 新华网 (Xinhua)
- ...等 100+ 国际新闻源

---

## 2. 文本摘要（更好的方案）

### 方案 A: HanLP ⭐ 中文效果最好

**开源中文 NLP 神器，支持抽取式摘要**

```python
pip install hanlp
```

```python
import hanlp

# 加载预训练模型
HanLP = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH)

# 抽取式摘要
text = """这里是很长的新闻内容..."""
summary = HanLP(text, tasks='extractive_summarization')

print(summary['extractive_summarization'])  # 关键句子
```

**优点**：
- ✅ 中文效果顶级
- ✅ 完全免费，本地运行
- ✅ 支持多种 NLP 任务

### 方案 B: UniLM_summarization ⭐ 生成式摘要

**基于中文 BERT 的生成式摘要**

```bash
git clone https://github.com/chenlian98/UniLM_summarization.git
pip install -r requirements.txt
```

```python
from summarization import UniLMSummarizer

model = UniLMSummarizer(model_path='unilm-base-chinese')
text = "这里是很长的新闻内容..."
summary = model.generate(text, max_length=100)
print(summary)
```

**优点**：
- ✅ 生成式摘要，更自然
- ✅ 基于中文 BERT，理解中文更好
- ✅ 完全开源免费

### 方案 C: 本地小模型（CPU可跑）

**ChatGLM-6B-Int4（量化版）**

```bash
# 下载模型（约 6GB）
git clone https://huggingface.co/THUDM/chatglm-6b-int4

# 或用更小模型
git clone https://huggingface.co/THUDM/chatglm2-6b-int4
```

```python
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True).half().cuda()

# 生成摘要
prompt = "请用50字概括以下内容：\n" + article_text[:2000]
response, history = model.chat(tokenizer, prompt, history=[])
print(response)
```

**硬件要求**：
- Int4 量化版：6GB 显存（或 CPU + 16GB 内存）
- Int8 量化版：8GB 显存

---

## 3. 智能分类（更好的方案）

### 方案 A: bert-base-chinese + 微调（推荐）

**使用开源 BERT 做文本分类**

```python
# 使用 transformers 库的零样本分类
from transformers import pipeline

# 零样本分类（无需训练）
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",  # 多语言模型
    device=-1  # CPU
)

text = "OpenAI发布GPT-5新模型..."
labels = ["热门", "深度", "新品", "突发"]

result = classifier(text, labels)
print(result['labels'][0])  # 最可能的分类
print(result['scores'][0])  # 置信度
```

**优点**：
- ✅ 零样本，无需训练数据
- ✅ 多语言支持
- ✅ 完全免费

### 方案 B: 使用现有的开源分类模型

```python
# 使用阿里开源的文本分类模型
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 下载模型（约 400MB）
model_name = "uer/roberta-base-finetuned-jd-binary-chinese"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 分类
text = "OpenAI发布新模型..."
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
outputs = model(**inputs)
predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
print(predictions)
```

### 方案 C: 简单但有效的关键词匹配

```python
# 更快更简单，不需要下载模型
import jieba
import jieba.analyse

def classify_by_keywords(text):
    """基于 TF-IDF 提取关键词，匹配分类"""
    
    # 提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True)
    
    # 分类词典
    categories = {
        'breaking': {'突发': 10, '紧急': 10, '重磅': 8, '刚刚': 8},
        'hot': {'热门': 8, '热议': 8, '火了': 7, '爆款': 7},
        'new': {'发布': 6, '新品': 6, '推出': 6, '上线': 6},
        'deep': {'研究': 5, '深度': 5, '分析': 5, '解读': 5}
    }
    
    # 计算分类得分
    scores = {}
    for cat, words in categories.items():
        score = 0
        for word, weight in keywords:
            if word in words:
                score += words[word] * weight
        scores[cat] = score
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else 'new'
```

---

## 4. 推荐最佳组合

### 🏆 推荐方案 A：全部免费，效果最好

| 功能 | 工具 | 优点 |
|------|------|------|
| **内容提取** | `newspaper4k` | 持续维护，自带 NLP |
| **摘要生成** | `HanLP` | 中文效果最佳 |
| **智能分类** | `bert-base-chinese` | 准确率高 |

**成本：0 元**

### 🚀 推荐方案 B：最简单快速

| 功能 | 工具 | 优点 |
|------|------|------|
| **内容提取** | `news-fetch` | 一行代码 |
| **摘要生成** | 内置摘要 | news-fetch 自带 |
| **智能分类** | 规则匹配 | 无需模型 |

**成本：0 元**

### 🎯 推荐方案 C：平衡效果与资源

| 功能 | 工具 | 优点 |
|------|------|------|
| **内容提取** | `newspaper4k` | 功能全面 |
| **摘要生成** | `TextRank` (gensim) | 快速，无需模型 |
| **智能分类** | 关键词 + TF-IDF | 简单有效 |

**成本：0 元**

---

## 5. 完整代码示例（推荐方案 C）

```python
# ingestor/enhanced_processor.py

import requests
from newspaper import Article
from gensim.summarization import summarize as gensim_summarize
import jieba
import jieba.analyse
from typing import Dict, List

class EnhancedArticleProcessor:
    """优化的文章处理器 - 完全免费"""
    
    def __init__(self):
        # 加载 jieba 词典（可选，提升准确率）
        # jieba.load_userdict('custom_dict.txt')
        pass
    
    def fetch_content(self, url: str) -> Dict:
        """抓取文章内容"""
        try:
            article = Article(url, language='zh')
            article.download()
            article.parse()
            
            # 使用内置 NLP
            article.nlp()
            
            return {
                'title': article.title,
                'content': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'keywords': article.keywords,  # NLP提取的关键词
                'top_image': article.top_image,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_summary(self, text: str, word_count: int = 100) -> str:
        """生成摘要"""
        if len(text) < 200:
            return text[:200]
        
        try:
            # 使用 gensim 的 TextRank（支持中文）
            summary = gensim_summarize(text, word_count=word_count)
            return summary if summary else text[:200]
        except:
            # 降级：取前 N 个句子
            sentences = text.split('。')[:3]
            return '。'.join(sentences) + '。'
    
    def classify(self, title: str, content: str) -> Dict:
        """智能分类"""
        text = title + ' ' + content[:1000]
        
        # 提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True)
        
        # 分类规则（带权重）
        rules = {
            'breaking': {
                'keywords': ['突发', '紧急', '刚刚', '重磅', '震惊'],
                'weight': 10
            },
            'hot': {
                'keywords': ['热门', '热议', '火了', '爆火', '热搜'],
                'weight': 8
            },
            'new': {
                'keywords': ['发布', '新品', '推出', '上线', '问世'],
                'weight': 6
            },
            'deep': {
                'keywords': ['研究', '深度', '分析', '解读', '综述'],
                'weight': 5
            }
        }
        
        # 计算得分
        scores = {}
        for cat, config in rules.items():
            score = 0
            for kw, weight in keywords:
                if kw in config['keywords']:
                    score += config['weight'] * weight
            scores[cat] = score
        
        # 选择最佳分类
        best_category = max(scores, key=scores.get) if max(scores.values()) > 0 else 'new'
        
        # 提取标签
        tag_keywords = ['AI绘画', 'LLM', 'ChatGPT', 'Midjourney', '产品发布', 
                       '研究', '工具', '安全', '商业', '硬件']
        tags = [kw for kw, _ in keywords if any(t in kw for t in tag_keywords)]
        
        return {
            'category': best_category,
            'tags': tags[:3],
            'keywords': [kw for kw, _ in keywords[:5]]
        }
    
    def process(self, url: str, rss_description: str = '') -> Dict:
        """处理单篇文章"""
        # 1. 抓取内容
        fetched = self.fetch_content(url)
        
        if not fetched['success']:
            # 抓取失败，使用 RSS 内容
            content = rss_description
            title = ''
        else:
            content = fetched['content']
            title = fetched['title']
        
        if not content:
            return None
        
        # 2. 生成摘要
        summary = self.generate_summary(content, word_count=100)
        
        # 3. 分类
        classification = self.classify(title, content)
        
        return {
            'title': title,
            'url': url,
            'content': content[:2000],  # 限制长度
            'summary': summary,
            'category': classification['category'],
            'tags': classification['tags'],
            'keywords': classification['keywords'],
            'authors': fetched.get('authors', []),
            'publish_date': fetched.get('publish_date', ''),
            'top_image': fetched.get('top_image', ''),
            'source': self._detect_source(url)
        }
    
    def _detect_source(self, url: str) -> str:
        """检测来源"""
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

### 安装依赖

```bash
pip install newspaper4k gensim jieba
python -m nltk.downloader punkt  # newspaper4k 需要
```

### 使用示例

```python
processor = EnhancedArticleProcessor()
result = processor.process(
    url='https://36kr.com/p/123456.html',
    rss_description='这是 RSS 的描述'
)

print(f"标题: {result['title']}")
print(f"分类: {result['category']}")
print(f"标签: {result['tags']}")
print(f"摘要: {result['summary'][:100]}...")
```

---

## 6. 性能对比

| 方案 | 准确率 | 速度 | 资源占用 | 易用性 |
|------|--------|------|----------|--------|
| newspaper4k + HanLP | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| news-fetch | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 本方案 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 7. 下一步建议

### 今天就能做（1小时）

1. 安装依赖并测试单个 URL
2. 调整分类关键词规则
3. 集成到现有的 ingestor

### 本周优化

1. 批量处理队列（防止被封）
2. 失败重试机制
3. 根据实际效果调整分类规则
4. 添加更多数据源

### 后期升级（可选）

1. 集成本地 ChatGLM（如果有 GPU）
2. 使用 HanLP 替代 gensim 摘要
3. 训练自己的分类模型

---

**推荐：先使用「方案 C」快速上线，验证效果后再决定是否升级！**
