# Cloudflare Python Workers 部署指南

> 如何将 AI Daily Collector 部署到 Cloudflare Workers（Python 运行时）

## 📋 前置条件

1. **Cloudflare 账号**（免费版即可）
2. **GitHub 仓库**（已推送代码）
3. **已安装 Wrangler CLI**（可选，用于本地测试）

---

## 🚀 快速开始

### 步骤 1：创建 D1 数据库

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 创建 D1 数据库
wrangler d1 create ai-daily-collector

# 输出示例：
# ✅ Successfully created DB 'ai-daily-collector'
# [[d1_databases]]
# binding = "DB"
# database_name = "ai-daily-collector"
# database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**重要**：记下 `database_id`，后面需要用到。

---

### 步骤 2：初始化数据库表

```bash
# 创建 schema.sql 文件
cat > schema.sql << 'EOF'
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT NOT NULL,
    published_at TEXT,
    source TEXT NOT NULL,
    categories TEXT,
    tags TEXT,
    summary TEXT,
    raw_markdown TEXT,
    ingested_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_ingested_at ON articles(ingested_at);
EOF

# 执行 SQL 创建表
wrangler d1 execute ai-daily-collector --file=./schema.sql
```

---

### 步骤 3：更新配置

编辑 `wrangler.toml`，填入你的数据库 ID：

```toml
name = "ai-daily-collector-api"
main = "worker.py"
compatibility_date = "2024-01-15"

[[d1_databases]]
binding = "DB"
database_name = "ai-daily-collector"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # ← 替换为你的 ID
```

---

### 步骤 4：配置 GitHub Secrets

在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 值 | 获取方式 |
|------------|-----|---------|
| `CF_ACCOUNT_ID` | 你的 Cloudflare 账户 ID | Cloudflare Dashboard 右下角 |
| `CF_API_TOKEN` | API 令牌 | Cloudflare → My Profile → API Tokens → Create Token |
| `CF_D1_DATABASE_ID` | D1 数据库 ID | 步骤 1 的输出 |

**创建 API Token 步骤**：
1. 进入 https://dash.cloudflare.com/profile/api-tokens
2. 点击 "Create Token"
3. 使用模板 "Edit Cloudflare Workers"
4. 权限包括：
   - Cloudflare Workers:Edit
   - Account:Read
   - D1:Edit
5. 复制生成的 Token

---

### 步骤 5：部署

#### 方式 A：通过 GitHub Actions（推荐）

```bash
# 1. 推送代码到 main/master 分支
git add .
git commit -m "Setup Cloudflare Python Workers"
git push origin main

# 2. GitHub Actions 会自动触发部署
# 查看部署状态：GitHub → Actions → Deploy Cloudflare Worker
```

#### 方式 B：本地部署

```bash
# 确保已安装 wrangler
npm install -g wrangler

# 登录
wrangler login

# 部署
wrangler deploy

# 部署成功后，会显示访问地址
# 例如：https://ai-daily-collector-api.your-subdomain.workers.dev
```

---

## ✅ 验证部署

### 1. 测试健康检查

```bash
curl https://ai-daily-collector-api.your-subdomain.workers.dev/health

# 预期响应：
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### 2. 测试 API 端点

```bash
# 获取文章列表
curl https://ai-daily-collector-api.your-subdomain.workers.dev/api/v2/articles?page_size=5

# 获取统计信息
curl https://ai-daily-collector-api.your-subdomain.workers.dev/api/v2/stats

# 获取来源列表
curl https://ai-daily-collector-api.your-subdomain.workers.dev/api/v2/sources
```

---

## 🔄 配置定时摄取

数据摄取通过 GitHub Actions 定时触发，与 Workers 部署是分开的。

### 检查摄取工作流

确保 `.github/workflows/ingest_schedule.yml` 已配置：

```yaml
name: Ingest Schedule

on:
  schedule:
    - cron: '0 18 * * *'  # 每天 UTC 18:00
  workflow_dispatch:       # 支持手动触发

# Secrets 已自动从环境继承
```

### 手动触发摄取

```bash
# GitHub CLI
gh workflow run ingest_schedule.yml

# 或在 GitHub 页面操作：
# Actions → Ingest Schedule → Run workflow
```

---

## 📊 架构概览

部署后的架构：

```
GitHub Actions (定时任务)
    │
    ▼ (Python ingestion)
Cloudflare D1 (数据存储)
    ▲
    │ (HTTP API)
Cloudflare Workers (Python)
    │
    ▼
客户端 (Web/App/Curl)
```

---

## 🔧 故障排除

### 问题 1：部署失败 "database_id not found"

**原因**：`wrangler.toml` 中的 database_id 不正确

**解决**：
```bash
# 查看数据库列表
wrangler d1 list

# 复制正确的 ID 到 wrangler.toml
```

### 问题 2：API 返回 "Database not available"

**原因**：D1 绑定未正确配置

**解决**：
1. 检查 `wrangler.toml` 中的 `[[d1_databases]]` 部分
2. 确认 `binding = "DB"` 与 `worker.py` 中的 `env.DB` 匹配
3. 重新部署

### 问题 3：GitHub Actions 部署失败

**原因**：Secrets 未设置或权限不足

**解决**：
1. 检查 GitHub Secrets 是否已添加（CF_ACCOUNT_ID, CF_API_TOKEN, CF_D1_DATABASE_ID）
2. 确认 API Token 有以下权限：
   - Cloudflare Workers:Edit
   - D1:Edit
   - Account:Read

### 问题 4：健康检查通过但 API 返回空数据

**原因**：数据库中没有数据

**解决**：
1. 先运行一次摄取任务：
   ```bash
   # 本地测试摄取
   DATABASE_PROVIDER=d1 CF_ACCOUNT_ID=xxx CF_D1_DATABASE_ID=xxx CF_API_TOKEN=xxx \
     python ingestor/main.py --dry-run
   ```
2. 或等待定时任务执行（UTC 18:00）
3. 检查摄取日志：GitHub Actions → Ingest Schedule → 查看最新运行

---

## 📈 监控和日志

### 查看 Workers 日志

```bash
# 实时查看日志
wrangler tail

# 或者使用 Cloudflare Dashboard
# Workers & Pages → ai-daily-collector-api → Logs
```

### 查看 D1 数据库

```bash
# 查询表结构
wrangler d1 execute ai-daily-collector --command=".schema"

# 查看文章数量
wrangler d1 execute ai-daily-collector --command="SELECT COUNT(*) FROM articles"

# 查看最近的文章
wrangler d1 execute ai-daily-collector --command="SELECT title, source, ingested_at FROM articles ORDER BY ingested_at DESC LIMIT 5"
```

---

## 🔄 更新部署

修改代码后，推送到 main 分支会自动触发重新部署：

```bash
git add .
git commit -m "Update API endpoints"
git push origin main

# GitHub Actions 会自动部署
```

---

## 🗑️ 清理资源

如需删除部署：

```bash
# 删除 Worker
wrangler delete

# 删除 D1 数据库（⚠️ 数据会丢失）
wrangler d1 delete ai-daily-collector
```

---

## 📚 参考文档

- [Cloudflare Workers Python](https://developers.cloudflare.com/workers/languages/python/)
- [Cloudflare D1 文档](https://developers.cloudflare.com/d1/)
- [Wrangler CLI 文档](https://developers.cloudflare.com/workers/wrangler/)

---

**完成！** 你现在拥有一个完全基于 Cloudflare 的无服务器架构：
- ✅ Python Workers 提供 API
- ✅ D1 数据库存储数据
- ✅ GitHub Actions 定时摄取
- ✅ 全球边缘节点加速
