# 文章内容抓取与处理方案

## 当前问题

现有的 scraper 只抓取了 RSS/API 提供的简要描述（description），存在的问题：
- ❌ 内容不完整（只有前500字符）
- ❌ 质量参差不齐（有些只是广告/导航）
- ❌ 没有AI总结
- ❌ 没有智能分类

---

## 解决方案

### 方案一：简单增强（推荐先实施）
使用 RSS 提供的 description 直接存储，不进行额外抓取。

**优点**: 简单、快速、不触发反爬
**缺点**: 内容质量依赖 RSS 源

### 方案二：完整抓取（推荐长期）
访问原 URL，抓取完整文章内容，然后用 AI 处理。

**优点**: 内容完整、可AI总结、可控性强
**缺点**: 需要处理反爬、耗时、可能失败

---

## 推荐实施方案

### Phase 1: 利用现有 description（今天完成）

当前 scraper 已经获取了 description，可以先存储到数据库的 `content` 字段。

**修改点**:
```python
# 在 ingestor/main.py 中
article = ArticleModel(
    id=generate_id(),
    title=item['title'],
    url=item['url'],
    content=item.get('description', ''),  # 使用 RSS 的 description
    summary=item.get('description', '')[:200],  # 前200字作为摘要
    source=source_name,
    # ...
)
```

---

### Phase 2: 内容抓取服务（本周实施）

创建 `content_fetcher` 模块，专门负责：
1. 从 URL 抓取完整内容
2. 清洗 HTML，提取正文
3. AI 总结生成摘要
4. 智能分类

#### 2.1 技术选型

**内容抓取**:
- 方案A: `requests` + `BeautifulSoup` (简单网站)
- 方案B: `playwright` (JavaScript 渲染的网站)
- 方案C: 第三方服务 (如 ScrapingBee, ScrapingAnt)

**AI 处理**:
- 国内: 智谱 GLM-4 / 文心一言 / 通义千问
- 国外: OpenAI GPT-4 / Claude

**分类算法**:
- 规则匹配（关键词）- 快速但不够智能
- AI 分类 - 准确但需要API调用

#### 2.2 架构设计

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   RSS Scraper   │────▶│  Content Fetcher │────▶│   AI Processor  │
│  (获取URL+描述)  │     │  (抓取完整内容)   │     │  (总结+分类)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   D1 Database   │
                                                │ (存储处理结果)  │
                                                └─────────────────┘
```

#### 2.3 Content Fetcher 实现

```python
# ingestor/content_fetcher.py

import requests
from bs4 import BeautifulSoup
from typing import Optional
import trafilatura  # 专门提取网页正文的库

class ContentFetcher:
    """从URL抓取网页内容"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_content(self, url: str) -> Optional[str]:
        """抓取网页正文内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 使用 trafilatura 提取正文（效果比 BeautifulSoup 好）
            content = trafilatura.extract(response.text)
            
            if content and len(content) > 100:
                return content
            return None
            
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None
```

**安装依赖**:
```bash
pip install trafilatura requests beautifulsoup4
```

#### 2.4 AI 处理器实现

```python
# ingestor/ai_processor.py

import os
from typing import Dict, List
import openai  # 或其他AI SDK

class AIProcessor:
    """AI内容处理器"""
    
    def __init__(self):
        self.api_key = os.getenv('ZHIPU_API_KEY')  # 或 OPENAI_API_KEY
    
    def summarize(self, title: str, content: str) -> str:
        """生成文章摘要"""
        prompt = f"""
        请为以下文章生成一段200字以内的中文摘要：
        
        标题：{title}
        
        内容：{content[:3000]}  # 只取前3000字，避免token超限
        
        要求：
        1. 简洁明了，突出核心观点
        2. 用中文输出
        3. 不要包含"这篇文章"、"本文"等词汇
        4. 控制在200字以内
        
        摘要：
        """
        
        # 调用 AI API
        response = self._call_ai(prompt)
        return response.strip()
    
    def classify(self, title: str, content: str) -> Dict[str, List[str]]:
        """智能分类"""
        prompt = f"""
        请分析以下文章，输出分类信息：
        
        标题：{title}
        内容：{content[:2000]}
        
        可选分类：
        - 分类(category): hot(热门)/deep(深度)/new(新品)/breaking(突发)
        - 标签(tags): AI绘画/LLM/产品发布/研究/工具/安全/伦理/商业
        
        输出格式（JSON）：
        {{
            "category": "hot",
            "tags": ["LLM", "产品发布"]
        }}
        """
        
        response = self._call_ai(prompt)
        # 解析 JSON 响应
        return self._parse_json(response)
    
    def _call_ai(self, prompt: str) -> str:
        """调用AI API"""
        # 这里集成智谱/OpenAI/Claude等
        # 示例使用智谱
        import zhipuai
        zhipuai.api_key = self.api_key
        response = zhipuai.model_api.invoke(
            model="chatglm_pro",
            prompt=[{"role": "user", "content": prompt}]
        )
        return response['data']['choices'][0]['content']
