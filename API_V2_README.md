# 后端 API v2 设计完成

## 📋 已完成的工作

### 1. 数据模型 (`api/v2/models.py`)
- ✅ `ArticleModel` - 完整匹配前端 Article 类型
- ✅ 请求/响应模型（ArticleListRequest, ArticleListResponse 等）
- ✅ 枚举类型（ArticleCategory, ArticleSource, TimeFilter, SortOption）
- ✅ 统一响应格式（BaseResponse 及子类）

### 2. 数据转换工具 (`api/v2/utils/`)
- ✅ `ArticleTransformer` - 将 Markdown 文件转换为 ArticleModel
  - ID 生成（MD5 hash）
  - Category 推断
  - Tags 提取
  - ViewCount/CommentCount 生成
  - Source 标准化

- ✅ `CategoryClassifier` - 分类推断工具
  - 基于关键词匹配
  - 基于来源匹配
  - 特殊规则优先级
  - 批量分类支持

- ✅ `TagExtractor` - 标签提取工具
  - 预定义标签库（25+ 标签）
  - 关键词提取（NLP 简单版）
  - 标签搜索
  - 热门标签查询

### 3. API 端点 (`api/v2/routes.py`)
- ✅ `GET /api/v2/articles` - 文章列表（完整筛选和排序）
  - keyword: 关键词搜索
  - timeRange: today/yesterday/week/month
  - sources: 来源列表
  - tags: 标签列表
  - sortBy: hot/newest/relevant/comments
  - page/pageSize: 分页
  - 自动回溯加载历史数据

- ✅ `GET /api/v2/suggestions` - 搜索建议
  - trending: 热门搜索
  - recent: 最近搜索
  - 支持查询词匹配

- ✅ `GET /api/v2/categories` - 分类列表
  - hot/deep/new/breaking
  - emoji 和描述

- ✅ `GET /api/v2/sources` - 来源列表
  - 动态统计各来源文章数
  - 按数量排序
  - 自动扫描所有可用数据目录

- ✅ `GET /api/v2/stats` - 统计信息
  - 今日统计
  - 总计统计
  - 自动扫描所有可用数据目录

- ✅ `GET /api/v2/health` - 健康检查
  - 服务状态
  - 版本信息

### 4. 缓存机制 (`api/v2/utils/cache.py`)
- ✅ `MemoryCache` - 5 分钟内存缓存
- ✅ `DiskCache` - 24 小时磁盘缓存
- ✅ `CacheManager` - 统一缓存管理

### 4. 路由集成 (`api/main.py`)
- ✅ 添加 v2 路由注册
- ✅ 保持 v1 接口向后兼容

### 5. 文档
- ✅ `docs/API_V2_DESIGN.md` - API 设计文档
- ✅ `docs/FRONTEND_INTEGRATION.md` - 前端集成指南

---

## 📁 文件结构

```
ai-daily-collector/
├── api/
│   ├── main.py              # 修改：添加 v2 路由注册
│   └── v2/                # 新增：API v2 模块
│       ├── __init__.py
│       ├── models.py         # 数据模型
│       ├── routes.py        # API 端点
│       └── utils/           # 工具模块
│           ├── __init__.py
│           ├── article_transformer.py
│           ├── category_classifier.py
│           └── tag_extractor.py
└── docs/
    ├── API_V2_DESIGN.md        # 新增：API 设计文档
    └── FRONTEND_INTEGRATION.md  # 新增：前端集成指南
```

---

## 🔧 后端启动

### 开发环境

```bash
cd /Users/young/xiaobailong/ai-code/ai-daily-collector

# 直接运行
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 部署

```bash
docker-compose up -d
```

---

## 🧪 API 测试

### 1. 测试文章列表

```bash
# 基础请求
curl "http://localhost:8000/api/v2/articles"

