# 文档导航

> 本文档是项目的文档导航入口。

## 📖 架构文档（必读）

| 文档 | 描述 | 优先级 |
|------|------|--------|
| **[ARCHITECTURE_ALL.md](ARCHITECTURE_ALL.md)** | ✅ **唯一权威架构参考**，包含完整数据流、数据契约、错误处理、分类规则、演进路线 | ⭐⭐⭐ 必读 |
| [openapi.yaml](openapi.yaml) | API 接口契约定义（OpenAPI 3.0 格式） | ⭐⭐ 推荐 |
| [schemas/](schemas/) | JSON Schema 数据契约定义 | ⭐ 参考 |

## 📁 文档分类

### 架构设计

| 文件 | 状态 | 说明 |
|------|------|------|
| `ARCHITECTURE_ALL.md` | ✅ 活跃 | All-in-One 架构总览 |
| `ARCHITECTURE_DIAGRAMS.md` | ⏸️ 待清理 | 架构图（需合并到主文档） |
| `ARCHITECTURE_DESIGN.md` | ⏸️ 待清理 | 设计准则（需合并到主文档） |
| `ARCHITECTURE_REDESIGN.md` | ⏸️ 待清理 | 重新设计提案（阶段 B） |

### 实现计划

| 文件 | 描述 |
|------|------|
| `IMPLEMENTATION_LOG.md` | 实现日志 |
| `IMPLEMENTATION_PLAN_A_B_C.md` | A/B/C 方案概述 |
| `IMPLEMENTATION_PLAN_A_B_C_DETAILED.md` | 详细实现计划 |

### 专项方案

| 文件 | 描述 |
|------|------|
| `CONTENT_PROCESSING_PLAN.md` | 内容处理方案 |
| `API_IMPLEMENTATION_PLAN.md` | API 实现方案 |
| `GITHUB_ACTIONS_CONTENT_PROCESSING_PLAN.md` | CI/CD 方案 |

### 问题排查

| 文件 | 描述 |
|------|------|
| `DEBUGGING_LOG.md` | 调试日志 |

## 📂 代码参考

### 核心脚本

| 路径 | 描述 |
|------|------|
| `scripts/content_processor.py` | 主内容处理器 |
| `scripts/extractors/` | 提取器实现 |
| `scripts/summarizers/` | 摘要生成器 |
| `scripts/classifiers/` | 分类器 |
| `scripts/report_generator.py` | 日报生成器 |

### 入口与 API

| 路径 | 描述 |
|------|------|
| `api/main.py` | FastAPI 入口 |
| `api/v2/` | Cloudflare Worker v2 |

### 工作流

| 路径 | 描述 |
|------|------|
| `.github/workflows/content-processing.yml` | GitHub Actions CI/CD |
| `ingestor/` | 数据摄入模块 |

## 🚀 快速开始

```bash
# 运行完整工作流
python scripts/content_processor.py --input ai/articles/original

# 启动 API 服务
make api

# 查看 API 文档
open http://localhost:8000/docs
```

## 📊 数据目录

```
ai/
├── articles/
│   ├── original/    # 原始 Markdown 文件
│   └── processed/   # 处理后的 JSON 文件
└── daily/
    ├── REPORT.md           # 日报
    └── REPORT_METRICS.md   # 处理指标
```

## 🔗 相关链接

- [README.md](../README.md) - 项目主 README
- [CHANGELOG.md](../CHANGELOG.md) - 版本变更记录
- [pyproject.toml](../pyproject.toml) - Python 项目配置

---

*本文档最后更新：2026-02-14*
