# Cloudflare Workers 快速部署指南

## 步骤 1: 获取 Cloudflare 配置

### 1.1 获取 API Token

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. 点击 **"Create Token"**
3. 选择 **"Edit Cloudflare Workers"** 模板
4. 设置权限:
   - Account: Workers and R2: Edit
   - Workers KV: Read and Write
5. 点击 **"Continue to summary"**
6. 点击 **"Create Token"**
7. **复制生成的 Token**（只显示一次！）

### 1.2 获取 Account ID

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 右侧面板显示 **Account ID**
3. 复制该 ID

---

## 步骤 2: 配置 GitHub Secrets

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 中添加:

| Secret 名称 | 值 |
|------------|-----|
| `CF_API_TOKEN` | 你的 Cloudflare API Token |
| `CF_ACCOUNT_ID` | 你的 Cloudflare Account ID |
| `CF_WORKER_NAME` | `ai-daily-collector` (或自定义) |

---

## 步骤 3: 运行部署

**方法 1: GitHub Actions 自动部署**

```bash
git add .
git commit -m "Add Cloudflare Workers deployment"
git push origin master
```

访问 https://github.com/你的用户名/ai-daily-collector/actions 查看进度。

**方法 2: 本地脚本部署**

```bash
# 1. 克隆仓库
git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 2. 安装依赖
npm install -g wrangler

# 3. 登录 Cloudflare
wrangler login

# 4. 运行部署脚本
bash scripts/deploy-cloudflare.sh
```

---

## 步骤 4: 验证部署

部署成功后，访问:

- **Worker URL**: `https://ai-daily-collector.workers.dev`
- **健康检查**: `https://ai-daily-collector.workers.dev/health`
- **API 文档**: `https://ai-daily-collector.workers.dev/api/stats`

---

## 可用端点

| 端点 | 说明 | 示例 |
|------|------|------|
| `GET /health` | 健康检查 | `https://ai-daily-collector.workers.dev/health` |
| `GET /api/hotspots` | 热点列表 | `https://ai-daily-collector.workers.dev/api/hotspots` |
| `GET /api/v2ex` | V2EX 热门 | `https://ai-daily-collector.workers.dev/api/v2ex` |
| `GET /api/reddit` | Reddit 热门 | `https://ai-daily-collector.workers.dev/api/reddit` |
| `GET /api/newsnow` | 中文平台 | `https://ai-daily-collector.workers.dev/api/newsnow` |
| `GET /api/github` | GitHub Trending | `https://ai-daily-collector.workers.dev/api/github` |
| `GET /rss` | RSS Feed | `https://ai-daily-collector.workers.dev/rss` |
| `GET /rss/latest` | 最新 RSS | `https://ai-daily-collector.workers.dev/rss/latest` |
| `GET /api/stats` | 统计信息 | `https://ai-daily-collector.workers.dev/api/stats` |

---

## 故障排除

### 问题 1: KV 命名空间未配置

```
Error: Missing binding for KV namespace "CACHE"
```

**解决**: 运行 KV 创建命令
```bash
wrangler kv:namespace create "CACHE"
```

### 问题 2: 权限不足

```
Error: You do not have permission to deploy workers
```

**解决**: 确保 API Token 有 Workers Edit 权限

### 问题 3: 域名冲突

```
Error: A worker with this name already exists
```

**解决**: 修改 `wrangler.toml` 中的 `name` 字段

### 问题 4: 部署超时

```
Error: Deployment failed due to timeout
```

**解决**: 减少 Worker 代码体积，或使用 `wrangler deploy --no-bundle`

---

## 高级配置

### 自定义域名

```bash
# 绑定自定义域名
wrangler routes add "https://api.your-domain.com/*" --zone-name=your-domain.com
```

或在 Dashboard 中配置:
1. 进入 Workers & Pages
2. 点击你的 Worker
3. Settings → Domains & Routes
4. Add → Custom Domain

### 环境变量

在 `wrangler.toml` 中配置:

```toml
[vars]
TZ = "Asia/Shanghai"
LOG_LEVEL = "INFO"
```

### 缓存配置

KV 缓存 TTL:
- 热点列表: 3600 秒 (1小时)
- RSS Feed: 1800 秒 (30分钟)
- 统计信息: 300 秒 (5分钟)

---

## 监控

### 查看日志

```bash
wrangler tail
```

### 查看部署历史

访问 [Cloudflare Dashboard](https://dash.cloudflare.com/workers-and-pages) → 你的 Worker → Deployments

---

## 费用说明

Cloudflare Workers **免费额度**:
- 每天 100,000 次请求
- 1GB KV 读取
- 1GB KV 写入

大多数个人使用场景下完全免费。

---

## 联系支持

如果遇到问题:
1. 查看 [Cloudflare 文档](https://developers.cloudflare.com/workers/)
2. 搜索 [Cloudflare Community](https://community.cloudflare.com/)
3. 查看 [GitHub Issues](https://github.com/xxl115/ai-daily-collector/issues)
