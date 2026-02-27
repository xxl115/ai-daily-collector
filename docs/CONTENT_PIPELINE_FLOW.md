# AI Content Processing Pipeline

## 完整数据流

```mermaid
flowchart TB
    subgraph D1["D1 Database"]
        direction TB
        D1_Articles["articles 表<br/>content = NULL"]
        D1_Extracted["articles 表<br/>content 已填充"]
    end

    subgraph Workflow["GitHub Actions: content-extraction.yml"]
        direction TB
        Trigger["定时触发 (8:00)<br/>或手动触发"]
    end

    subgraph Processor["content_processor.py"]
        direction TB
        ReadD1["从 D1 读取<br/>--source d1"]
        Query["SQL: content IS NULL"]
        
        subgraph Extraction["三层降级提取"]
            Trafilatura["Trafilatura"]
            Jina["Jina Reader"]
            Crawl4AI["Crawl4AI"]
        end
        
        SaveLocal["保存到本地<br/>ai/articles/processed/*.json"]
        SaveD1["写回 D1<br/>update_article_content"]
    end

    Trigger --> ReadD1
    ReadD1 --> Query
    Query --> D1_Articles
    D1_Articles --> Trafilatura
    
    Trafilatura -- 失败 --> Jina
    Jina -- 失败 --> Crawl4AI
    Crawl4AI -- 成功 --> SaveLocal
    Crawl4AI -- 失败 --> SaveLocal
    
    SaveLocal --> SaveD1
    SaveD1 --> D1_Extracted
```

## 提取流程详情

```mermaid
flowchart LR
    subgraph Input["输入"]
        URL["URL"]
        Title["标题"]
    end

    subgraph Extractors["三层降级"]
        E1["Trafilatura<br/>本地提取"]
        E2["Jina Reader<br/>API 提取"]
        E3["Crawl4AI<br/>浏览器模拟"]
    end

    subgraph Output["输出"]
        Content["content<br/>正文内容"]
        Method["extraction_method<br/>提取方法"]
    end

    URL --> E1
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
    subgraph Schedule["定时任务"]
        S1["内容抓取<br/>scheduled-collection"]
        S2["内容提取<br/>content-extraction"]
        S3["内容摘要<br/>content-summarization"]
        S4["内容分类<br/>content-classification"]
        S5["日报生成<br/>daily-report"]
    end

    S1 -->|"写入 D1<br/>content=NULL"| S2
    S2 -->|"更新 D1<br/>content=已填充"| S3
    S3 -->|"更新 D1<br/>summary=已生成"| S4
    S4 -->|"更新 D1<br/>category=已分类"| S5
```

## 数据字段映射

```mermaid
erDiagram
    ARTICLES {
        string id PK
        string title
        string content "提取的文章正文"
        string url
        string published_at
        string source "来源网站"
        string categories "JSON 数组"
        string tags "JSON 数组"
        string summary "AI 生成的摘要"
        string raw_markdown "提取方法标记"
        string ingested_at
        string created_at
    }

    CRAWL_LOGS {
        integer id PK
        string source_name
        string source_type
        integer articles_count
        integer duration_ms
        string status
        string error_message
        string crawled_at
    }
```

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--source` | 数据源 | `local` / `d1` |
| `--mode` | 处理模式 | `full` / `extract-only` / `summarize-only` / `classify-only` |
| `--d1-account-id` | Cloudflare 账户 ID | 从 `CF_ACCOUNT_ID` secrets 读取 |
| `--d1-database-id` | D1 数据库 ID | 从 `CF_D1_DATABASE_ID` secrets 读取 |
| `--d1-api-token` | API Token | 从 `CF_API_TOKEN` secrets 读取 |
| `--max-articles` | 最大处理数量 | 默认 30 |

## 典型使用场景

```bash
# 1. 从 D1 提取内容（GitHub Actions 自动）
python scripts/content_processor.py \
  --source d1 \
  --mode extract-only \
  --d1-account-id $CF_ACCOUNT_ID \
  --d1-database-id $CF_D1_DATABASE_ID \
  --d1-api-token $CF_API_TOKEN

# 2. 从本地文件提取内容（开发测试）
python scripts/content_processor.py \
  --source local \
  --mode extract-only \
  --input ai/articles/original

# 3. 完整处理流程
python scripts/content_processor.py \
  --source d1 \
  --mode full
```
