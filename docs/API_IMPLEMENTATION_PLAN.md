# 前后端 API 集成实施方案

## 文档信息
- **创建日期**: 2026-02-13
- **文档状态**: 实施中
- **相关项目**:
  - 后端: `ai-daily-collector`
  - 前端: `ai-daily-web`

---

## 1. 当前状态分析

### 1.1 接口对比表

| 接口 | 前端期望 | 后端现状 | 状态 | 优先级 |
|------|---------|---------|------|--------|
| `GET /api/v2/articles` | 支持 keyword/timeRange/sources/tags/sortBy/page/pageSize 查询 | 仅支持 source 筛选和分页 | ❌ 不匹配 | 🔴 高 |
| `GET /api/v2/sources` | 返回来源列表及文章数 | 已实现 | ✅ 可用 | 🟢 低 |
| `GET /api/v2/stats` | 返回 today/total 统计信息 | 返回 total/sources 统计 | ⚠️ 部分匹配 | 🟡 中 |
| `GET /api/v2/categories` | 返回分类列表（含emoji、描述等） | 未实现 | ❌ 缺失 | 🔴 高 |
| `GET /api/v2/suggestions?q=xxx` | 返回搜索建议（trending/recent） | 未实现 | ❌ 缺失 | 🟡 中 |

### 1.2 响应格式差异

#### 前端期望格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

#### 后端现状格式
```json
{
  "total": 0,
  "articles": [],
  "page": 1,
  "page_size": 20
}
```

**结论**: 需要统一响应格式，或前端适配后端格式。

### 1.3 数据字段差异

#### 前端 Article 类型
```typescript
interface Article {
  id: string;
  title: string;
  summary: string;
  category: string;        // 分类ID（hot/deep/new/breaking）
  source: string;
  publishedAt: string;     // ISO 8601 格式
  viewCount: number;       // 浏览量
  commentCount: number;    // 评论数
  tags: string[];
  url: string;
}
```

#### 后端 Article 模型
```python
class ArticleModel:
    id: str
    title: str
    content: str           # 前端用 summary
    url: str
    source: str
    categories: List[str]  # 前端用 category（单值）
    tags: List[str]
    published_at: datetime
    ingested_at: datetime
    # 缺失: viewCount, commentCount
```

---

## 2. 实施方案

### 方案选择

**方案 A**: 后端适配前端（推荐）
- 后端修改接口，完全匹配前端需求
- 优点: 前端无需改动，用户体验一致
- 缺点: 后端工作量较大

**方案 B**: 前端适配后端
- 前端修改 API 调用和数据处理
- 优点: 后端改动少
- 缺点: 部分功能可能无法实现

**决定**: 采用 **方案 A**，后端适配前端。

---

## 3. 详细实施计划

### Phase 1: API 响应格式标准化（第1-2天）

#### 任务清单
- [ ] 创建统一的 API 响应包装器
- [ ] 修改所有现有接口，包装为 `{success, message, data}` 格式
- [ ] 添加错误处理和错误消息
- [ ] 保持向后兼容（可选，通过 header 或参数控制）

#### 响应格式规范
```python
# 成功响应
{
    "success": True,
    "message": "获取成功",
    "data": {
        "total": 100,
        "articles": [...],
        "page": 1,
        "pageSize": 20
    }
}

# 错误响应
{
    "success": False,
    "message": "参数错误：page 必须是正整数",
    "data": None
}
```

#### 涉及文件
- `api/v2/routes_d1.py` - 修改响应格式
- `api/v2/models.py` - 添加响应模型

---

### Phase 2: 扩展文章列表接口（第2-4天）

#### 任务清单
- [ ] 实现关键词搜索（keyword）
- [ ] 实现时间范围筛选（timeRange: today/week/month）
- [ ] 实现多来源筛选（sources 逗号分隔）
- [ ] 实现标签筛选（tags）
- [ ] 实现排序功能（sortBy: hot/new）

#### 查询参数设计
```
GET /api/v2/articles?
    keyword=GPT&                  # 关键词搜索（标题+内容）
    timeRange=today&              # 时间范围：today/week/month/all
    sources=36氪,ArXiv&           # 来源筛选（逗号分隔）
    tags=AI,LLM&                  # 标签筛选（逗号分隔）
    sortBy=hot&                   # 排序：hot(热度)/new(最新)
    page=1&                       # 页码
    pageSize=20                   # 每页数量
```

#### 技术实现要点

**1. 关键词搜索**
```sql
SELECT * FROM articles 
WHERE title LIKE ? OR content LIKE ? OR summary LIKE ?
```

**2. 时间范围筛选**
```python
# today: 今天
# week: 最近7天
# month: 最近30天
# all: 全部

def get_time_range(time_range: str) -> tuple:
    now = datetime.now()
    if time_range == 'today':
        start = now.replace(hour=0, minute=0, second=0)
    elif time_range == 'week':
        start = now - timedelta(days=7)
    elif time_range == 'month':
        start = now - timedelta(days=30)
    else:
        return (None, None)
    return (start, now)
```

**3. 排序策略**
- `hot`: 按浏览量 + 评论数加权排序（需要添加这些字段）
- `new`: 按 `published_at` 倒序

---

### Phase 3: 新增缺失接口（第4-5天）

#### 3.1 分类列表接口

```
GET /api/v2/categories
```

