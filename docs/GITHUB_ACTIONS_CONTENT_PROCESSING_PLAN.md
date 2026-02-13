# GitHub Actions 内容处理方案

> **目标**: 实现全自动化的 AI 文章内容抓取、摘要生成、智能分类
> **约束**: GitHub Actions 有限时（6小时）和资源限制（2核CPU, 7GB RAM）
> **成本**: 0 元（完全免费）

---

## 一、方案概述

### 1.1 现有问题

- ✅ 已实现: RSS 定时采集
- ❌ 待实现: 完整内容抓取、AI 摘要、智能分类

### 1.2 解决方案

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  RSS Scraper    │────▶│  Content Extractor│────▶│  AI Processor   │
│  (已有)         │     │  trafilatura     │     │  本地 LLM       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                        │
                              ▼                        ▼
                        ┌──────────────────────────────────┐
                        │        GitHub Actions           │
                        │   (ubuntu-latest, 2C7G, 6小时)   │
                        └──────────────────────────────────┘
                                      │
                                      ▼
                        ┌──────────────────────────────────┐
                        │  Daily Report + Git Commit       │
                        └──────────────────────────────────┘
```

---

## 二、技术选型

### 2.1 内容提取（免费 + 高准确率）

| 方案 | 准确率 | 维护状态 | 推荐度 |
|------|--------|----------|--------|
| **trafilatura 2.0** ⭐ | ⭐⭐⭐⭐⭐ | 活跃 | **强烈推荐** |
| **Jina Reader** ⭐ | ⭐⭐⭐⭐⭐ | 商业支持 | 降级备选 |
| newspaper4k | ⭐⭐⭐ | 维护较少 | 可用 |

**最终方案**:
```python
# 主方案: trafilatura
html = trafilatura.fetch_url(url)
text = trafilatura.extract(html, target_language='zh')

# 降级: Jina Reader
if not text or len(text) < 100:
    text = requests.get(f'https://r.jina.ai/{url}').text
```

### 2.2 摘要生成（免费 + CPU 可跑）

| 方案 | 硬件要求 | 中文效果 | 推荐度 |
|------|----------|----------|--------|
| **Qwen2.5-1.5B-Instruct** ⭐ | CPU可跑 | ⭐⭐⭐⭐⭐ | **强烈推荐** |
| Ollama + qwen:1.5b | CPU可跑 | ⭐⭐⭐⭐⭐ | 运维简单 |
| mBART-50 | 需GPU | ⭐⭐⭐ | 不推荐 |

**最终方案**:
```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:1.5b
```

```python
# API 调用
import requests
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:1.5b",
        "prompt": f"请用50字概括以下内容：{text[:2000]}",
        "stream": False
    }
)
return response.json()['response']
```

**为什么选 Qwen2.5-1.5B**:
- ✅ 1.5B 参数，量化后约 1.5GB
- ✅ 中文效果接近 GPT-3.5
- ✅ CPU 推理约 5-10 秒/篇
- ✅ Ollama 一键安装，运维简单

### 2.3 智能分类（免费 + 高准确率）

| 方案 | 准确率 | 资源占用 | 推荐度 |
|------|--------|----------|--------|
| **BAAI/bge-m3** ⭐ | ⭐⭐⭐⭐⭐ | 400MB | **强烈推荐** |
| **BAAI/bge-large-zh** | ⭐⭐⭐⭐⭐ | 1.5GB | 高质量场景 |
| jieba TF-IDF | ⭐⭐⭐ | 10MB | 兜底方案 |

**最终方案**:
```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 加载模型
classifier = SentenceTransformer('BAAI/bge-m3')

# 分类模板
templates = {
    'breaking': ['突发新闻', '紧急快讯', '重磅消息'],
    'hot': ['热门话题', '热议', 'trending'],
    'new': ['新品发布', '新版本', '正式上线'],
    'deep': ['深度分析', '技术解读', '研究论文']
}

# 预计算
template_embs = {cat: classifier.encode(templates[cat]) for cat in templates}

# 分类函数
def classify(text):
    text_emb = classifier.encode([text[:500]])
    scores = {cat: np.dot(text_emb, template_embs[cat])[0] for cat in templates}
    return max(scores, key=scores.get)
```

---

## 三、工作流设计

### 3.1 GitHub Actions 配置

```yaml
name: AI Content Processor

