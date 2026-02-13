# Architecture Diagrams for AI Content Processing Pipeline (Baseline A)

These Mermaid diagrams visualize the baseline architecture and end-to-end data flow. They complement the textual architecture description and help with quick onboarding and reviews.

## 1) Deployment / Component Diagram (High level)
```mermaid
graph TD
  GH[GitHub Actions Scheduler] --> Ingestor[Ingestor / ingestor/main.py]
  Ingestor --> D1[(Cloudflare D1)]
  D1 --> CF[(Cloudflare Workers / FastAPI)]
  CF --> Client[Client App]
  subgraph Extraction
    Extractor[Content Extractor]
  end
  CF --> Extractor
  Extractor --> Processed[(ai/articles/processed)]
  Processed --> Daily[(ai/daily/REPORT.md)]
```

## 2) End-to-End Data Flow (Sequence)
```mermaid
sequenceDiagram
  participant CF as CF Worker
  participant In as Ingestor
  participant EX as Extractor
  participant SUM as Summarizer
  participant CLS as Classifier
  participant REP as Reporter
  participant D as D1
  participant Day as Daily

  CF->>In: Trigger ingestion of URL
  In->>EX: /extract?url=<URL>
  EX-->>In: content or fallback content
  In->>SUM: summarize(content)
  SUM-->>In: summary
  In->>CLS: classify(title + summary)
  CLS-->>In: category, tags
  In->>D: update ArticleProcessed with content/summary/category
  D->>Day: generate DAILY REPORT from processed data
  Day-->>D: ok
```

## 3) Data Contracts / Entities
```mermaid
classDiagram
  class ArticleInput {
    +url: string
    +title: string
  }
  class ArticleProcessed {
    +url: string
    +title: string
    +content: string
    +summary: string
    +category: string
    +tags: list<string>
    +source: string
    +processed_at: string
  }
  ArticleInput --|> ArticleProcessed : transforms
```

## 4) Notes
- 上述图可直接在 GitHub 的 Markdown 页面中渲染（Mermaid 支持）。
- 现阶段基线的实现点与这三张图保持一致：CF Worker 为入口，D1 为存储，内容提取、摘要、分类、日报等阶段的落地路径。可视化帮助团队理解数据流与依赖关系。
