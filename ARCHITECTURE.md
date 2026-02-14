# ⚠️ 文档已废弃

> **本文档已废弃，请参考 [docs/ARCHITECTURE_ALL.md](docs/ARCHITECTURE_ALL.md)**

---

## 历史版本说明

本文档是 v2.0 版本的架构文档（最后更新：2024-01-15），已被新架构文档替代。

### 主要变更

| 变更项 | 旧版（本文档） | 新版 |
|--------|---------------|------|
| 权威文档 | `ARCHITECTURE.md` | `docs/ARCHITECTURE_ALL.md` |
| 数据存储 | Cloudflare D1 | 本地文件系统（当前） |
| 抓取器数量 | 16 个 | 简化为 2 个（Trafilatura/Jina） |
| 分类方式 | 手动分类 | BGE 嵌入向量分类 |
| 演进阶段 | 单一阶段 | A/B/C 三阶段演进 |

### 迁移说明

新版文档（`docs/ARCHITECTURE_ALL.md`）提供了：
- ✅ 清晰的实现状态表（已实现/进行中/计划）
- ✅ 详细的批处理数据流说明
- ✅ 完整的数据契约（含 version 字段）
- ✅ 错误处理与容错设计
- ✅ 分类规则透明化
- ✅ 阶段 B/C 的时间表

---

## 快速跳转到新版文档

👉 **[docs/ARCHITECTURE_ALL.md](docs/ARCHITECTURE_ALL.md)** - 唯一权威架构参考

---

*本文档最后更新：2026-02-14*  
*状态：已废弃*
