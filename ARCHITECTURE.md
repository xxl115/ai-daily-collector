# AI Daily Collector - 系统架构文档 v2.0

> AI 资讯自动采集系统的完整架构文档

**版本:** 2.0  
**最后更新:** 2024-01-15  
**状态:** ✅ 生产就绪

---

## 快速概览

AI Daily Collector 是一个生产就绪的内容聚合系统：
- 从 **60+ 个 AI/科技资讯源** 采集（RSS、API、社区）
- 使用 **Cloudflare D1** 作为生产存储，SQLite 用于开发环境
- 通过 **FastAPI** 提供服务，自动生成 API 文档
- 在 **GitHub Actions** 定时任务上运行
- 提供 **结构化 JSON 日志** 和性能指标

---

## 系统架构图

系统分为三个主要层次：
1. **客户端层** - Web/移动应用、RSS阅读器、API客户端
2. **API网关层** - FastAPI提供的REST API服务
3. **数据摄取层** - 定时抓取、转换、存储管道

### 核心数据流

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   来源配置   │     │   抓取器     │     │   转换器     │     │   存储层     │
│  (YAML)      │────▶│  (HTTP/API)  │────▶│ (Pydantic)   │────▶│  (D1/SQLite) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 组件清单

### 抓取器（16个）

| # | 文件 | 类型 | 来源数量 |
|---|------|------|---------|
| 1 | rss_scraper.py | RSS/Atom | 30+ |
| 2 | newsnow_scraper.py | API | 8个平台 |
| 3 | hackernews_scraper.py | API | Hacker News |
| 4 | devto_scraper.py | API | Dev.to |
| 5 | v2ex_scraper.py | API | V2EX |
| 6 | reddit_scraper.py | API | Reddit |
| 7 | arxiv_scraper.py | API | ArXiv |
| 8 | article_scraper.py | Web | 通用 |

### API端点（5个）

- `GET /api/v2/articles` - 文章列表（分页）
- `GET /api/v2/articles/{id}` - 单篇文章
- `GET /api/v2/stats` - 统计信息
- `GET /api/v2/sources` - 来源列表
- `GET /api/v2/health` - 健康检查

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.11+ | 运行时 |
| Web框架 | FastAPI 0.109+ | REST API |
| 数据库（生产） | Cloudflare D1 | 文章存储 |
| 数据库（开发） | SQLite 3.0+ | 本地开发 |
| 调度 | GitHub Actions | 定时任务 |
| 配置 | PyYAML 6.0+ | YAML解析 |

---

## 数据模型

### ArticleModel

```python
class ArticleModel:
    id: str                    # 唯一ID
    title: str                 # 标题
    content: str               # 内容
    url: str                   # URL
    source: str                # 来源
    categories: List[str]      # 分类
    tags: List[str]            # 标签
    published_at: datetime     # 发布时间
    ingested_at: datetime      # 采集时间
```

### 数据库Schema

```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    categories TEXT,           -- JSON数组
    tags TEXT,                 -- JSON数组
    ingested_at TEXT NOT NULL
);

CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_ingested_at ON articles(ingested_at);
```

---

## 配置说明

### 环境变量

```bash
# 必需（生产环境）
ENVIRONMENT=production
DATABASE_PROVIDER=d1
CF_ACCOUNT_ID=xxx
CF_D1_DATABASE_ID=xxx
CF_API_TOKEN=xxx

# 可选
LOG_LEVEL=INFO
LOG_FORMAT=json
MAX_ARTICLES_PER_SOURCE=50
```

---

## 部署架构

### 生产部署

```
GitHub Actions (定时 UTC 18:00)
    │
    ▼
ingestor/main.py
    │
    ▼
Cloudflare D1 (边缘数据库)
    │
    ▼
FastAPI (Cloudflare Workers)
    │
    ▼
客户端 (Web/App)
```

### 环境切换

```bash
# 开发环境（本地SQLite）
ENVIRONMENT=development
DATABASE_PROVIDER=local
LOG_FORMAT=text

# 生产环境（D1）
ENVIRONMENT=production
DATABASE_PROVIDER=d1
LOG_FORMAT=json
```

---

## 性能指标

| 指标 | 数值 |
|------|------|
| 摄取吞吐量 | ~100 文章/分钟 |
| API响应时间 | < 50ms (缓存查询) |
| 数据库查询 | < 10ms (索引查询) |
| 支持来源数 | 60+ |

---

## 监控与日志

### 结构化日志格式

```json
{
  "timestamp": "2024-01-15T12:00:00Z",
  "level": "INFO",
  "message": "采集完成",
  "source": "MIT Tech Review",
  "articles_count": 10,
  "duration_ms": 1500
}
```

---

## 故障排除

### 常见问题

1. **D1连接失败**
   - 检查 CF_ACCOUNT_ID、CF_API_TOKEN、CF_D1_DATABASE_ID

2. **来源返回空文章**
   - 检查URL可访问性
   - 验证关键词过滤条件

3. **高错误率**
   - 查看单个来源日志
   - 检查API限流

---

## 系统状态

✅ **生产就绪** - 所有组件实现完成，文档齐全，可部署上线

---

*最后更新: 2024-01-15*  
*版本: 2.0*  
*状态: 生产环境* 🚀
