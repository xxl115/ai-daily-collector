# Architecture All-in-One — AI 内容处理流水线（基线 A）

> **本文档是项目的唯一权威架构参考**  
> 其他 ARCHITECTURE*.md 文档已废弃，请以本文档为准

## 目录

1. [当前实现状态](#1-当前实现状态)
2. [核心数据流](#2-核心数据流)
   - [2.1 URL 抓取流程（ingestor）](#21-url-抓取流程ingestor)
3. [端到端数据契约](#3-端到端数据契约)
4. [数据落地与可追溯性](#4-数据落地与可追溯性)
5. [组件接口示例](#5-组件接口示例)
6. [运行与部署要点](#6-运行与部署要点)
7. [观测性与基线指标](#7-观测性与基线指标)
8. [错误处理与容错设计](#8-错误处理与容错设计)
9. [分类规则说明](#9-分类规则说明)
10. [演进路线与里程碑](#10-演进路线与里程碑)
11. [安全与合规](#11-安全与合规)
12. [API 接口契约](#12-api-接口契约)
13. [参考与关联](#13-参考与关联)
14. [数据示例](#14-数据示例)

---

## 1. 当前实现状态

| 组件/功能 | 状态 | 备注 | 完成度 |
|----------|------|------|--------|
| URL 抓取器（Ingestor） | ✅ 已实现 | `ingestor/main.py` + 7 种抓取器 | 100% |
| 来源配置 | ✅ 已实现 | `config/sources.yaml` | 100% |
| GitHub Actions 定时任务 | ✅ 已实现 | UTC 18:00 触发 | 100% |
| 本地文件存储 | ✅ 已实现 | `ai/articles/processed/*.json` | 100% |
| ContentProcessor 处理器 | ✅ 已实现 | `scripts/content_processor.py` | 100% |
| 提取器（Trafilatura/Jina） | ✅ 已实现 | 回退机制完整 | 100% |
| 摘要生成（Ollama） | ✅ 已实现 | 本地 LLM | 100% |
| 分类器（BGE） | ✅ 已实现 | 嵌入向量分类 | 100% |
| 日报生成 | ✅ 已实现 | `ai/daily/REPORT.md` | 100% |
| FastAPI 接口 | ✅ 已实现 | `api/main.py` | 100% |
| Cloudflare Workers | 🔄 进行中 | `api/v2/` 目录 | 30% |
| Dagster 编排层 | 📋 计划 | `dagster/` 目录待开发 | 0% |
| 错误处理降级 | ⚠️ 部分实现 | 需完善 metrics 写入 | 70% |
| 重试机制 | 📋 计划 | 需实现指数退避 | 0% |
| 限流策略 | 📋 计划 | 需实现速率限制 | 0% |
| 审计日志 | 📋 计划 | 需实现 | 0% |

---

## 2. 核心数据流

### 完整数据流（抓取 → 处理 → 输出）

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   来源配置           │     │   URL 抓取器         │     │   数据转换器        │
│   config/sources.yaml │────▶│   ingestor/main.py   │────▶│   transformers/     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                    │                            │
                                    ▼                            ▼
                           ┌─────────────────────┐     ┌─────────────────────┐
                           │   抓取器集合         │     │   ArticleModel      │
                           │   scrapers/*        │     │   数据模型          │
                           └─────────────────────┘     └─────────────────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────────┐
                                                       │   存储层             │
                                                       │   D1 / SQLite        │
                                                       └─────────────────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────────┐
                                                       │   批处理入口         │
                                                       │   ContentProcessor   │
                                                       └─────────────────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────────┐
                                                       │   本地 JSON 输出     │
                                                       │   ai/articles/      │
                                                       └─────────────────────┘
                                                                │
                                                                ▼
                                                       ┌─────────────────────┐
                                                       │   日报汇总           │
                                                       │   ai/daily/REPORT.md│
                                                       └─────────────────────┘
```

### 2.1 URL 抓取流程（ingestor）

#### 概述

URL 抓取是数据流的第一阶段，由 `ingestor/main.py` 负责从多种来源采集文章 URL 和元数据。

#### 抓取器清单

| 抓取器 | 类型 | 来源数量 | 实现文件 |
|--------|------|----------|----------|
| RSS 聚合 | RSS/Atom | 30+ | `scrapers/rss_scraper.py` |
| NewsNow | API | 8 平台 | `scrapers/newsnow_scraper.py` |
| Hacker News | API | 1 | `scrapers/hackernews_scraper.py` |
| Dev.to | API | 1 | `scrapers/devto_scraper.py` |
| V2EX | API | 1 | `scrapers/v2ex_scraper.py` |
| Reddit | API | 1 | `scrapers/reddit_scraper.py` |
| ArXiv | API | 1 | `scrapers/arxiv_scraper.py` |

#### 配置示例

```yaml
# config/sources.yaml
sources:
  - name: "MIT Tech Review"
    type: "rss"
    url: "https://www.technologyreview.com/feed/"
    enabled: true
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 20

  - name: "Hacker News AI"
    type: "hackernews"
    enabled: true
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 30

  - name: "ArXiv CS.AI"
    type: "arxiv"
    enabled: true
    filters:
      max_articles: 15
```

#### 支持的来源类型

| type 值 | 来源 | 说明 |
|---------|------|------|
| `rss` | RSS/Atom 订阅 | 通用 RSS 抓取 |
| `newsnow` | NewsNow | 聚合新闻平台 |
| `hackernews` | Hacker News | Algolia API |
| `devto` | Dev.to | 技术社区 |
| `v2ex` | V2EX | 中文技术社区 |
| `reddit` | Reddit | 子论坛 |
| `arxiv` | ArXiv | 学术论文 |
| `ai_blogs` | AI 博客 | RSS 订阅 |
| `tech_media` | 科技媒体 | RSS 订阅 |
| `youtube` | YouTube | 频道 RSS |
| `producthunt` | Product Hunt | 产品发布 |

#### 抓取流程

```
1. 加载配置
   └─→ ingestor/main.py 读取 config/sources.yaml

2. 遍历来源
   └─→ 对每个 enabled: true 的来源执行抓取

3. 调用对应抓取器
   └─→ fetch_{source_type}() 返回文章列表

4. 数据转换
   └─→ transformer/article_transformer.py 统一格式

5. 存储/输出
   └─→ 写入 D1/SQLite 或输出到文件
```

#### 命令行使用

```bash
# 完整抓取（写入数据库）
python -m ingestor.main

# 干跑模式（不写入数据库）
python -m ingestor.main --dry-run

# 只抓取特定类型
python -m ingestor.main --source-type rss

# 指定配置文件
python -m ingestor.main --config config/custom.yaml
```

#### 数据模型（Ingestor）

```python
class ArticleModel(BaseModel):
    id: str                    # 唯一ID（UUID）
    title: str                 # 标题
    url: str                   # 原文链接
    content: str               # 正文内容
    source: str                # 来源名称
    categories: List[str]      # 分类列表
    tags: List[str]            # 标签列表
    summary: Optional[str]     # AI 生成的摘要
    raw_markdown: Optional[str] # 原始 Markdown
    published_at: Optional[datetime] # 发布时间
    ingested_at: datetime     # 抓取时间
```

#### 与 ArticleProcessed 的关系

| ArticleModel 字段 | ArticleProcessed 字段 | 说明 |
|-------------------|----------------------|------|
| `id` | `id` | 唯一标识 |
| `url` | `url` | 原文链接 |
| `title` | `title` | 标题 |
| `content` | `content` | 正文内容 |
| `summary` | `summary` | AI 摘要 |
| `source` | `source` | 来源 |
| `categories` | `category` | 分类（列表转字符串） |
| `tags` | `tags` | 标签列表 |
| `published_at` | - | 保留字段（未使用） |
| `ingested_at` | `extracted_at` | 抓取/提取时间 |

### 数据流说明

| 阶段 | 输入 | 处理 | 输出 | 实现文件 |
|------|------|------|------|----------|
| 0. 来源配置 | YAML 文件 | 解析来源列表 | 来源配置 | `config/sources.yaml` |
| 1. URL 抓取 | 来源配置 | HTTP/API 调用 | 文章元数据列表 | `ingestor/scrapers/*` |
| 2. 数据转换 | 元数据 | 格式统一 | ArticleModel | `ingestor/transformers/*` |
| 3. 存储 | ArticleModel | 写入数据库 | D1/SQLite | `storage/*` |
| 4. 读取 | JSON/Markdown | 解析 URL 和标题 | ArticleInput 列表 | `content_processor.py` |
| 5. 内容提取 | URL | HTTP 抓取 + 解析 | 原始文本 | `scripts/extractors/*` |
| 6. 摘要生成 | 原始文本 | Ollama LLM 生成 | 摘要文本 | `scripts/summarizers/*` |
| 7. 分类 | 标题+摘要 | BGE 嵌入 + 分类 | category + tags | `scripts/classifiers/*` |
| 8. 持久化 | 处理结果 | JSON 写入 | `*.json` 文件 | `content_processor.py` |
| 9. 汇总 | JSON 文件列表 | 日报模板渲染 | `REPORT.md` | `report_generator.py` |

### ⚠️ 重要说明

- **URL 抓取是独立流程**：使用 `ingestor/main.py` 从各来源采集文章
- **内容提取是后续流程**：使用 `scripts/content_processor.py` 从已采集的 URL 提取正文
- **数据存储**：抓取结果存入 D1/SQLite，内容处理结果存入本地 JSON 文件
- **两种模式**：
  - **生产模式**：ingestor → D1/SQLite → ContentProcessor → JSON
  - **开发模式**：直接运行 ContentProcessor 处理本地 Markdown 文件

---

## 3. 端到端数据契约

### 3.1 ArticleInput（输入）

```json
{
  "url": "https://example.com/article",
  "title": "文章标题",
  "file": "article.md"
}
```

### 3.2 ArticleProcessed（输出）

```json
{
  "id": "auto-generated-uuid",
  "url": "https://example.com/article",
  "title": "文章标题",
  "content": "提取的完整文本（最多 10000 字符）",
  "summary": "AI 生成的摘要（最多 500 字符）",
  "category": "new",
  "tags": ["AI", "新闻"],
  "source": "MIT Tech Review",
  "extracted_at": "2026-02-14T12:00:00Z",
  "processed_at": "2026-02-14T12:05:00Z",
  "version": "v1"
}
```

### 3.3 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 系统生成的唯一标识（UUID） |
| `url` | string | ✅ | 原始链接 |
| `title` | string | ✅ | 标题 |
| `content` | string | ✅ | 提取的正文内容（截断至 10000 字符） |
| `summary` | string | ✅ | AI 生成的摘要 |
| `category` | string | ✅ | 分类标签，默认 `'new'` |
| `tags` | string[] | ✅ | 标签列表 |
| `source` | string | ✅ | 来源识别结果 |
| `extracted_at` | string | ✅ | 内容提取时间（ISO 8601） |
| `processed_at` | string | ✅ | 处理完成时间（ISO 8601） |
| `version` | string | ✅ | 数据契约版本，固定 `'v1'` |

### 3.4 版本演进策略

- 当前版本：`v1`
- 字段变更：向后兼容，新增字段可选
- 主版本升级：当字段删除或语义变更时升级

---

## 4. 数据落地与可追溯性

| 数据类型 | 存储位置 | 格式 | 说明 |
|----------|----------|------|------|
| 处理后文章 | `ai/articles/processed/{title}.json` | JSON | 完整 ArticleProcessed |
| 原始文章 | `ai/articles/original/*.md` | Markdown | 仅包含 URL 和标题 |
| 日报汇总 | `ai/daily/REPORT.md` | Markdown | 人工可读汇总 |
| 处理指标 | `ai/daily/REPORT_METRICS.md` | Markdown + JSON | 机器可读指标 |
| 去重缓存 | `.ai_cache/processed_urls.json` | JSON | 已处理 URL 集合 |

### 可追溯性链路

```
REPORT.md 
  → 点击原文链接 → ArticleProcessed JSON 
    → content 字段中的原始链接 → 原始网页
```

---

## 5. 组件接口示例

```python
# 提取器接口
class BaseExtractor:
    def extract(url: str) -> Optional[str]:
        """从 URL 提取正文文本"""
        pass

# 摘要生成器接口
class BaseSummarizer:
    def summarize(text: str) -> str:
        """生成文章摘要"""
        pass

# 分类器接口
class BaseClassifier:
    def classify(text: str) -> Dict:
        """返回 { category: str, tags: List[str], scores: Dict }"""
        pass

# 日报生成器接口
class ReportGenerator:
    def generate(articles: List[Dict], output_path: str) -> None:
        """生成日报 Markdown"""
        pass
```

---

## 6. 运行与部署要点

### 6.1 GitHub Actions 部署

| Workflow | 触发器 | 说明 |
|----------|--------|------|
| `content-processing.yml` | 定时（UTC 8:00）、手动 | 内容处理主流程 |
| `scheduled-collection.yml` | 定时 | 定时采集任务 |
| `ing_schedule.yml` | 定时 | 摄入调度 |
| `ci.yml` | push、PR | CI 测试 |
| `cloudflare-deploy.yml` | push | Cloudflare 部署 |

**content-processing.yml 资源限制**：6 小时、2 核 CPU、7GB RAM

### 6.2 本地运行

```bash
# 安装依赖
make install

# 运行完整工作流
make run

# 或直接执行
python scripts/content_processor.py --input ai/articles/original --max-articles 30
```

### 6.3 启动 API 服务

```bash
make api
# 访问 http://localhost:8000/docs 查看 Swagger 文档
```

### 6.4 Docker 部署

```bash
docker-compose up -d
```

---

## 7. 观测性与基线指标

### 7.1 关键指标

| 指标 | 描述 | 告警阈值 |
|------|------|----------|
| `pages_processed` | 成功处理的文章数 | < 10（日报需至少 10 篇） |
| `duplicates_skipped` | 跳过的重复 URL 数 | - |
| `avg_processing_time_s` | 平均处理耗时 | > 600s |
| `extract_success_rate` | 提取成功率 | < 80% |
| `category_distribution` | 分类分布 | 单一分类 > 70% |

### 7.2 Metrics 快照

指标实时写入 `ai/daily/REPORT_METRICS.md`：

```markdown
## Metrics Snapshot @ 2026-02-14 12:00:00

```json
{
  "timestamp": "2026-02-14T12:00:00",
  "metrics": { ... },
  "averages": {
    "avg_processing_time_s": 12.5,
    "avg_content_len": 8500,
    "avg_summary_len": 450
  }
}
```
```

### 7.3 未来观测性增强（阶段 B）

- Dagster UI 面板
- 数据血缘追踪
- 任务级重试/失败告警
- 资源使用率监控

---

## 8. 错误处理与容错设计

### 8.1 降级策略

| 场景 | 降级策略 | 实现方式 |
|------|----------|----------|
| 提取器失败 | 使用标题作为占位内容 | `if not content: content = title` |
| 摘要生成失败 | 返回空摘要，记录错误日志 | `logger.error()` + 空字符串 |
| 分类模型失败 | 使用默认分类 `'new'` | 异常时回退默认值 |
| Ollama 不可用 | 跳过摘要生成 | try/except + 降级逻辑 |
| 文件写入失败 | 静默跳过（需改进） | 当前 `except: pass` |

### 8.2 重试机制（待实现）

| 组件 | 重试策略 | 最大次数 | 退避策略 |
|------|----------|----------|----------|
| HTTP 请求（提取） | 指数退避 | 3 次 | 1s, 2s, 4s |
| LLM API 调用 | 固定间隔 | 2 次 | 3s 间隔 |
| 文件写入 | 立即重试 | 1 次 | - |

### 8.3 限流策略（待实现）

```yaml
rate_limits:
  article_processing:
    max_concurrent: 5
    per_minute: 60
  api_requests:
    per_minute: 100
```

### 8.4 告警规则（待实现）

| 告警项 | 阈值 | 通知方式 |
|--------|------|----------|
| 提取成功率 | < 80% | Slack / 邮件 |
| 处理耗时 | > 600s | Slack |
| API 错误率 | > 5% | Slack |

---

## 9. 分类规则说明

### 9.1 分类模型

- **模型**：BGE Classifier（BAAI/bge-base-en-v1.5）
- **输入**：标题 + 摘要的拼接文本
- **输出**：`{ category: string, tags: string[], scores: Record<string, float> }`

### 9.2 分类映射

| ID | 分类名称 | 触发条件/关键词 |
|----|----------|-----------------|
| 1 | 今日焦点 | score > 0.85 + 新闻媒体来源 |
| 2 | 大厂/人物 | Anthropic, OpenAI, Google, DeepMind, Altman 等 |
| 3 | Agent 工作流 | MCP, A2A, AutoGen, Agent, Workflow 等 |
| 4 | 编程助手 | Cursor, Windsurf, Cline, IDE 插件等 |
| 5 | 内容生成 | 多模态, 写作, 视频生成, Midjourney 等 |
| 6 | 工具生态 | LangChain, LlamaIndex, OpenClaw 等 |
| 7 | 安全风险 | 漏洞, 恶意软件, 深度伪造, 攻击等 |
| 8 | 灵感库 | 待深挖方向，概念性内容 |
| new | 默认 | 以上皆不匹配 |

### 9.3 来源识别

```python
DOMAIN_SOURCE_MAP = {
    '36kr.com': '36氪',
    'arxiv.org': 'ArXiv',
    'news.ycombinator.com': 'Hacker News',
    'techcrunch.com': 'TechCrunch',
    'jiqizhixin.com': '机器之心',
    'mit.edu': 'MIT Tech Review',
}
```

---

## 10. 演进路线与里程碑

### 10.1 当前状态评估

```
阶段 A（GitHub Actions 基线）    ████████████████████  85%  ▸ 可正常生产运行
阶段 B（Dagster 编排层）         ████░░░░░░░░░░░░░░  15%  ▸ 需 2-4 周完成 MVP
阶段 C（微服务化）              ░░░░░░░░░░░░░░░░░░   0%   ▸ 暂无时间表
```

### 10.2 阶段 B 详细时间表（Dagster 编排层）

| 里程碑 | 目标 | 预计完成 |
|--------|------|----------|
| M1 | 最小 DAG 定义 + 提取阶段集成 | 第 1 周 |
| M2 | 摘要 + 分类阶段接入 | 第 2 周 |
| M3 | 观测性面板 + 数据血缘 | 第 3 周 |
| M4 | CI/CD 对齐 + 回滚测试 | 第 4 周 |

### 10.3 回滚策略

- 保留 `main` 分支为纯 GitHub Actions 模式
- Dagster 部署在独立分支 `feature/dagster`
- 回滚：切换回 `main` 分支部署

### 10.4 风险与对策

| 风险 | 对策 |
|------|------|
| 学习成本 | 优先 MVP 实现，先能用再优化 |
| 运维成本 | 提供云托管/自托管对照选择 |
| 兼容性 | 确保能回滚到现有架构 |

---

## 11. 安全与合规

- ✅ 遵循最小权限原则
- ✅ 避免密钥硬编码（使用 `.env` 环境变量）
- ✅ 模型/数据访问在受控环境中进行
- ⚠️ 审计日志待实现
- ⚠️ 数据脱敏策略待制定

---

## 12. API 接口契约

### 12.1 接口概览

API 挂载在 `api/main.py`，v2 路由挂载在 `/api/v2` 前缀下。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 根路径（返回版本信息） |
| `/health` | GET | 健康检查 |
| `/api/v2/articles` | GET | 获取文章列表 |
| `/api/v2/articles/{article_id}` | GET | 获取单篇文章 |
| `/api/v2/stats` | GET | 获取统计信息 |
| `/api/v2/sources` | GET | 获取来源列表 |
| `/docs` | GET | Swagger API 文档 |
| `/redoc` | GET | ReDoc API 文档 |

### 12.2 API v2 详细端点

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/api/v2/articles` | GET | `page`, `page_size`, `source`, `category` | 分页获取文章 |
| `/api/v2/articles/{id}` | GET | - | 获取文章详情 |
| `/api/v2/stats` | GET | - | 获取统计信息 |
| `/api/v2/sources` | GET | - | 获取来源列表 |
| `/api/v2/health` | GET | - | 健康检查 |

### 12.3 详细接口定义

完整 OpenAPI 定义见：[docs/openapi.yaml](docs/openapi.yaml)

---

## 13. 参考与关联

### 代码文件

#### URL 抓取层
- `ingestor/main.py` - 抓取入口主程序
- `ingestor/scrapers/rss_scraper.py` - RSS 抓取器
- `ingestor/scrapers/hackernews_scraper.py` - Hacker News 抓取器
- `ingestor/scrapers/newsnow_scraper.py` - NewsNow 抓取器
- `ingestor/scrapers/devto_scraper.py` - Dev.to 抓取器
- `ingestor/scrapers/v2ex_scraper.py` - V2EX 抓取器
- `ingestor/scrapers/reddit_scraper.py` - Reddit 抓取器
- `ingestor/scrapers/arxiv_scraper.py` - ArXiv 抓取器
- `ingestor/transformers/article_transformer.py` - 数据转换器
- `config/sources.yaml` - 来源配置文件

#### 内容处理层
- `scripts/content_processor.py` - 主处理器
- `scripts/extractors/*` - 提取器实现
- `scripts/summarizers/*` - 摘要生成器
- `scripts/classifiers/*` - 分类器
- `scripts/report_generator.py` - 日报生成器

#### 服务层
- `api/main.py` - FastAPI 入口
- `.github/workflows/content-processing.yml` - CI/CD

### 相关文档

- [docs/openapi.yaml](docs/openapi.yaml) - API 契约
- [docs/schemas/article_input.schema.json](docs/schemas/article_input.schema.json) - 输入 Schema
- [docs/schemas/article_processed.schema.json](docs/schemas/article_processed.schema.json) - 输出 Schema
- [docs/schemas/daily_report.schema.json](docs/schemas/daily_report.schema.json) - 日报 Schema

---

## 14. 数据示例

### 完整 ArticleProcessed 示例

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "url": "https://www.anthropic.com/news/claude-enterprise-deployment",
  "title": "Claude Enterprise 正式发布：企业级 AI 助手能力解析",
  "content": "Anthropic 今日宣布推出 Claude Enterprise，这是一个面向企业用户的 AI 助手产品...",
  "summary": "Anthropic 推出 Claude Enterprise，面向企业用户，提供增强的安全性和管理功能。",
  "category": "2",
  "tags": ["Anthropic", "Claude", "企业级", "AI Assistant"],
  "source": "MIT Tech Review",
  "extracted_at": "2026-02-14T12:00:00Z",
  "processed_at": "2026-02-14T12:05:23Z",
  "version": "v1"
}
```

### 日报 REPORT.md 示例

```markdown
# AI Daily Report - 2026-02-14

## 今日焦点

1. **[Claude Enterprise 正式发布](https://www.anthropic.com/news/claude-enterprise-deployment)**
   - 来源：MIT Tech Review
   - 摘要：Anthropic 推出 Claude Enterprise...

## 大厂/人物

...

## Agent 工作流

...
```

---

*本文档最后更新：2026-02-14*  
*版本：v1.0*
