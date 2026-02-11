# AI Daily Collector 后端 API 设计方案

## 📋 前端需求分析

### 1. Article 数据结构

```typescript
interface Article {
  id: string;                    // 文章唯一标识
  title: string;                  // 文章标题
  summary: string;                // 中文总结
  category: 'hot' | 'deep' | 'new' | 'breaking';  // 分类
  source: ArticleSource;          // 来源（枚举）
  publishedAt: string;            // ISO 日期时间
  viewCount: number;              // 浏览数
  commentCount: number;           // 评论数
  tags: string[];                // 标签数组
  thumbnail?: string;             // 缩略图 URL（可选）
  url?: string;                  // 原文链接（可选）
}
```

### 2. FilterState 筛选参数

```typescript
interface FilterState {
  keyword?: string;                      // 关键词搜索
  timeRange: 'today' | 'yesterday' | 'week' | 'month';
  sources: ArticleSource[];              // 来源筛选数组
  tags: string[];                        // 标签筛选数组
  sortBy: 'hot' | 'newest' | 'relevant' | 'comments';
}
```

### 3. 搜索建议

```typescript
interface SearchSuggestions {
  trending: Array<{ text: string; icon: string }>;   // 热门搜索
  recent: Array<{ text: string; icon: string }>;     // 最近搜索
}
```

---

## 🔧 后端接口设计

### API v2（面向前端）

#### 1. 文章列表

```
GET /api/v2/articles

Query Parameters:
  - keyword: string (optional)     关键词搜索
  - timeRange: 'today' | 'yesterday' | 'week' | 'month' (required, default: 'today')
  - sources: string[] (optional)   来源列表，如 openai,google,anthropic
  - tags: string[] (optional)     标签列表，如 LLM,GPT-4,AI绘画
  - sortBy: 'hot' | 'newest' | 'relevant' | 'comments' (required, default: 'hot')
  - page: int (required, default: 1)
  - pageSize: int (required, default: 20, max: 100)

Response:
{
  "success": true,
  "data": {
    "date": "2026-02-10",
    "timeRange": "today",
    "total": 45,
    "page": 1,
    "pageSize": 20,
    "articles": [
      {
        "id": "arxiv-260123456",
        "title": "ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval",
        "summary": "本文提出ShotFinder...",
        "category": "hot",
        "source": "arxiv",
        "publishedAt": "2026-02-10T14:30:00Z",
        "viewCount": 2340,
        "commentCount": 45,
        "tags": ["LLM", "视频", "研究"],
        "url": "http://arxiv.org/abs/260123456"
      }
    ]
  }
}
```

#### 2. 搜索建议

```
GET /api/v2/suggestions

Query Parameters:
  - q: string (optional)  查询词

Response:
{
  "success": true,
  "data": {
    "trending": [
      { "text": "GPT-4", "icon": "🤖" },
      { "text": "Claude", "icon": "🧠" },
      { "text": "AI绘画", "icon": "🎨" }
    ],
    "recent": [
      { "text": "多模态模型", "icon": "🔍" }
    ]
  }
}
```

#### 3. 分类列表

```
GET /api/v2/categories

Response:
{
  "success": true,
  "data": [
    {
      "id": "hot",
      "name": "热门",
      "emoji": "🔥",
      "description": "高热度内容"
    },
    {
      "id": "deep",
      "name": "深度",
      "emoji": "📰",
      "description": "深度研究内容"
    },
    {
      "id": "new",
      "name": "新品",
      "emoji": "🆕",
      "description": "最新发布内容"
    },
    {
      "id": "breaking",
      "name": "突发",
      "emoji": "⚡",
      "description": "突发新闻"
    }
  ]
}
```

#### 4. 来源列表

```
GET /api/v2/sources

Response:
{
  "success": true,
  "data": [
    {
      "id": "openai",
      "name": "OpenAI",
      "count": 12
    },
    {
      "id": "google",
      "name": "Google AI",
      "count": 8
    },
    {
      "id": "anthropic",
      "name": "Anthropic",
      "count": 5
    },
    {
      "id": "mit",
      "name": "MIT Tech Review",
      "count": 3
    },
    {
      "id": "arxiv",
      "name": "ArXiv AI",
      "count": 15
    }
  ]
}
```

#### 5. 统计信息

```
GET /api/v2/stats

Response:
{
  "success": true,
  "data": {
    "today": {
      "date": "2026-02-10",
      "articles": 45,
      "views": 12500,
      "comments": 320
    },
    "total": {
      "articles": 1234,
      "sources": 8,
      "categories": 4
    }
  }
}
```