**响应格式**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": [
    {
      "id": "hot",
      "name": "热门",
      "emoji": "🔥",
      "description": "高热度内容",
      "bgClass": "bg-primary/10",
      "textClass": "text-primary"
    },
    {
      "id": "deep",
      "name": "深度",
      "emoji": "📰",
      "description": "深度研究内容",
      "bgClass": "bg-secondary/10",
      "textClass": "text-secondary"
    },
    {
      "id": "new",
      "name": "新品",
      "emoji": "🆕",
      "description": "最新发布内容",
      "bgClass": "bg-green-100",
      "textClass": "text-green-600"
    },
    {
      "id": "breaking",
      "name": "突发",
      "emoji": "⚡",
      "description": "突发新闻",
      "bgClass": "bg-orange-100",
      "textClass": "text-orange-600"
    }
  ]
}
```

**实现方式**: 硬编码返回（分类是固定的），无需数据库查询。

#### 3.2 搜索建议接口

```
GET /api/v2/suggestions?q={query}
```

**响应格式**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "trending": [
      { "text": "GPT-4", "icon": "🤖" },
      { "text": "Claude", "icon": "🧠" },
      { "text": "AI绘画", "icon": "🎨" },
      { "text": "多模态模型", "icon": "👁️" }
    ],
    "recent": [
      { "text": "Cursor IDE", "icon": "⌨️" },
      { "text": "Gemini Ultra", "icon": "🔍" }
    ]
  }
}
```

**实现策略**:
- Phase 1: 硬编码热门关键词
- Phase 2: 从文章标签/标题提取高频词
- Phase 3: 基于用户搜索历史（需要添加搜索日志）

---

### Phase 4: 统计数据接口完善（第5天）

#### 当前问题
后端 `stats` 返回:
```json
{
  "total": 162,
  "sources": { "36氪": 30, "ArXiv": 15, ... }
}
```

前端期望:
```json
{
  "today": {
    "date": "2026-02-13",
    "articles": 12,
    "views": 3500,
    "comments": 120
  },
  "total": {
    "date": "2026-02-13",
    "articles": 162,
    "views": 12500,
    "comments": 320
  }
}
```

#### 任务清单
- [ ] 实现今日文章数统计
- [ ] 添加浏览量和评论数字段（先用默认值 0）
- [ ] 调整响应格式匹配前端需求

---

### Phase 5: 数据字段补充（第5-6天）

#### 需要添加的字段

**方案 1: 修改数据库表（推荐长期）**
```sql
ALTER TABLE articles ADD COLUMN view_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN comment_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN category TEXT;
```

**方案 2: 运行时计算/映射（快速实现）**
- `viewCount`: 随机生成或返回 0
- `commentCount`: 返回 0
- `category`: 从 `categories` 数组取第一个，或根据规则映射

#### 映射规则示例
```python
def map_category(categories: List[str], tags: List[str]) -> str:
    """将后端分类映射到前端分类"""
    # 优先级: breaking > hot > new > deep
    if any(kw in str(categories + tags) for kw in ['突发', '紧急', 'breaking']):
        return 'breaking'
    elif any(kw in str(tags) for kw in ['热门', 'hot', 'trending']):
        return 'hot'
    elif 'new' in categories or '新品' in tags:
        return 'new'
    else:
        return 'deep'
```

---

## 4. 实施优先级

### 🔴 高优先级（必须实现）
1. **API 响应格式标准化** - 前后端能正常通信
2. **文章列表查询扩展** - 基本筛选功能
3. **分类列表接口** - 前端首页需要

### 🟡 中优先级（建议实现）
4. **统计数据完善** - 首页统计展示
5. **搜索建议接口** - 搜索功能
6. **数据字段映射** - 分类显示

### 🟢 低优先级（可选）
7. 浏览量/评论数真实统计
8. 高级搜索功能
9. API 缓存优化

---

## 5. 接口变更记录

### 变更日志

#### v2.0 -> v2.1 (当前实施)
- ✅ 修复 D1 数据库连接问题
- ✅ 实现基础文章列表查询
- 🔄 响应格式标准化（进行中）
- 🔄 查询参数扩展（进行中）

#### v2.1 -> v2.2 (计划中)
- 新增 `/api/v2/categories` 接口
- 新增 `/api/v2/suggestions` 接口
- 完善 `/api/v2/stats` 接口

---

## 6. 测试计划

### 单元测试
- [ ] API 响应格式测试
- [ ] 查询参数解析测试
- [ ] 数据库查询测试

### 集成测试
- [ ] 前端调用端到端测试
- [ ] 性能测试（响应时间 < 500ms）
- [ ] 错误处理测试

### 验收标准
- [ ] 所有接口返回格式符合前端要求
- [ ] 文章列表支持所有筛选条件
- [ ] 首页能正常加载并显示文章
- [ ] 搜索功能正常工作

---

## 7. 风险与注意事项

### 技术风险
1. **D1 查询性能**: 复杂查询可能影响响应时间
   - 缓解: 添加索引，限制返回字段

2. **数据一致性**: 响应格式变更可能影响其他调用方
   - 缓解: 保持向后兼容，或通知所有调用方

3. **浏览量/评论数**: 暂时无法实现真实统计
   - 缓解: 先用默认值，后续添加统计服务

### 实施注意事项
1. 每次修改后需要重新部署 Workers
2. 修改数据库结构需要数据迁移
3. 关注 Workers 日志，及时处理错误

---

## 8. 相关文档

- [架构文档](./ARCHITECTURE.md)
- [问题排查记录](./DEBUGGING_LOG.md)
- [前端 API 客户端](../ai-daily-web/lib/api/client.ts)
- [前端类型定义](../ai-daily-web/lib/types)

---

**最后更新**: 2026-02-13  
**状态**: 实施计划中  
**负责人**: AI Daily Team