# 带筛选
curl "http://localhost:8000/api/v2/articles?keyword=GPT&sources=openai,google&sortBy=hot&page=1&pageSize=10"
```

### 2. 测试搜索建议

```bash
curl "http://localhost:8000/api/v2/suggestions?q=GPT"
```

### 3. 测试分类列表

```bash
curl "http://localhost:8000/api/v2/categories"
```

### 4. 测试来源列表

```bash
curl "http://localhost:8000/api/v2/sources"
```

### 5. 测试统计信息

```bash
curl "http://localhost:8000/api/v2/stats"
```

---

## 📊 数据转换示例

### 输入（Markdown 文件）

```markdown
---
title: "ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval"
source: "ArXiv AI"
original_url: "http://arxiv.org/abs/2601.23285v1"
date: "2026-02-03"
---

# ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval

**来源**: ArXiv AI | **原文**: [链接](http://arxiv.org/abs/2601.23285v1)

## 中文总结

本文提出ShotFinder，一种基于网络搜索的想象驱动开放域视频片段检索方法...
```

### 输出（API v2 响应）

```json
{
  "id": "arxiv-a1b2c3d4",
  "title": "ShotFinder: Imagination-Driven Open-Domain Video Shot Retrieval",
  "summary": "本文提出ShotFinder，一种基于网络搜索的想象驱动开放域视频片段检索方法...",
  "category": "deep",
  "source": "arxiv",
  "publishedAt": "2026-02-03T00:00:00Z",
  "viewCount": 1234,
  "commentCount": 32,
  "tags": ["研究", "视频", "LLM"],
  "url": "http://arxiv.org/abs/2601.23285v1"
}
```

---

## 🔄 前端对接

### 修改 `hooks/useArticles.ts`

将 mock 数据替换为 API 调用：

```typescript
const fetchArticles = useCallback(async () => {
  setLoading(true);
  setError(null);

  try {
    const params = new URLSearchParams({
      timeRange: filters?.timeRange || 'today',
      sortBy: filters?.sortBy || 'hot',
      page: '1',
      pageSize: '20',
    });

    if (filters?.keyword) params.append('keyword', filters.keyword);
    if (filters?.sources?.length) params.append('sources', filters.sources.join(','));
    if (filters?.tags?.length) params.append('tags', filters.tags.join(','));

    const response = await fetch(`http://localhost:8000/api/v2/articles?${params}`);
    const result = await response.json();

    if (result.success && result.data) {
      setArticles(result.data.articles);
    }
  } catch (err) {
    setError(err instanceof Error ? err : new Error('Unknown error'));
  } finally {
    setLoading(false);
  }
}, [filters]);
```

### 其他 Hooks 需要创建

- `useSearchSuggestions.ts` - 搜索建议
- `useCategories.ts` - 分类列表（可选，前端已硬编码）
- `useSources.ts` - 来源列表（可选，前端已硬编码）

---

## 📝 待办事项

### Phase 1: 核心集成
- [ ] 修改前端 `useArticles` hook 集成 API v2
- [ ] 添加环境变量配置（API_BASE_URL）
- [ ] 测试筛选和排序功能

### Phase 2: 增强功能
- [ ] 实现搜索建议功能
- [ ] 添加错误处理和重试逻辑
- [ ] 实现加载状态优化

### Phase 3: 数据优化
- [ ] 实现真实的 ViewCount/CommentCount 数据来源
- [ ] 优化 Category 推断准确率
- [ ] 添加更多预定义标签

### Phase 4: 性能优化
- [ ] 添加 API 响应缓存
- [ ] 实现分页预加载
- [ ] 优化数据转换性能

---

## ⚠️ 注意事项

1. **Python 依赖**：确保安装了 FastAPI, Uvicorn, Pydantic
2. **数据目录**：确保 `/ai/articles/summary/` 目录存在且有数据
3. **CORS**：后端已配置允许所有来源
4. **向后兼容**：API v1 接口保持不变

---

## 📞 问题反馈

如有问题，请提交 Issue 或查看文档：
- `docs/API_V2_DESIGN.md` - API 设计文档
- `docs/FRONTEND_INTEGRATION.md` - 前端集成指南
