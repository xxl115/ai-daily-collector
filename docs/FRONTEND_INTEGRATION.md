# 前端集成指南

## 📦 后端 API 接口

### 基础 URL
- 开发环境: `http://localhost:8000`
- 生产环境: `https://your-domain.com`

### 可用端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v2/articles` | GET | 获取文章列表 |
| `/api/v2/suggestions` | GET | 获取搜索建议 |
| `/api/v2/categories` | GET | 获取分类列表 |
| `/api/v2/sources` | GET | 获取来源列表 |
| `/api/v2/stats` | GET | 获取统计信息 |

---

## 🔗 前端集成步骤

### 1. 修改 `hooks/useArticles.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import type { Article, FilterState } from '@/lib/types';

// API 基础 URL
const API_BASE_URL = 'http://localhost:8000';

interface UseArticlesReturn {
  articles: Article[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useArticles(filters?: FilterState): UseArticlesReturn {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchArticles = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 构建查询参数
      const params = new URLSearchParams({
        timeRange: filters?.timeRange || 'today',
        sortBy: filters?.sortBy || 'hot',
        page: '1',
        pageSize: '20',
      });

      if (filters?.keyword) params.append('keyword', filters.keyword);
      if (filters?.sources?.length) params.append('sources', filters.sources.join(','));
      if (filters?.tags?.length) params.append('tags', filters.tags.join(','));

      // 请求 API
      const response = await fetch(`${API_BASE_URL}/api/v2/articles?${params}`);
      if (!response.ok) throw new Error('Failed to fetch articles');

      const result = await response.json();

      if (result.success && result.data) {
        setArticles(result.data.articles);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  return {
    articles,
    loading,
    error,
    refetch: fetchArticles,
  };
}
```

### 2. 修改 `hooks/useSearchSuggestions.ts`（新建）

```typescript
import { useState, useEffect } from 'react';
import type { SearchSuggestion } from '@/lib/types';

const API_BASE_URL = 'http://localhost:8000';

interface SearchSuggestions {
  trending: SearchSuggestion[];
  recent: SearchSuggestion[];
}

export function useSearchSuggestions(query?: string) {
  const [suggestions, setSuggestions] = useState<SearchSuggestions>({
    trending: [],
    recent: [],
  });

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const params = query ? `?q=${encodeURIComponent(query)}` : '';
        const response = await fetch(`${API_BASE_URL}/api/v2/suggestions${params}`);
        const result = await response.json();

        if (result.success && result.data) {
          setSuggestions(result.data);
        }
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
      }
    };

    fetchSuggestions();
  }, [query]);

  return suggestions;
}
```

### 3. 修改 `hooks/useCategories.ts`（新建）

```typescript
import { useState, useEffect } from 'react';
import type { CategoryBadgeConfig } from '@/lib/constants';

const API_BASE_URL = 'http://localhost:8000';

export function useCategories() {
  const [categories, setCategories] = useState<CategoryBadgeConfig[]>([]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v2/categories`);
        const result = await response.json();

        if (result.success && result.data) {
          setCategories(result.data);
        }
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    };

    fetchCategories();
  }, []);

  return categories;
}
```

### 4. 修改 `hooks/useSources.ts`（新建）

```typescript
import { useState, useEffect } from 'react';
import type { Source } from '@/lib/types';

const API_BASE_URL = 'http://localhost:8000';

export function useSources() {
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v2/sources`);
        const result = await response.json();

        if (result.success && result.data) {
          setSources(result.data);
        }
      } catch (err) {
        console.error('Failed to fetch sources:', err);
      }
    };

    fetchSources();
  }, []);

  return sources;
}
```

---

## 📝 类型定义更新

在 `lib/types/index.ts` 中确保以下类型定义完整：

```typescript
/** 分类信息 */
export interface CategoryInfo {
  id: string;
  name: string;
  emoji: string;
  description: string;
}

/** 来源信息 */
export interface SourceInfo {
  id: string;
  name: string;
  count: number;
}
```

---

## 🧪 测试 API

### 测试文章列表

```bash
# 基础请求
curl "http://localhost:8000/api/v2/articles"

# 带筛选
curl "http://localhost:8000/api/v2/articles?keyword=GPT&sources=openai,google&sortBy=hot"

# 分页
curl "http://localhost:8000/api/v2/articles?page=2&pageSize=10"
```

### 测试搜索建议

```bash
curl "http://localhost:8000/api/v2/suggestions?q=GPT"
```

### 测试分类列表

```bash
curl "http://localhost:8000/api/v2/categories"
```

### 测试来源列表

```bash
curl "http://localhost:8000/api/v2/sources"
```

---

## 🔧 环境变量配置

在 `.env.local` 文件中：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

在生产环境：

```env
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
```

---

## ⚠️ 注意事项

### 1. CORS 配置

后端已配置允许所有来源：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 数据格式

后端返回的所有日期格式为 **ISO 8601**：
```json
"publishedAt": "2026-02-10T14:30:00Z"
```

### 3. 错误处理

后端返回的统一格式：
```json
{
  "success": false,
  "message": "错误信息"
}
```

### 4. 分页

- `page`: 从 1 开始
- `pageSize`: 最大 100
- `total`: 总文章数量

---

## 🚀 部署

### 后端部署

```bash
cd /Users/young/xiaobailong/ai-code/ai-daily-collector

# 使用 Docker
docker-compose up -d

# 或直接运行
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 前端配置

确保 `.env.local` 中的 API URL 正确指向后端服务。

---

## 📊 API 响应示例

### 文章列表响应

```json
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
        "id": "arxiv-a1b2c3d4",
        "title": "ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval",
        "summary": "本文提出ShotFinder，一种基于网络搜索的想象驱动开放域视频片段检索方法...",
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

### 搜索建议响应

```json
{
  "success": true,
  "data": {
    "trending": [
      { "text": "GPT-4", "icon": "🤖" },
      { "text": "Claude", "icon": "🧠" }
    ],
    "recent": [
      { "text": "Cursor IDE", "icon": "⌨️" }
    ]
  }
}
```

---

## 🔄 向后兼容

API v1 接口保持不变，可以继续使用：

| 端点 | 说明 |
|------|------|
| `/api/v1/articles` | 原有接口 |
| `/api/v1/report/today` | 日报接口 |
| `/api/v1/categories` | 分类接口 |
| `/api/v1/stats` | 统计接口 |
| `/rss` | RSS Feed |

前端可以逐步从 v1 迁移到 v2。