on:
  schedule:
    - cron: "0 8 * * *"  # 每天 8:00 UTC (北京时间 16:00)
  workflow_dispatch:
    inputs:
      mode:
        type: choice
        options: [full, fetch_only, summarize_only, classify_only]

env:
  PYTHON_VERSION: "3.12"
  MAX_ARTICLES: 30  # 限制处理数量

jobs:
  content-processing:
    runs-on: ubuntu-latest
    timeout-minutes: 180  # 3 小时超时
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install trafilatura requests beautifulsoup4 jieba pyyaml
          pip install sentence-transformers transformers accelerate
          pip install ollama  # Ollama Python SDK

      - name: Install and start Ollama
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          ollama pull qwen2.5:1.5b
          ollama serve &
          sleep 10

      - name: Run processing pipeline
        run: |
          python scripts/content_processor.py \
            --input ai/articles/original \
            --output ai/articles/processed \
            --max-articles ${{ env.MAX_ARTICLES }}

      - name: Generate daily report
        run: |
          python scripts/generate_report.py \
            --input ai/articles/processed \
            --output ai/daily/REPORT.md

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git add ai/
          git commit -m "AI Content: $(date +%Y-%m-%d)"
          git push
```

### 3.2 处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                            │
│                    ubuntu-latest                            │
│                     2C7G, 6H                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 准备环境                                             │
│   - Python 3.12 + pip                                       │
│   - 安装 trafilatura, sentence-transformers                  │
│   - 安装 Ollama + qwen2.5:1.5b                             │
│   - 预加载 bge-m3 模型                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 内容提取 (10-20 秒/篇)                              │
│                                                             │
│   for article in articles[:30]:                             │
│     try:                                                    │
│       text = trafilatura.extract(url)                       │
│       if len(text) < 100:                                  │
│         text = jina_reader(url)  # 降级                    │
│       save(text, extracted/)                                │
│     except:                                                 │
│       use_rss_description()  # 最终降级                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 摘要生成 (5-10 秒/篇)                               │
│                                                             │
│   for article in extracted:                                 │
│     summary = ollama.generate(                              │
│       model="qwen2.5:1.5b",                                │
│       prompt=f"50字概括: {text[:2000]}"                    │
│     )                                                       │
│     save(summary, summarized/)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 智能分类 (1-2 秒/篇)                                │
│                                                             │
│   for article in summarized:                                │
│     text = read(article)                                    │
│     scores = bge_m3.classify(text[:1000])                  │
│     category = max(scores, key=scores.get)                  │
│     if scores[category] < 0.3:                             │
│       category = "new"  # 默认分类                          │
│     save(category, classified/)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: 生成日报                                            │
│                                                             │
│   categories = {                                            │
│     "breaking": [],                                         │
│     "hot": [],                                              │
│     "new": [],                                              │
│     "deep": []                                              │
│   }                                                         │
│                                                             │
│   for article in classified:                                │
│     categories[article.category].append(article)             │
│                                                             │
│   report = generate_markdown(categories)                   │
│   save(report, ai/daily/REPORT.md)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: 提交结果                                            │
│                                                             │
│   git add ai/                                               │
│   git commit -m "AI Content: 2026-02-13"                    │
│   git push                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 时间估算

| 步骤 | 每篇耗时 | 30篇总耗时 | 说明 |
|------|----------|------------|------|
| 环境准备 | - | ~5 分钟 | 模型下载 |
| 内容提取 | 10-20s | 5-10 分钟 | 主要耗时 |
| 摘要生成 | 5-10s | 3-5 分钟 | LLM 推理 |
| 智能分类 | 1-2s | 1 分钟 | Embedding |
| 生成日报 | - | 10 秒 | - |
| **总计** | - | **~15 分钟** | 远低于 6 小时限制 |

---

## 四、代码结构

```
scripts/
├── content_processor.py    # 主处理脚本
│
├── extractors/
│   ├── __init__.py
│   ├── trafilatura_extractor.py   # 主提取器
│   └── jina_extractor.py          # 降级提取器
│
├── summarizers/
│   ├── __init__.py
│   └── ollama_summarizer.py       # LLM 摘要
│
├── classifiers/
│   ├── __init__.py
│   └── bge_classifier.py          # Embedding 分类
│
└── report_generator.py   # 日报生成
```

### 4.1 主脚本 `content_processor.py`

```python
#!/usr/bin/env python3
"""
AI 文章内容处理器

功能:
1. 从 URL 抓取完整内容
2. 用 LLM 生成摘要
3. 用 Embedding 智能分类
4. 生成结构化日报
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from extractors import TrafilaturaExtractor, JinaExtractor
from summarizers import OllamaSummarizer
from classifiers import BGEClassifier
from report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentProcessor:
    """文章内容处理器"""
    
    def __init__(self, max_articles: int = 30):
        self.max_articles = max_articles
        
        # 初始化组件
        self.extractor = TrafilaturaExtractor()
        self.fallback_extractor = JinaExtractor()
        self.summarizer = OllamaSummarizer()
        self.classifier = BGEClassifier()
        self.report_generator = ReportGenerator()
    
    def process_article(self, url: str, title: str) -> Dict:
        """处理单篇文章"""
        result = {
            'url': url,
            'title': title,
            'content': '',
            'summary': '',
            'category': 'new',
            'tags': [],
            'source': self._detect_source(url)
        }
        
        # 1. 提取内容
        logger.info(f"提取内容: {url}")
        content = self.extractor.extract(url)
        if not content or len(content) < 100:
            content = self.fallback_extractor.extract(url)
        
        if not content:
            logger.warning(f"无法提取内容，使用 RSS 描述")
            content = title  # 最终降级
        
        result['content'] = content[:10000]  # 限制长度
        
        # 2. 生成摘要
        logger.info(f"生成摘要...")
        result['summary'] = self.summarizer.summarize(content[:3000])
        
        # 3. 智能分类
        logger.info(f"智能分类...")
        classification = self.classifier.classify(
            title + ' ' + result['summary']
        )
        result['category'] = classification['category']
        result['tags'] = classification['tags']
        
        return result
    
    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """批量处理"""
        results = []
        for i, article in enumerate(articles[:self.max_articles]):
            logger.info(f"处理 {i+1}/{len(articles)}: {article['title']}")
            try:
                result = self.process_article(
                    article['url'],
                    article.get('title', '')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败: {e}")
                continue
        
        return results
    
    def _detect_source(self, url: str) -> str:
        """检测来源"""
        domains = {
            '36kr.com': '36氪',
            'arxiv.org': 'ArXiv',
            'news.ycombinator.com': 'Hacker News',
            'techcrunch.com': 'TechCrunch',
            'jiqizhixin.com': '机器之心',
            'mit.edu': 'MIT Tech Review',
        }
        for domain, name in domains.items():
            if domain in url:
                return name
        return '其他'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default='ai/articles/original')
    parser.add_argument('--output', type=Path, default='ai/articles/processed')
    parser.add_argument('--max-articles', type=int, default=30)
    args = parser.parse_args()
    
    # 读取待处理文章列表
    input_dir = Path(args.input)
    articles = []
    for f in input_dir.glob('*.md'):
        with open(f) as file:
            content = file.read()
            url = content.split('\n')[0].replace('URL:', '').strip()
            title = content.split('\n')[1].replace('标题:', '').strip() if '\n' in content else f.name
            articles.append({'url': url, 'title': title, 'file': f.name})
    
    # 处理
    processor = ContentProcessor(max_articles=args.max_articles)
    results = processor.process_batch(articles)
    
    # 保存结果
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        output_file = output_dir / result['title'][:50].replace(' ', '_') + '.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 生成日报
    processor.report_generator.generate(results, 'ai/daily/REPORT.md')
    
    logger.info(f"处理完成: {len(results)} 篇文章")


if __name__ == '__main__':
    main()
```

### 4.2 内容提取器

```python
# scripts/extractors/trafilatura_extractor.py

import trafilatura
from typing import Optional


class TrafilaturaExtractor:
    """trafilatura 内容提取器"""
    
    def __init__(self):
        pass
    
    def extract(self, url: str) -> Optional[str]:
        """提取网页正文"""
        try:
            # 获取 HTML
            html = trafilatura.fetch_url(url)
            if not html:
                return None
            
            # 提取正文
            text = trafilatura.extract(
                html,
                target_language='zh',
                include_comments=False,
                include_tables=False,
                deduplicate=True
            )
            
            if text and len(text) > 100:
                return text.strip()
            
            return None
            
        except Exception as e:
            print(f"trafilatura 提取失败: {e}")
            return None


# scripts/extractors/jina_extractor.py

import requests
from typing import Optional


class JinaExtractor:
    """Jina Reader 降级提取器"""
    
    def extract(self, url: str) -> Optional[str]:
        """通过 Jina API 提取"""
        try:
            response = requests.get(
                f'https://r.jina.ai/{url}',
                timeout=30
            )
            
            if response.status_code == 200:
                text = response.text
                if len(text) > 100:
                    return text.strip()
            
            return None
            
        except Exception as e:
            print(f"Jina 提取失败: {e}")
            return None
```

### 4.3 摘要生成器

```python
# scripts/summarizers/ollama_summarizer.py

import requests
import time
from typing import Optional


class OllamaSummarizer:
    """Ollama LLM 摘要生成器"""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.model = "qwen2.5:1.5b"
        self.prompt_template = """请用50字以内概括以下内容，突出核心信息：

