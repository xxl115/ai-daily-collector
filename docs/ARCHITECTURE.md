# AI Daily Collector 架构文档

## 一、项目概述

**AI Daily Collector** 是一个自动化收集和整理每日 AI 相关新闻、论文、工具的系统。

| 项目 | 内容 |
|------|------|
| 项目路径 | `~/code/ai-daily-collector` |
| 版本 | v2.2.1 |
| 部署 | Cloudflare Workers |
| 数据存储 | D1 (Cloudflare) |

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      数据流                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RSS源 ──▶ 抓取 ──▶ 存储 ──▶ 处理 ──▶ 输出                 │
│  (30+)      (ingestor)  (D1)   (scripts)   (API/日报)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心模块

### 1. ingestor/ 数据摄取

**功能**：从多来源抓取 AI 新闻和论文

**目录结构**：
```
ingestor/
├── main.py              # 抓取入口
├── scrapers/            # 8 种抓取器
│   ├── rss_scraper.py
│   ├── hackernews_scraper.py
│   ├── reddit_scraper.py
│   ├── arxiv_scraper.py
│   ├── v2ex_scraper.py
│   ├── devto_scraper.py
│   ├── newsnow_scraper.py
│   └── article_scraper.py
├── storage/            # 存储适配
│   ├── d1_adapter.py
│   ├── d1_client.py
│   └── db.py
└── transformers/
    └── article_transformer.py
```

**8 种数据源**：
| 抓取器 | 来源 |
|--------|------|
| rss_scraper | RSS 订阅 |
| hackernews_scraper | Hacker News |
| reddit_scraper | Reddit |
| arxiv_scraper | ArXiv 论文 |
| v2ex_scraper | V2EX |
| devto_scraper | Dev.to |
| newsnow_scraper | NewsNow |
| article_scraper | 通用文章 |

---

### 2. scripts/ 内容处理

**功能**：提取正文、生成摘要、分类

**目录结构**：
```
scripts/
├── content_processor.py      # 主处理器
├── generate_daily_report.py  # 生成日报
├── report_generator.py       # 报告生成器
├── summarize_by_date.py     # 按日期摘要
├── extractors/              # 内容提取 (5种)
│   ├── jina_extractor.py
│   ├── crawl4ai_extractor.py
│   ├── trafilatura_extractor.py
│   ├── race_extractor.py
│   └── multi_extractor.py
├── summarizers/             # 摘要生成
│   └── ollama_summarizer.py
└── classifiers/             # 分类器
    ├── bge_classifier.py
    └── rule_classifier.py
```

**处理流程**：
1. 提取正文 (Extractors)
2. 生成摘要 (Summarizers) - Ollama 本地 LLM
3. 分类 (Classifiers) - BGE 嵌入向量 / 规则

---

### 3. api/ 服务层

**功能**：提供 REST API 接口

**目录结构**：
```
api/
├── main.py                   # FastAPI 入口
├── mcp.py                   # MCP 协议支持
├── cloudflare_worker.py     # Cloudflare Worker 适配
├── v2/
│   ├── models.py           # 数据模型
│   ├── routes_d1.py       # D1 存储路由
│   └── routes_daily.py    # 日报路由
└── storage/
    └── dao.py              # 数据访问对象
```

**API 端点**：
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 根路径 |
| `/health` | GET | 健康检查 |
| `/api/v2/articles` | GET | 文章列表 |
| `/api/v2/articles/{id}` | GET | 文章详情 |
| `/api/v2/stats` | GET | 统计信息 |
| `/api/v2/sources` | GET | 来源列表 |
| `/api/v2/crawl-logs` | GET | 抓取日志 |
| `/api/v2/crawl-stats` | GET | 抓取统计 |

---

### 4. worker.py

**功能**：Cloudflare Workers MCP 工具

**MCP 工具**：
| 工具 | 功能 |
|------|------|
| `get_articles_needing_processing` | 获取待处理文章 |
| `update_article_summary_and_category` | 更新摘要和分类 |
| `get_articles_with_empty_summary` | 获取空摘要文章 |

---

### 5. config/ 配置

```
config/
├── config.py        # 环境变量配置
├── settings.py     # 应用设置
└── sources.yaml   # RSS 源配置 (30+)
```

---

### 6. utils/ 工具

```
utils/
├── audit.py          # 审计日志
├── retry.py         # 重试机制
├── rate_limit.py    # 速率限制
└── logging_config.py # 日志配置
```

---

## 四、数据模型

### Article

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文章 ID |
| url | string | 原文链接 |
| title | string | 标题 |
| content | string | 正文内容 |
| summary | string | AI 摘要 |
| categories | list | 分类 |
| tags | list | 标签 |
| source | string | 来源 |
| published_at | datetime | 发布时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 五、部署

### 部署方式

| 方式 | 配置文件 |
|------|----------|
| Docker | docker-compose.yml |
| Cloudflare Workers | worker.py + wrangler.toml |
| CI/CD | GitHub Actions |

### GitHub Actions 工作流

| 工作流 | 功能 |
|--------|------|
| ci.yml | 持续集成 |
| cloudflare-deploy.yml | Workers 部署 |
| content-extraction.yml | 内容提取 |
| scheduled-collection.yml | 定时采集 |

---

## 六、环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ZAI_API_KEY` | 智谱 AI API Key | - |
| `ZAI_MODEL` | 模型名称 | glm-4 |
| `NOTION_API_KEY` | Notion API | - |
| `DATA_DIR` | 数据目录 | ./data |
| `ARTICLES_HOURS_BACK` | 抓取小时数 | 24 |
| `MAX_ARTICLES` | 每源最大文章数 | 30 |

---

## 七、测试

```
tests/
├── test_api.py
├── test_core.py
├── test_content_processor.py
├── test_report_generator.py
├── test_all_scrapers.py
├── test_dedup.py
├── test_integration.py
├── test_utils_*.py
└── ...
```

---

## 八、相关文档

| 文档 | 说明 |
|------|------|
| `docs/ARCHITECTURE_ALL.md` | 完整架构（参考） |
| `docs/MCP_WORKER_API.md` | MCP API 文档 |
| `docs/openapi.yaml` | OpenAPI 规范 |
| `docs/schemas/` | JSON Schema |
