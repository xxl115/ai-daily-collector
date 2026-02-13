AI Content Processing Pipeline – Architecture Redesign (Option B-like with Dagster/Prefect)

概述
- 在现有 CF Worker / D1 边缘存储的基础上，设计一个独立的编排层，将提取、摘要、分类、日报等阶段解耦为可观测、可测试、可扩展的任务/资产。

设计目标
- 更高的可观测性、数据血缘、容错和可扩展性。
- 保持现有产物与数据契约的一致性，确保从 CF Worker 触发到 D1 写入的端到端链路可追溯。
- 最小可行性实现 (MVP) 能力：引入 Dagster/Prefect 的最小工作流，覆盖提取、摘要、分类、日报等阶段，输出到 ai/articles/processed 与 ai/daily/REPORT.md。

方案要点
- 资产化建模：文章作为数据资产，包含 URL、标题、内容、摘要、分类、标签、来源、提取/处理时间戳、版本等。
- 流程编排：定义清晰的依赖关系和阶段边界，支持幂等、重试、降级路径。
- 数据流向与落地：提取文本落地到内容仓储/字段（ content 字段或 content store），后续阶段读取内容进行摘要与分类，最终汇总日报。
- 观测性：任务状态、事件日志、指标、血缘追踪等，方便排错和容量规划。
- 迁移策略：从现有的 CF Worker+D1 入口逐步迁移到编排层，确保可回滚性。

数据契约（示例，简化）
- ArticleInput: { id, url, title, ingested_at }
- ArticleContent (化简)：{ article_id, content, extracted_at }
- ArticleProcessed：{ article_id, url, title, content, summary, category, tags, source, processed_at, version }
- 日报结构：基于 ArticleProcessed 生成的汇总，输出 ai/daily/REPORT.md

实现路线（MVP 版本）
- 阶段 1：选型与最小可运行 DAG/Flow，聚焦提取阶段的集成，确保能写回 D1 的 content 字段与 ArticleProcessed 结构
- 阶段 2：接入摘要/分类阶段，完成报告聚合输出
- 阶段 3：引入数据血缘、观测性与简单测试
- 阶段 4：与现有 CI/CD 的对齐和回滚点设计

风险与对策
- 学习曲线：Dagster/Prefect 的资产/任务模型需要学习成本，优先以 MVP 实现为先。
- 运维成本：自托管编排需要运维能力，优先提供可选的云托管/托管版对照。
- 兼容性：确保能回滚回到现有架构（CF Worker/D1）以免影响现有生产。

参考资料
- Dagster 官方文档、Prefect 官方文档、数据管线设计与血缘最佳实践。