{}

要求：
1. 用中文输出
2. 简洁明了
3. 直接输出摘要，不要前缀

摘要："""
    
    def summarize(self, text: str) -> str:
        """生成摘要"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self.prompt_template.format(text[:2000]),
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 100
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            
            return text[:200]  # 降级
            
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return text[:200]  # 降级
```

### 4.4 分类器

```python
# scripts/classifiers/bge_classifier.py

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List


class BGEClassifier:
    """BGE Embedding 智能分类器"""
    
    def __init__(self):
        self.model = SentenceTransformer('BAAI/bge-m3')
        
        # 分类模板
        self.templates = {
            'breaking': [
                '突发新闻', '紧急快讯', '重磅消息', 'Breaking News',
                '刚刚发布', '震惊业界', '重大突破'
            ],
            'hot': [
                '热门话题', '热议讨论', 'trending', '热搜',
                '病毒式传播', '全网刷屏', '引发争议'
            ],
            'new': [
                '新品发布', '新版本上线', '正式发布', '发布公告',
                '产品更新', '功能发布', '全新推出'
            ],
            'deep': [
                '深度分析', '技术解读', '研究论文', '原理解析',
                '内部原理', '详细评测', '系统性研究'
            ]
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
        
        # 预计算模板 embedding
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """预计算分类模板"""
        self.template_embs = {}
        for cat, texts in self.templates.items():
            embs = self.model.encode(texts)
            self.template_embs[cat] = np.mean(embs, axis=0)
    
    def classify(self, text: str) -> Dict[str, any]:
        """分类文章"""
        if not text:
            return {'category': 'new', 'tags': []}
        
        text = text[:1000]
        
        # 计算相似度
        text_emb = self.model.encode([text])
        scores = {}
        
        for cat, template_emb in self.template_embs.items():
            sim = np.dot(text_emb, template_emb.T)[0]
            scores[cat] = float(sim)
        
        # 选择最佳分类
        if max(scores.values()) > 0:
            category = max(scores, key=scores.get)
        else:
            category = 'new'
        
        # 阈值判断
        if scores.get(category, 0) < 0.3:
            category = 'new'
        
        # 提取标签
        tags = self._extract_tags(text)
        
        return {
            'category': category,
            'tags': tags[:3],  # 最多3个标签
            'scores': scores
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        text_lower = text.lower()
        tags = []
        
        for tag, keywords in self.tag_keywords.items():
            if any(kw.lower() in text_lower for kw in keywords):
                tags.append(tag)
        
        return tags
```

### 4.5 日报生成器

```python
# scripts/report_generator.py

import json
from datetime import datetime
from typing import List, Dict


class ReportGenerator:
    """日报生成器"""
    
    def __init__(self):
        self.categories = {
            'breaking': '🚨 突发新闻',
            'hot': '🔥 热门话题',
            'new': '🆕 新品发布',
            'deep': '💡 深度分析'
        }
    
    def generate(self, articles: List[Dict], output_path: str):
        """生成 Markdown 日报"""
        
        # 按分类整理
        categorized = {cat: [] for cat in self.categories}
        for article in articles:
            cat = article.get('category', 'new')
            if cat in categorized:
                categorized[cat].append(article)
        
        # 统计
        total = len(articles)
        
        # 生成 Markdown
        md = f"""# AI Daily Report - {datetime.now().strftime('%Y-%m-%d')}

## 📊 统计概览

- **总文章数**: {total}
{''.join([f"- **{self.categories[cat]}**: {len(categorized[cat])} 篇\n' for cat in self.categories])}

---

"""
        
        # 各分类详细内容
        for cat, title in self.categories.items():
            if categorized[cat]:
                md += f"## {title}\n\n"
                for article in categorized[cat]:
                    md += f"""### {article['title']}

- **来源**: {article.get('source', '未知')}
- **标签**: {', '.join(article.get('tags', [])) or '无'}
- **摘要**: {article.get('summary', '')[:200]}...

[原文]({article['url']})

---
"""
        
        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"日报已生成: {output_path}")
```

---

## 五、资源占用估算

### 5.1 GitHub Actions 资源

| 资源 | 占用 | 限制 | 使用率 |
|------|------|------|--------|
| CPU | 2 核 | 2 核 | 100% |
| 内存 | ~5 GB | 7 GB | ~70% |
| 磁盘 | ~3 GB | ~14 GB | ~20% |
| 时间 | ~15 分钟 | 360 分钟 | ~4% |

### 5.2 模型资源

| 模型 | 大小 | 内存占用 | 首次下载 |
|------|------|----------|----------|
| BAAI/bge-m3 | ~400MB | ~1 GB | ✅ 首次运行 |
| Qwen2.5-1.5B | ~1.5GB | ~2 GB | ✅ 需预下载 |
| trafilatura | - | ~100MB | - |
| **总计** | ~2GB | ~3.5GB | 远低于 7GB 限制 |

---

## 六、优化策略

### 6.1 速度优化

```python
# 并行处理（利用多核）
from concurrent.futures import ThreadPoolExecutor

def process_parallel(articles, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_article, articles))
    return results
