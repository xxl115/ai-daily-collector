# Architecture All-in-One — AI Content Processing Pipeline (Baseline A)

此文档整合并简化了现有架构相关要点，提供一个可直接落地的全景视图，方便快速理解、评审与落地。

## 核心数据流
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   来源配置   │     │   抓取器     │     │   转换器     │     │   存储层     │
│  (YAML)      │────▶│  (HTTP/API)  │────▶│ (Pydantic)   │────▶│  (D1/SQLite) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

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

## 数据模型（简要）
- ArticleInput: { url, title }
- ArticleProcessed: { url, title, content, summary, category, tags, source, processed_at }
- Metrics: 运行指标快照（后续扩展）

## 数据契约示例（代码）
```python
from pydantic import BaseModel
from typing import List

class ArticleProcessed(BaseModel):
    url: str
    title: str
    content: str
    summary: str
    category: str
    tags: List[str]
    source: str
    processed_at: str
```

## 运行与部署要点
- 运行环境：GitHub Actions CI，6 小时、2 核 CPU、7GB RAM，资源需通过缓存/降级等策略保障
- 部署：通过 .github/workflows/content-processing.yml 实现自动化执行
- 安全性：避免在仓库中硬编码密钥，模型访问需在受控环境中进行

## 演进路线
- 阶段 II：Dagster/Prefect 编排（方案 B）提升观测性与血缘
- 阶段 III：微服务化（方案 C）提升可扩展性

## 数据制品与可追溯性
- 产出的数据文件 ai/articles/processed/ 以 JSON 形式存储每篇文章的完整信息
- 每篇文章的抓取 URL 将记录在 ArticleProcessed.url 字段，用于追溯
- 日报 ai/daily/REPORT.md 中对原文链接使用 [原文](URL) 的形式呈现

## 参考与关联
- 参考 docs/ARCHITECTURE_DESIGN.md（更为详细的设计与模式）
- 与实现文件的对齐：scripts/content_processor.py、scripts/extractors/*、scripts/summarizers/*、scripts/classifiers/*、scripts/report_generator.py