---

## 📊 数据转换逻辑

### 1. Category 推断规则

| 原分类 | 新 Category | 规则 |
|--------|-------------|------|
| 大厂人物 | hot | 包含 OpenAI/Anthropic/Google 关键词 |
| Agent工作流 | hot | 包含 agent/workflow/MCP 关键词 |
| 编程助手 | new | 包含 cursor/copilot/IDE 关键词 |
| 内容生成 | breaking | 包含 image/video/audio 生成 |
| 工具生态 | deep | 包含 SDK/framework 关键词 |
| 安全风险 | breaking | 包含 security/vulnerability |
| ArXiv 论文 | deep | 来源为 ArXiv |
| Product Hunt | new | 来源为 Product Hunt |

### 2. Tags 提取规则

从标题和总结中提取关键词：
- 预定义标签库（LLM, GPT-4, Claude, AI绘画, etc.）
- 基于内容的 NLP 关键词提取（可选）
- 限制最多 5 个标签

### 3. ViewCount & CommentCount 生成策略

**方案 A - 基于热度评分**
```python
viewCount = int(hot_score * 100 + random.randint(0, 500))
commentCount = int(viewCount * 0.05)
```

**方案 B - 从文件读取（如果存储）**
- 从 `daily.json` 读取实际数据
- 或从数据库/缓存读取

### 4. ID 生成规则

```python
# 使用源名 + 时间戳 + hash
import hashlib
def generate_id(source: str, title: str) -> str:
    hash_str = hashlib.md5(f"{source}:{title}".encode()).hexdigest()[:8]
    return f"{source.lower()}-{hash_str}"
```

---

## 🔄 兼容性处理

### 向后兼容
- `/api/v1/*` 接口保持不变
- 新增 `/api/v2/*` 接口用于前端

### 渐进式迁移
- 前端使用 `/api/v2/articles`
- 后端内部统一数据处理逻辑

---

## 🚀 实现优先级

### Phase 1: 核心功能（高优先级）
- [ ] `GET /api/v2/articles` - 文章列表（完整数据结构）
- [ ] Category 推断逻辑
- [ ] Tags 提取逻辑
- [ ] 排序功能实现

### Phase 2: 增强功能（中优先级）
- [ ] `GET /api/v2/suggestions` - 搜索建议
- [ ] `GET /api/v2/categories` - 分类列表
- [ ] `GET /api/v2/sources` - 来源列表
- [ ] `GET /api/v2/stats` - 统计信息

### Phase 3: 优化功能（低优先级）
- [ ] 缓存机制
- [ ] 分页优化
- [ ] 搜索性能优化
- [ ] ViewCount/CommentCount 真实数据来源

---

## 📝 代码修改清单

### 新增文件
- `api/v2/endpoints.py` - API v2 端点
- `api/v2/models.py` - 数据模型
- `api/v2/utils/article_transformer.py` - 文章数据转换工具
- `api/v2/utils/category_classifier.py` - 分类推断工具
- `api/v2/utils/tag_extractor.py` - 标签提取工具

### 修改文件
- `api/main.py` - 注册 v2 路由
- `requirements.txt` - 添加依赖（如需要 NLP 库）

---

## 🎯 数据流示例

```
Article File (Markdown)
    ↓ parse_article_file()
Raw Article Data
    ↓ ArticleTransformer.transform()
    ↓ - Generate ID
    ↓ - Infer Category
    ↓ - Extract Tags
    ↓ - Generate viewCount/commentCount
Enhanced Article Data
    ↓ Apply Filters & Sort
    ↓ Return JSON Response
Frontend Article Object
```

---

## 🔍 测试用例

```python
# 1. 测试文章列表
GET /api/v2/articles?timeRange=today&sortBy=hot&page=1&pageSize=20
assert response["success"] == True
assert len(response["data"]["articles"]) <= 20

# 2. 测试筛选
GET /api/v2/articles?sources=openai,google&tags=LLM,GPT-4
assert all(a["source"] in ["openai", "google"] for a in articles)

# 3. 测试排序
GET /api/v2/articles?sortBy=hot
assert articles[0]["viewCount"] >= articles[-1]["viewCount"]

# 4. 测试搜索建议
GET /api/v2/suggestions?q=GPT
assert any("GPT" in s["text"] for s in response["data"]["trending"])
```