```

### 6.2 缓存策略

```yaml
# .gitignore
# 忽略模型缓存（GitHub Actions 会自动缓存）
~/.cache/huggingface/
~/.cache/torch/
~/.cache/transformers/
```

```yaml
# GitHub Actions - 缓存模型
- name: Cache models
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/huggingface
      ~/.cache/torch
    key: models-${{ runner.os }}-bge-m3
```

### 6.3 降级策略

```python
# 三级降级
def extract_with_fallback(url):
    # 1. trafilatura
    text = trafilatura.extract(url)
    if text and len(text) > 100:
        return text
    
    # 2. Jina Reader
    text = jina_extract(url)
    if text and len(text) > 100:
        return text
    
    # 3. RSS description (最终降级)
    return get_rss_description(url)
```

---

## 七、实施步骤

### 7.1 第一步：创建目录结构

```bash
mkdir -p scripts/{extractors,summarizers,classifiers}
touch scripts/{__init__.py,content_processor.py,report_generator.py}
touch scripts/{extractors,summarizers,classifiers}/__init__.py
```

### 7.2 第二步：创建处理脚本

按上述代码创建各个模块

### 7.3 第三步：测试运行

```bash
# 本地测试
python scripts/content_processor.py \
  --input ai/articles/original \
  --output ai/articles/processed \
  --max-articles 5
