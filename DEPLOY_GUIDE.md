# 部署指南

## 🚀 快速部署到 Cloudflare Workers (推荐)

Cloudflare Workers 免费且已配置好，部署步骤：

### 1. 配置 GitHub Secrets

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

```bash
# Cloudflare API Token (需要以下权限)
# - Cloudflare Workers: Edit
# - Cloudflare KV: Read/Write
CF_API_TOKEN = "your-cloudflare-api-token"

# Cloudflare Account ID (从 Dashboard 获取)
CF_ACCOUNT_ID = "your-account-id"

# Worker 名称
CF_WORKER_NAME = "ai-daily-collector"
```

**获取方式：**
- `CF_ACCOUNT_ID`: Cloudflare Dashboard → Workers & Pages → Settings → Account ID
- `CF_API_TOKEN`: Cloudflare Dashboard → API Tokens → Create Custom Token

```
Cloudflare Workers:Edit
Cloudflare KV:Read/Write
```

### 2. 创建 KV Namespace (可选，用于缓存)

```bash
# 本地安装 wrangler 并登录
npm install -g wrangler
wrangler login

# 创建 KV 命名空间
wrangler kv:namespace create "CACHE"

# 会返回类似:
# [kv-namespacebinding]
# id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# preview_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

然后在 wrangler.toml 中更新 id。

### 3. 推送代码触发部署

```bash
git add .
git commit -m "🚀 Deploy to Cloudflare Workers"
git push origin master
```

GitHub Actions 会自动：
1. 运行 CI 测试
2. 部署到 Cloudflare Workers
3. 发送通知

### 4. 验证部署

```bash
# 测试 health 端点
curl https://ai-daily-collector.<your-subdomain>.workers.dev/health

# 测试热点 API
curl https://ai-daily-collector.<your-subdomain>.workers.dev/api/hotspots
```

---

## 🐳 部署到 Docker (VPS)

### 1. 配置服务器 Secrets

```bash
# GitHub Secrets
SERVER_HOST = "your-server-ip"
SERVER_USER = "root"  # 或其他用户
SERVER_SSH_KEY = "-----BEGIN RSA PRIVATE KEY-----..."
SERVER_PATH = "/opt/ai-daily-collector"
```

### 2. 本地测试

```bash
# 构建镜像
docker build -t ai-daily-collector .

# 运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 推送触发部署

```bash
git commit -m "🚀 Deploy to Docker Server"
git push
```

---

## 📦 一键部署命令

```bash
# 使用 Makefile
make deploy          # 部署到服务器
make deploy-cf       # 部署到 Cloudflare
make deploy-docker   # 部署到 Docker
make deploy-all      # 全部部署

# 查看状态
make status          # 检查服务状态
make logs            # 查看日志
make restart         # 重启服务
```

---

## 🔧 环境变量配置

### 必需
```bash
# 智谱 AI (日报生成)
ZAI_API_KEY = "your-api-key"

# 飞书推送 (可选)
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
FEISHU_APP_ID = "xxx"
FEISHU_APP_SECRET = "xxx"
```

### 可选
```bash
# 缓存
REDIS_URL = "redis://localhost:6379"

# Notion 同步
NOTION_API_KEY = "secret_xxx"
NOTION_PARENT_PAGE_ID = "page_id"

# GitHub
GITHUB_TOKEN = "ghp_xxx"
```

---

## ✅ 验证部署成功

```bash
# API 健康检查
curl https://your-domain/health

# 预期响应:
# {"status": "ok", "version": "1.0.0"}

# 获取热点
curl https://your-domain/api/hotspots | jq '. | head -5'

# RSS 订阅
curl https://your-domain/rss/latest.xml | head -20
```

---

## 📊 部署选项对比

| 方案 | 费用 | 适合 | 难度 |
|------|------|------|------|
| Cloudflare Workers | 免费 | API/小型服务 | ⭐ |
| Docker + VPS | $5-10/月 | 完整服务 | ⭐⭐ |
| Kubernetes | 付费 | 大规模 | ⭐⭐⭐ |
| Railway/Render | 免费/付费 | 快速部署 | ⭐⭐ |

---

## 🐛 常见问题

### Q: Cloudflare 部署失败？
A: 检查 CF_API_TOKEN 权限是否包含 Workers:Edit

### Q: Docker 构建失败？
A: 确保服务器已安装 Docker 和 Docker Compose

### Q: 推送不触发部署？
A: 检查 .github/workflows/deploy.yml 中的分支条件

### Q: 如何回滚？
A: GitHub Actions 历史中找到之前的成功部署，点击 Re-run jobs
