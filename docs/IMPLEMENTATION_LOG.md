# Implementation Log — AI Content Processing Pipeline (方案 A 基线)

记录时间线、变更内容、实施要点、验收标准以及后续行动计划，确保可追踪、可复现、可回滚。

1. 总览
- 目标/路线：先落地基线（方案 A，GitHub Actions 基线实现），稳定后再评估方案 B、方案 C。
- 当前阶段：阶段 I 基线落地正在推进，已实现 GH Actions 工作流、核心骨架代码与提取器/摘要/分类/日报等基础组件。
- 主要产出：.github/workflows/content-processing.yml、scripts/content_processor.py、提取器/摘要器/分类器/日报生成器、以及文档计划。

2. 已完成的实施内容（按时间顺序）
- 2026-02-14: 新增 GitHub Actions 工作流 content-processing.yml，配置环境、依赖、Ollama 启动、核心流水线调用、结果提交。参见 .github/workflows/content-processing.yml。
- 2026-02-14: 实现基础内容处理骨架 scripts/content_processor.py，包含从原始文章读取、批量处理、降级与日志输出的入口逻辑。
- 2026-02-14: 实现提取器/降级提取器：脚本文件 scripts/extractors/trafilatura_extractor.py 与 scripts/extractors/jina_extractor.py，提供主方案的文本提取与降级获取能力。
- 2026-02-14: 实现摘要生成器（scripts/summarizers/ollama_summarizer.py）与分类器（scripts/classifiers/bge_classifier.py）、日报生成器（scripts/report_generator.py）的初步实现。
- 2026-02-14: 新增模块入口文件：scripts/extractors/__init__.py、scripts/summarizers/__init__.py、scripts/classifiers/__init__.py，方便导入。
- 2026-02-14: 新增对比实施计划文档 docs/IMPLEMENTATION_PLAN_A_B_C_DETAILED.md，记录三种方案的阶段性任务与计划。 
- 2026-02-14: 将实施计划简要合并到 docs/GITHUB_ACTIONS_CONTENT_PROCESSING_PLAN.md 的实施章节（十一节）。
- 2026-02-14: 新增独立实现方案总览 docs/IMPLEMENTATION_PLAN_A_B_C.md（阶段性工作计划/里程碑/风险/回滚的摘要）。
- 2026-02-14: 新增阶段性工作要点、风险回滚点的完整文档，确保评审与落地可追踪。 

3. 设计要点回顾
- 幂等性：在内容处理链中为每篇文章生成全局唯一标识，避免重复输出日报。
- 降级路径：若提取失败走降级降级、摘要失败回退到简短摘要、分类失败回退到默认分类。
- 缓存：对依赖、模型、中间结果进行缓存，降低重复工作与提升速度。
- 观测性：输出关键指标日志，便于后续观测与告警。
- 回滚策略：制定明确的阶段性回滚点，确保可控降级回退。

4. 下一步行动计划（阶段 I 的后续工作）
- A7-A10：完成提取器、摘要器、分类器、日报生成器的完整实现并在本地验证。
- A6/阶段 I 验收：本地快速验证，确保 5-10 篇文章的端到端可执行性，输出 ai/articles/processed 与 ai/daily/REPORT.md。
- B 阶段准备：在基线稳定后，评估引入 Dagster/Prefect 的可行性与计划。
- C 阶段准备：在评估后，制定微服务化的实施方案与迁移策略。

5. 验收标准（阶段性）
- 端到端可运行：本地或 CI 环境从输入到输出的全流程可以执行且产出符合结构。
- 幂等性：重复执行不产生重复的日报，或输出已存在的记录不重复新增。 
- 降级可用性：降级路径可用，报告产出仍具价值。
- 日报格式正确：日报包含统计、各分类条目、原文链接、摘要等字段。
- 日志完整性：日志输出包含关键状态、耗时信息、错误信息。

6. 参考与链接
- docs/GITHUB_ACTIONS_CONTENT_PROCESSING_PLAN.md
- docs/IMPLEMENTATION_PLAN_A_B_C_DETAILED.md
- docs/IMPLEMENTATION_PLAN_A_B_C.md
- .github/workflows/content-processing.yml
- scripts/content_processor.py
- scripts/extractors/*
- scripts/summarizers/*
- scripts/classifiers/*
- scripts/report_generator.py

7. 附件：变更清单（核心改动摘要）
- 1) 新增工作流：.github/workflows/content-processing.yml
- 2) 新增核心处理脚本：scripts/content_processor.py
- 3) 新增提取器/降级提取器：scripts/extractors/trafilatura_extractor.py、scripts/extractors/jina_extractor.py
- 4) 新增摘要生成器与分类器：scripts/summarizers/ollama_summarizer.py、scripts/classifiers/bge_classifier.py
- 5) 新增日报生成器：scripts/report_generator.py
- 6) 新增模块入口：scripts/extractors/__init__.py、scripts/summarizers/__init__.py、scripts/classifiers/__init__.py
- 7) 新增阶段性计划文档：docs/IMPLEMENTATION_PLAN_A_B_C_DETAILED.md
- 8) 新增综合实现计划文档：docs/IMPLEMENTATION_PLAN_A_B_C.md
- 9) 将实施计划对照纳入现有计划：docs/GITHUB_ACTIONS_CONTENT_PROCESSING_PLAN.md（新增十一章）
- 10) 新增可落地对比模板与本地验证策略待后续补充

8. 下一步确认
- 你确认后我将按阶段 I 的计划推进，逐步提交 Patch 并在每个阶段完成后提供验收要点与结果总结。
- 如需我同时准备一个可直接粘贴到 PR 的对比模板，请告知，我将一并生成。
- 主要产出：.github/workflows/content-processing.yml、scripts/content_processor.py、提取器/摘要器/分类器/日报生成器、以及文档计划。
- 进一步记录更新：2026-02-14 进展进入阶段 I 的基础实现与本地验证通过。

### 2026-02-15 — 阶段 I 进展记录
- 完成 A11-A13 的初步设计：增强本地观测性、扩展本地测试、准备 PR 对比模板。
- 实现要点：将 per-article 流程的观测勋章纳入日志、输出指标到 AI 日报 Metrics 文件、并添加去重/幂等的持久化缓存。
- 下一步：继续完善本地验证、扩展测试、编写 PR 对比模板。 