```

#### 2.5 处理流程

```python
# ingestor/main.py - 修改后的流程

async def process_article(url: str, title: str, description: str):
    """处理单篇文章"""
    
    # 1. 检查数据库是否已存在
    existing = await check_existing(url)
    if existing:
        return existing
    
    # 2. 抓取完整内容
    fetcher = ContentFetcher()
    content = await fetcher.fetch_content(url)
    
    if not content:
        # 抓取失败，使用 RSS 的 description
        content = description
        summary = description[:200] if description else ""
        category = "new"  # 默认分类
        tags = []
    else:
        # 3. AI 处理
        processor = AIProcessor()
        summary = processor.summarize(title, content)
        classification = processor.classify(title, content)
        category = classification['category']
        tags = classification['tags']
    
    # 4. 保存到数据库
    article = ArticleModel(
        id=generate_id(),
        title=title,
        url=url,
        content=content,
        summary=summary,
        category=category,
        tags=tags,
        source=detect_source(url),
        # ...
    )
    
    await save_to_db(article)
    return article
```

---

### Phase 3: 分类系统设计

#### 3.1 规则映射（快速实现）

先不用AI，用规则快速分类：

```python
# ingestor/classifier.py

CATEGORY_RULES = {
    'breaking': ['突发', '紧急', '刚刚', '重磅', '震惊', '紧急发布'],
    'hot': ['热门', '热议', ' trending', '火了', '爆火', '刷屏'],
    'new': ['发布', '新品', '推出', '上线', '问世', '亮相', '官宣'],
    'deep': ['研究', '论文', '深度', '分析', '解读', '综述', '技术细节']
}

def classify_by_rules(title: str, content: str) -> str:
    """基于规则分类"""
    text = (title + ' ' + content).lower()
    
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in text for kw in keywords):
            return category
    
    return 'new'  # 默认分类

TAG_RULES = {
    'AI绘画': ['midjourney', 'dalle', 'stable diffusion', '绘画', '生图', '图像生成'],
    'LLM': ['gpt', 'llama', 'claude', '大模型', '语言模型', 'chatgpt'],
    '产品发布': ['发布', '新品', '推出', '上线', 'v1.', 'v2.', '版本'],
    '研究': ['论文', 'arxiv', 'research', '研究', 'novel', 'method'],
    '工具': ['工具', 'plugin', '插件', '扩展', 'cursor', 'ide'],
    '安全': ['安全', '风险', '漏洞', '隐私', '攻击', '防护'],
    '商业': ['融资', '收购', '财报', '市场', '商业', '投资']
}

def extract_tags(title: str, content: str) -> List[str]:
    """基于规则提取标签"""
    text = (title + ' ' + content).lower()
    tags = []
    
    for tag, keywords in TAG_RULES.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    
    return tags[:3]  # 最多3个标签
```

#### 3.2 AI 分类（进阶）

在规则分类基础上，用AI提升准确性：

```python
async def classify_article(title: str, content: str) -> Dict:
    """混合分类：规则 + AI"""
    # 先用规则快速分类
    category = classify_by_rules(title, content)
    tags = extract_tags(title, content)
    
    # 如果内容足够长，用AI优化
    if len(content) > 500:
        try:
            ai_result = await ai_classify(title, content)
            category = ai_result.get('category', category)
            tags = ai_result.get('tags', tags)
        except:
            pass  # AI失败时回退到规则
    
    return {'category': category, 'tags': tags}
```

---

## 实施建议

### 今天就能做的（1小时）

1. **先用 description 填充 content**
   ```python
   # 修改 ingestor/main.py
   content = item.get('description', '')
   ```

2. **添加简单分类**
   ```python
   # 使用上面的规则分类
   from classifier import classify_by_rules, extract_tags
   
   category = classify_by_rules(title, content)
   tags = extract_tags(title, content)
   ```

### 本周实施（2-3天）

1. 集成 `trafilatura` 抓取内容
2. 添加 AI 总结（使用智谱 API）
3. 优化分类准确性
4. 处理抓取失败的情况

### 成本考虑

**AI API 费用**（按100篇文章/天计算）：
- 智谱 GLM-4: ~0.1元/篇 × 100 = 10元/天
- OpenAI GPT-4: ~$0.002/篇 × 100 = $0.2/天

**优化策略**:
- 只对新文章调用AI
- 内容短的直接规则分类
- 批量处理减少API调用

---

## 下一步行动

您希望：
1. **先用现有 description 快速上线**（今天完成）
2. **直接实施完整抓取方案**（2-3天）
3. **先设计分类规则**（1小时）

请告诉我您的选择，我立即开始实施！
