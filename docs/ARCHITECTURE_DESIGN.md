# AI Content Processing Pipeline – Architecture Design (方案 A 基线)

适用范围
- 以 GitHub Actions 为基线的端到端 AI 内容处理流水线，覆盖从数据入口到日报输出的完整流程，并提供幂等、降级、缓存与基础观测性能力。

1. 概要设计
- 系统目标：在资源受限的 CI 环境中，稳定地完成文章提取、摘要、分类、日报生成，并可在未来逐步扩展为更复杂的编排与微服务架构。
- 数据流核心：输入文章集合 -> 提取 -> 摘要 -> 分类 -> 汇总日报 -> 输出持久化结果
- 主要组件边界：
  - ContentProcessor（编排入口）
  - TrafilaturaExtractor（主提取器）
  - JinaExtractor（降级提取器）
  - OllamaSummarizer（摘要器）
  - BGEClassifier（分类器）
  - ReportGenerator（日报生成器）
  - Cache/State Management（简单的 URL 去重与缓存）

2. 架构决策要点
- 采用本地优先、CI 触发的方式，尽量避免网络风口的不可控成本与延迟
- 幂等性：对每篇文章使用全局唯一标识，重复执行不会产出重复日报
- 降级策略：如提取失败，降级为 RSS 描述；如摘要失败，降级为简短摘要；如分类失败，回归到默认分类
- 缓存策略：缓存模型、依赖和中间结果，减少重复下载与推理
- 观测性：日志、指标与简单的统计报告，以便快速定位瓶颈
- 安全性：避免在 CI 配置中暴露密钥，模型推理应仅在受控环境中进行
- 未来演进：方案 B（ Dagster/ Prefect 编排）与方案 C（微服务）作为后续选项

3. 数据模型与接口概览
- ArticleInput: { url, title }
- ArticleProcessed: { url, title, content, summary, category, tags, source, processed_at }
- ReporterOutput: MD 文档字符串
- 组件接口示例：
  - TrafilaturaExtractor.extract(url) -> Optional[str]
  - JinaExtractor.extract(url) -> Optional[str]
  - OllamaSummarizer.summarize(text) -> str
  - BGEClassifier.classify(text) -> { category, tags, scores }
  - ReportGenerator.generate(articles, output_path) -> None

4. 数据流与时序
- Step 1: 数据输入 -> 文章列表读取（ai/articles/original）
- Step 2: 内容提取 -> content = TrafilaturaExtractor.extract(url) or JinaExtractor.extract(url)
- Step 3: 摘要生成 -> summary = OllamaSummarizer.summarize(content)
- Step 4: 分类 -> classification = BGEClassifier.classify(title + summary)
- Step 5: 组装 ArticleProcessed，并输出到 ai/articles/processed/{title}.json
- Step 6: 生成日报 -> ReportGenerator.generate(results, ai/daily/REPORT.md)
- Step 7: 记录日志、更新去重缓存、emit metrics

5. 资源与性能考虑
- CI Runner：Ubuntu-latest，2 核 CPU、7GB RAM，3 小时超时（按计划）
- 模型加载与推理：本地 Ollama + qwen2.5:1.5b，必要时缓存与预下载
- 依赖缓存：pip 缓存、模型缓存、transformers/torch 缓存
- 并发控制：当前阶段以顺序执行为基线，后续再引入并行化（线程/进程/分布式）

6. 可观测性、监控与告警
- 日志字段： URL、标题、来源、提取长度、摘要长度、分类分数、处理耗时
- 指标：提取成功率、摘要长度均值、分类准确性代理、日报生成成功率
- 指标输出：生成 ai/daily/REPORT_METRICS.md，便于追踪与比较

7. 错误处理与降级路径
- 提取失败：降级为 RSS 描述或标题文本
- 摘要失败：降级为简短摘要
- 分类失败：默认分类 (new)
- 全局错误处理：日志记录并进入下一个条目

8. 持久化与幂等性设计
- 文件系统持久化：.ai_cache/processed_urls.json 记录已处理 URL
- 每次处理完成后写入，确保跨会话幂等
- 未来可扩展为外部缓存/数据库实现持久化

9. 安全与合规
- 不在仓库中硬编码密钥，模型服务应在受控环境中调用
- 日报输出本地化，避免敏感信息外泄

10. 迁移路径与演进
- 方案 B（Dagster/Prefect）作为中期目标，提升编排、血缘、观测性
- 方案 C（微服务）作为长期目标，提升扩展性与部署灵活性

11. 风险与对策
- 资源瓶颈、CI 超时、网络波动、模型不可用等风险点，以及对策：分批处理、降级路径、缓存、健康检查、回滚点

12. 参考与后续步骤
- 参考 Dagster/Prefect 官方文档、GitHub Actions 缓存文档、以及端到端 RAG 流水线设计的公开实践
