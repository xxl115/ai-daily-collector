# AI Content Processing Pipeline

> 最后更新: 2026-02-27

## 完整数据流

```mermaid
flowchart TB
    subgraph D1["D1 Database"]
        direction TB
        D1_Articles["articles 表<br/>content = NULL"]
        D1_Extracted["articles 表<br/>content 已填充"]
    end

    subgraph Workflow["GitHub Actions"]
        Trigger["定时触发 (8:00)<br/>或手动触发"]
    end

    subgraph Processor["content_processor.py"]
        ReadD1["从 D1 读取<br/>--source d1"]
        Query["SQL: content IS NULL<br/>AND TRIM(url) != ''"]
        
        subgraph Extraction["三层降级提取"]
            Trafilatura["Trafilatura"]
            Jina["Jina Reader"]
            Crawl4AI["Crawl4AI"]
        end
        
        SaveD1["写回 D1<br/>update_article_content"]
    end

    Trigger --> ReadD1
    ReadD1 --> Query
    Query --> D1_Articles
    D1_Articles --> Trafilatura
    
    Trafilatura -- 失败 --> Jina
    Jina -- 失败 --> Crawl4AI
    Crawl4AI --> SaveD1
    
    SaveD1 --> D1_Extracted
```

## 提取流程详情

```mermaid
flowchart LR
    subgraph Input["输入"]
        URL["URL (也是文章 ID)"]
        Title["标题"]
        ID["原始 ID (URL)"]
    end

    subgraph Extractors["三层降级"]
        E1["Trafilatura<br/>本地提取"]
        E2["Jina Reader<br/>API 提取"]
        E3["Crawl4AI<br/>浏览器模拟"]
    end

    subgraph Output["输出"]
        Content["content<br/>正文内容"]
        Method["extraction_method<br/>提取方法标记"]
    end

    URL --> E1
    ID --> ID
    E1 -- 有内容 --> Content
    E1 -- 空 --> E2
    E2 -- 有内容 --> Content
    E2 -- 空 --> E3
    E3 -- 有内容 --> Content
    E3 -- 空 --> Content
    
    E1 --> Method
    E2 --> Method
    E3 --> Method
```

## Workflow 触发链

```mermaid
flowchart TB
    S1["内容抓取<br/>scheduled-collection"]
    S2["内容提取<br/>content-extraction"]
    S3["内容摘要<br/>content-summarization"]
    S4["内容分类<br/>content-classification"]
    S5["日报生成<br/>daily-report"]

    S1 -->|"写入 D1<br/>content=NULL"| S2
    S2 -->|"更新 D1<br/>content=已填充"| S3
    S3 -->|"更新 D1<br/>summary=已生成"| S4
    S4 -->|"更新 D1<br/>category=已分类"| S5
```

## 数据模型

### articles 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | **URL 作为主键**（如 `https://example.com/article`） |
| title | TEXT | 文章标题 |
| content | TEXT | 提取的文章正文 |
| url | TEXT | 文章 URL |
| published_at | TEXT | 发布时间 |
| source | TEXT | 来源网站 |
| categories | TEXT | JSON 数组 |
| tags | TEXT | JSON 数组 |
| summary | TEXT | AI 生成的摘要 |
| raw_markdown | TEXT | 提取方法标记（trafilatura/jina/crawl4ai） |
| ingested_at | TEXT | 抓取时间 |
| created_at | TEXT | 创建时间 |

### crawl_logs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| source_name | TEXT | 来源名称 |
| source_type | TEXT | 来源类型 |
| articles_count | INTEGER | 文章数量 |
| duration_ms | INTEGER | 耗时(毫秒) |
| status | TEXT | 状态 |
| error_message | TEXT | 错误信息 |
| crawled_at | TEXT | 抓取时间 |

## 命令行参数

```bash
python scripts/content_processor.py [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--source` | 数据源 | `local` |
| `--mode` | 处理模式 | `full` |
| `--input` | 输入目录 | `ai/articles/original` |
| `--output` | 输出目录 | `ai/articles/processed` |
| `--max-articles` | 最大处理数量 | 30 |
| `--d1-account-id` | Cloudflare 账户 ID | 环境变量 `CF_ACCOUNT_ID` |
| `--d1-database-id` | D1 数据库 ID | 环境变量 `CF_D1_DATABASE_ID` |
| `--d1-api-token` | API Token | 环境变量 `CF_API_TOKEN` |

### mode 选项

| 值 | 说明 |
|---|------|
| `full` | 完整流程：提取 + 摘要 + 分类 |
| `extract-only` | 仅提取内容 |
| `summarize-only` | 仅生成摘要 |
| `classify-only` | 仅分类 |

### source 选项

| 值 | 说明 |
|---|------|
| `local` | 从本地目录读取 `.md` 文件 |
| `d1` | 从 D1 数据库读取 |

## 使用示例

### 1. 从 D1 提取内容（生产环境）

```bash
python scripts/content_processor.py \
  --source d1 \
  --mode extract-only \
  --d1-account-id $CF_ACCOUNT_ID \
  --d1-database-id $CF_D1_DATABASE_ID \
  --d1-api-token $CF_API_TOKEN
```

### 2. 从本地文件提取（开发测试）

```bash
python scripts/content_processor.py \
  --source local \
  --mode extract-only \
  --input ai/articles/original
```

### 3. 完整流程

```bash
python scripts/content_processor.py \
  --source d1 \
  --mode full
```

## GitHub Secrets

运行 workflow 需要以下 Secrets：

| Secret | 说明 |
|--------|------|
| `CF_ACCOUNT_ID` | Cloudflare 账户 ID |
| `CF_D1_DATABASE_ID` | D1 数据库 ID |
| `CF_API_TOKEN` | Cloudflare API Token |

## 实现细节

### D1 API 返回格式

```json
{
  "result": [{
    "results": [...],
    "success": true,
    "meta": {...}
  }],
  "success": true
}
```

需要通过 `result['result'][0]['results']` 获取实际数据。

### 三层降级策略

1. **Trafilatura** - 本地 HTML 解析（最快）
2. **Jina Reader** - API 提取（`r.jina.ai/{url}`）
3. **Crawl4AI** - 浏览器模拟（最慢但最鲁棒）

### 文章 ID 设计

- 使用 **URL 作为主键**（保证唯一性）
- 原始 ID 在提取时被保留，用于更新 D1 记录