```

### 7.4 第四步：创建 GitHub Actions

```bash
# 创建工作流
mkdir -p .github/workflows
touch .github/workflows/content-processing.yml
```

### 7.5 第五步：配置定时任务

工作流会自动在每天 8:00 UTC 执行

---

## 八、预期效果

### 8.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 处理时间 | < 30 分钟 | 30 篇文章 |
| 成功率 | > 90% | 提取成功比例 |
| 准确率 | > 80% | 分类正确比例 |
| 成本 | 0 元 | GitHub Actions 免费 |

### 8.2 输出示例

```markdown
# AI Daily Report - 2026-02-13

## 📊 统计概览

- **总文章数**: 25
- 🚨 突发新闻: 2 篇
- 🔥 热门话题: 5 篇
- 🆕 新品发布: 10 篇
- 💡 深度分析: 8 篇

---

## 🚨 突发新闻

### OpenAI 发布 GPT-5 重大更新

- **来源**: OpenAI
- **标签**: LLM, 产品
- **摘要**: OpenAI 今日宣布 GPT-5 重大更新，支持更长的上下文窗口...

[原文](https://openai.com/blog/gpt-5-update)
```

---

## 九、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| GitHub Actions 超时 | 低 | 高 | 限制文章数量，优先处理 |
| 模型下载失败 | 中 | 中 | 添加重试，使用缓存 |
| API 限流 | 低 | 中 | Jina Reader 降级 |
| LLM 质量差 | 中 | 中 | 提示词优化，降级截取 |

---

## 十、总结

### 方案优势

1. **完全免费**: 所有工具均为开源免费
2. **零运维**: GitHub Actions 自动执行
3. **高准确率**: trafilatura + BGE + Qwen 组合
4. **可扩展**: 模块化设计，易于修改
5. **容错强**: 多级降级策略

### 下一步

1. ✅ 创建目录结构
2. ⬜ 编写各模块代码
3. ⬜ 本地测试
4. ⬜ 创建 GitHub Actions
5. ⬜ 部署验证

---

**文档版本**: v1.0
**创建时间**: 2026-02-13
**作者**: AI Daily Collector

---

## 十一 实施计划与风险控制

### 11.1 方案 A：GH Actions 基线实施计划
- 目标：在 GitHub Actions 环境中实现端到端的内容处理流水线，包含提取、摘要、分类、日报输出，具备幂等、降级和基础缓存机制，确保资源约束下的可稳定运行。
- 架构要点：RSS/源抓取 -> 内容提取（trafilatura 为主，Jina 降级） -> 摘要（Ollama/qwen） -> 分类（BAAI/bge-m3） -> 日报生成 -> 提交/推送报告
- 阶段性工作计划：
  1) 阶段 1（1-2 周）：搭建骨架、实现端到端最小流、实现幂等与降级路径
  2) 阶段 2（2-3 周）：引入缓存、强化错⻛处理、初步监控输出
  3) 阶段 3（2 周）：完善端到端测试、回滚策略、文档与示例
  4) 阶段 4（1 周）：性能评估与成本控制、上线准备
- 里程碑：
  - Milestone 1：骨架就绪并可跑通小样本
  - Milestone 2：幂等、降级、缓存落地
  - Milestone 3：端到端稳定性测试通过
  - Milestone 4：成本与性能达到或接近目标
- 风险与回滚点：
  - 风险：GH Actions 超时/资源受限 → 回滚到更小的 batch size 并启用分批执行；降低 MAX_ARTICLES
  - 风险：模型加载失败/推理慢 → 回滚到降级文本或 RSS 描述，缓存结果以避免重复请求
  - 风险：外部服务不可用 → 回滚至本地可用的降级流程，记录错误并发出告警
  - 风险：幂等边界模糊 → 引入全局去重表与版本控制，确保重复执行不会影响结果

### 11.2 方案 B：Dagster/Prefect 编排实施计划（高鲁棒性与可观测性）
- 目标：以 Dagster/Prefect 作为端到端编排层，将提取、摘要、分类、日报等步骤以资产/作业形式组织，提升可观测性、重试策略和数据血缘能力。
- 架构要点：任务 DAG/资产，重试策略，血缘跟踪，指标与日志，独立执行与 GH Actions 集成点。
- 阶段性工作计划：
  1) 阶段 1：确定资产模型、任务图、接口契约
  2) 阶段 2：实现核心资产与数据流
  3) 阶段 3：引入血缘、指标、测试
  4) 阶段 4：CI/CD 集成、回滚与降级策略
- 里程碑：
  - Milestone 1：核心资产 + 流程可跑
  - Milestone 2：血缘和观测性完备
  - Milestone 3：端到端稳定性验证通过
- 风险与回滚点：
  - 风险：学习曲线与运行成本
  - 回滚：先回落到方案 A 的实现，再逐步迁移到 Dagster/Prefect

### 11.3 方案 C：微服务端到端流水线实施计划（长期扩展性）
- 目标：将各阶段模块化为独立微服务，使用轻量队列/HTTP 接口解耦，便于横向扩展和部署。
- 架构要点：提取、摘要、分类、日报服务，以及一个聚合/编排服务；Docker/K8s 部署方案可选。
- 阶段性工作计划：
  1) 阶段 1：定义服务接口、搭建最小微服务集
  2) 阶段 2：实现聚合器与任务分发
  3) 阶段 3：缓存、幂等、健康检查
  4) 阶段 4：端到端测试 + 部署演练
- 里程碑：
  - Milestone 1：微服务雏形就绪
  - Milestone 2：聚合器就绪，端到端可跑
  - Milestone 3：缓存、幂等、健康检查完成
- 风险与回滚点：
  - 风险：运维复杂性/成本上升 → 回滚到方案 A，逐步迁移
  - 风险：接口不兼容/版本冲突 → 回滚点设计、版本化接口

## 参考与导航
- 方案 A 的落地模板与草案请见：docs/IMPLEMENTATION_PLAN_A_B_C.md
- 方案 B/C 的前置参考：Dagster、Prefect 的官方文档与实际案例链接
