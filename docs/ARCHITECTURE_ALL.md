# Architecture All-in-One — AI 内容处理流水线（基线 A）

以下文档作为全量架构参考，覆盖端到端的数据流、数据契约、落地路径，以及未来的演进路线。请以此文档为统一参考源，其他补充文档作为导航与扩展。

1. 概览
- 目标：提供一个统一、易于理解、便于落地的 All-in-One 架构参考。
- 当前基线：GitHub Actions 定时触发（UTC 18:00），ingestor/main.py 将 URL 写入 Cloudflare D1 边缘数据库，CF Workers/ FastAPI 作为入口与分发，客户端通过 API/前端访问。
- 演进路径：A 基线 → B（Dagster/Prefect MVP） → C（微服务/事件驱动）

2. 核心数据流（图示与文字并用）
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   来源配置   │     │   抓取器     │     │   转换器     │     │   存储层     │
│  (YAML)      │────▶│  (HTTP/API)  │────▶│ (Pydantic)   │────▶│  (D1/SQLite) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

GitHub Actions（定时任务，UTC 18:00）
```
GitHub Actions (定时 UTC 18:00)
    触发点：定时触发 → ingestor/main.py
    处理链路：提取/转换/落地/日报
```

3. 端到端数据契约（字段要点）
- ArticleInput: { url, title, ingested_at }
- ArticleProcessed: {
  id: 由系统生成的唯一标识,
  url: 原始链接,
  title: 标题,
  content: 原始/处理后的文本,
  summary: 摘要文本,
  category: 分类标签,
  tags: 标签列表,
  source: 来源,
  extracted_at: 提取时间,
  processed_at: 处理完成时间,
  version: 版本标识
}
- DailyReport: 日报的结构描述（简化）

4. 数据落地与可追溯性
- ai/articles/processed/{title}.json：存储 ArticleProcessed 条目，字段覆盖上述数据契约
- ai/daily/REPORT.md：每日汇总日报，包含原文链接：[原文](URL)
- URL 的可追溯性：从日报到原文的跳转点，以及 content 字段中的原始链接

5. 数据流与接口示例
```
- TrafilaturaExtractor.extract(url) -> Optional[str]
- JinaExtractor.extract(url) -> Optional[str]
- OllamaSummarizer.summarize(text) -> str
- BGEClassifier.classify(text) -> { category, tags, scores }
- ReportGenerator.generate(articles, output_path) -> None
```

6. 运行与部署要点
- 运行环境：GitHub Actions CI，6 小时、2 核 CPU、7GB RAM，资源需通过缓存/降级等策略保障
- 部署：通过 .github/workflows/content-processing.yml 实现自动化执行
- 安全性：避免在仓库中硬编码密钥，模型访问需在受控环境中进行

7. 观测性与基线指标
- 观测项：提取成功率、摘要长度、分类分数、日报完成率、处理耗时
- Metrics 快照：ai/daily/REPORT_METRICS.md（离线分析用）

8. 演进路线
- 阶段 II：Dagster/Prefect 编排（方案 B）提升观测性与血缘
- 阶段 III：微服务化（方案 C）提升可扩展性

9. 安全与合规
- 遵循最小权限原则，避免密钥暴露；模型/数据访问在受控环境中进行

10. 参考与关联
- 参考 ARCHITECTURE_DESIGN.md（更为详细的设计与模式）
- 与实现文件的对齐：scripts/content_processor.py、scripts/extractors/*、scripts/summarizers/*、scripts/classifiers/*、scripts/report_generator.py

11. 数据示例
```
{
  "url": "https://example.com/article1",
  "title": "示例文章1",
  "content": "提取的文本…",
  "summary": "摘要…",
  "category": "new",
  "tags": ["AI", "新闻"],
  "source": "MIT Tech Review",
  "extracted_at": "2026-02-14T12:00:00Z",
  "processed_at": "2026-02-14T12:00:00Z",
  "version": "v1"
}
```

12. 迁移与对齐
- 与现有 CF Worker / D1 入口保持对齐，逐步引入编排层（Dagster/Prefect）作为 MVP。
- 迁移计划：分阶段从基线 A 过渡到 B，确保回滚点与数据契约一致。

13. 风险与回滚点
- 学习成本、成本、对现网影响等风险，以及回滚到基线 A 的策略。

14. 注记
- 如需，后续可将图表用 Mermaid 代码块嵌入，便于渲染。
## 额外说明（中文版）
- 本文档提供 All-in-One 架构总览的中文版本，方便中文团队对齐与落地。
- 如需查看英文原文，请参考 ARCHITECTURE_ALL.md 的英文版本或 ARCHITECTURE_DIAGRAMS.md。
