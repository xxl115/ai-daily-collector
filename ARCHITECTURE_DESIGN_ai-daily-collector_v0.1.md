# ai-daily-collector 数据抓取管道与对外 API 服务分离设计文档
版本: v0.1
状态: 草案，待审核

说明：本设计文档描述在同一代码库内将 ingestion 数据抓取管道与对外 API 服务分离的方案，采用 Cloudflare D1 作为主存储，并通过共享数据契约 ArticleModel 对接。文档覆盖目标、边界、数据契约、存储适配、入口点、CI/CD 集成要点以及阶段性实现路线，便于后续实现和评审。

## 1. 设计目标与范围
- 目标
  - 将 ingestion 与 api 的职责分离，降低耦合、提升可测试性与扩展性。
  - 统一的数据契约 ArticleModel，在 ingestion 与 api 之间对接，并落地到 Cloudflare D1。
  - 两端在同一仓库内完成分层实现，演进到独立微服务仓库的路径保留。
  - 提供可扩展的安全、日志、测试与 CI/CD 支撑，初期不强制实现告警通知。
- 范围
  - ingestor: 数据抓取、清洗、转换、写入 D1 的完整管线（入口 ingest/main.py、scrapers、transformers、storage/d1_client）。
  - api: 读取 D1 数据并对外暴露 API（api/main.py、api/v2/routes 等）。
  - shared: 共享的数据契约（ArticleModel 等）。
  - cloud: Cloudflare D1 的存储适配实现，保留本地回退设计以便测试。

## 2. 架构概览
- ingestor/（数据抓取管道）
  - main.py
  - scrapers/rss_scraper.py、article_scraper.py
  - transformers/article_transformer.py
  - storage/d1_client.py
  - storage/db.py
  - storage/models.py
- shared/（共享契约）
  - models.py 作为 ArticleModel 等数据模型的暴露点
- api/（对外 API 服务）
  - main.py
  - storage/dao.py
  - v2/routes.py、v2/models.py
- config/settings.yaml
- .github/workflows/ingest_schedule.yml
- tests/（后续阶段补充）
- 运行/运维
  - docker-compose.yml、Makefile、requirements.txt（阶段性可用）

## 3. 数据契约与模型设计
- ArticleModel（共享契约，放在 shared/models.py）
  - id: str
  - title: str
  - content: str
  - url: str
  - published_at: datetime | None
  - source: str
  - categories: List[str]
  - tags: List[str]
  - summary: Optional[str]
  - raw_markdown: Optional[str]
  - ingested_at: datetime
- 辅助类型：SourceConfig、CrawledItem、TransformResult 等，用于扩展。
- 数据契约对接要点
  - ingestion 输出的 ArticleModel 需尽量向后兼容。
  - storage/models.py 字段应与 ArticleModel 对齐，以便映射数据库表。

## 4. Cloudflare D1 存储设计
- 目标：将 articles 表作为长期持久化存储， ingestion 写入， api 读取。
- 表结构（示意）
  - id TEXT PRIMARY KEY
  - title TEXT
  - content TEXT
  - url TEXT
  - published_at TIMESTAMP WITH TIME ZONE
  - source TEXT
  - categories TEXT
  - tags TEXT
  - summary TEXT
  - raw_markdown TEXT
  - ingested_at TIMESTAMP WITH TIME ZONE
- 适配器设计
  - ingestor/storage/d1_client.py：封装 D1 REST/SQL 调用，使用 Bearer Token 认证，读取 CF_ACCOUNT_ID、CF_API_TOKEN、CF_D1_DB_NAME。
  - ingestor/storage/db.py：统一存储适配器接口，未来支持回退到本地数据库。
  - api/storage/dao.py：通过 D1 读取数据，供 API 路由使用。
- 安全性
  - Secrets 注入 via GitHub Actions: CF_ACCOUNT_ID、CF_API_TOKEN、CF_D1_DB_NAME。
- 幂等与去重
  - UPSERT 逻辑确保重复抓取不写入重复记录。

## 5. 入口与定时触发设计（GitHub Actions）
- ingestion 的定时触发入口：ingest/main.py，作为 GH Actions 的执行目标。
- GH Actions 时区统一为 UTC，cron 示例：0 18 * * *（UTC 18:00，等价于 Asia/Shanghai 02:00，若需要换算请告知再映射）
- workflow_dispatch 支持手动重跑。
- 并发控制：concurrency group: ingest，cancel-in-progress: true。
- 日志上传：将 ingested 日志作为 artifact 上传，便于排错。
- 告警通知：当前阶段不实现告警通知，后续再扩展。
- 秘密/凭证：CF_ACCOUNT_ID、CF_API_TOKEN、CF_D1_DB_NAME 通过 GitHub Secrets 注入。
- 关键工作流草案文件：.github/workflows/ingest_schedule.yml

## 6. 安全性与 Secrets 管理
- Secrets 使用 GitHub Secrets 注入，日志中不输出 secrets。
- ingestion 的对外端点可在阶段 2/3 引入 API Key 或 OAuth/JWT，当前阶段使用最小暴露原则。
- 未来可在 ingest 管理端增加 IP 白名单或简单鉴权来保护入口。

## 7. 验证、测试与验收
- 验收点
  - ingestion 能通过 D1 写入新抓取的数据，api 能从 D1 读取并返回分页/筛选结果。
  - ArticleModel 在 shared/models.py 与数据库层对齐，端到端测试通过。
  - GH Actions ingest_schedule.yml 在 UTC 时区按计划触发，Secrets 注入正确生效。
- 测试建议
  - D1Adapter 的单元测试（SQL 生成、UPSERT 行为）
  - ingestion 到 API 的集成测试（端到端数据流）
  - contract 测试：shared ArticleModel 的一致性测试

## 8. 阶段性实施路线（概览）
- 阶段 1（1–2 周）: Skeleton + D1 适配基础
  - 新增 ingestor/storage/d1_client.py、ingestor/storage/db.py、ingestor/storage/models.py
  - shared/models.py、api/storage/dao.py 的对接准备
  - ingest/main.py 的最小入口实现
  - .github/workflows/ingest_schedule.yml 的初版草案
- 阶段 2（3–6 周）: 错误处理、日志、认证草案、测试覆盖
- 阶段 3（6+ 周）: 指标、监控、部署方案、可能的微服务分离评估

## 9. 与现有实现的对比与迁移
- 现有 api/main.py、api/v2/routes.py 等保留作为对外 API 的入口，逐步改造为读取 D1 数据。
- ingestion 的数据抓取输出将逐步统一落地到 D1，转换逻辑落在 ingestor/transformers/article_transformer.py。
- 数据契约 ArticleModel 作为共享入口，确保字段对齐和版本向后兼容。

## 10. 附件与参考
- 代表性路径示例（绝对路径）
  - ingestor/main.py
  - ingestor/storage/d1_client.py
  - ingestor/storage/db.py
  - ingestor/storage/models.py
  - shared/models.py
  - api/main.py
  - api/storage/dao.py
  - api/v2/routes.py
  - ARCHITECTURE_DESIGN_ai-daily-collector_v0.1.md (本文件)

## 变更记录
- v0.1: 初始设计草案，覆盖目标、架构、契约、存储、入口、CI/CD、阶段路线等。
