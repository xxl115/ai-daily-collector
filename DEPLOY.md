# 部署指南

## 目录

- [Docker 部署](#docker-部署)
- [GitHub Actions 自动部署](#github-actions-自动部署)
- [手动服务器部署](#手动服务器部署)
- [云平台部署](#云平台部署)
- [环境变量配置](#环境变量配置)

---

## Docker 部署

### 1. 快速启动

```bash
# 克隆项目
git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 创建环境变量
cp .env.development .env
# 编辑 .env 文件，填入必要的 API Key

# 启动服务
docker-compose up -d
```

### 2. 查看日志

```bash
docker-compose logs -f
```

### 3. 停止服务

```bash
docker-compose down
```

---

## GitHub Actions 自动部署

### 前提条件

1. **Docker Hub 账号**（用于推送镜像）
2. **目标服务器**（VPS/云服务器）

### 步骤

#### 1. 配置 Docker Hub Secrets

在 GitHub 仓库设置中添加以下 Secrets:

| Secret 名称 | 说明 |
|------------|------|
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token |

获取 Docker Hub Token:
1. 访问 [Docker Hub Settings](https://hub.docker.com/settings/security)
2. 点击 "New Access Token"
3. 复制生成的 Token

#### 2. 配置服务器 Secrets

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `SERVER_HOST` | 服务器 IP 地址 | `192.168.1.100` |
| `SERVER_USER` | SSH 用户名 | `ubuntu` |
| `SERVER_SSH_KEY` | SSH 私钥内容 | `-----BEGIN RSA PRIVATE KEY...` |
| `SERVER_PATH` | 项目部署路径 | `/opt/ai-daily-collector` |

#### 3. 配置 GitHub Actions

确保启用 workflows:
1. 进入仓库 Settings → Actions → General
2. 确保 "Read and write permissions" 已启用
3. 保存设置

#### 4. 触发部署

```bash
# 推送代码到 master 分支
git add .
git commit -m "Update"
git push origin master
```

GitHub Actions 会自动:
1. 运行测试和代码检查
2. 构建 Docker 镜像
3. 推送到 Docker Hub
4. 连接到服务器并部署

#### 5. 查看部署状态

访问 https://github.com/你的用户名/ai-daily-collector/actions

---

## 手动服务器部署

### 1. 连接服务器

```bash
ssh ubuntu@your-server-ip
```

### 2. 安装 Docker

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 部署项目

```bash
# 创建部署目录
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 创建环境变量
sudo cp .env.development .env
sudo nano .env

# 启动服务
docker-compose up -d
```

### 4. 配置 Nginx（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. 配置 SSL（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 云平台部署

### 1. Vercel（无服务器）

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录并部署
vercel login
vercel --prod
```

**注意**: Vercel 适合无状态服务，需要使用外部数据库。

### 2. Railway

1. 登录 [Railway](https://railway.app)
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择你的仓库
4. 配置环境变量
5. 点击 "Deploy"

### 3. Render

1. 登录 [Render](https://render.com)
2. 点击 "New" → "Web Service"
3. 连接 GitHub 仓库
4. 配置:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. 添加环境变量
6. 点击 "Create Web Service"

### 4. Fly.io

```bash
# 安装 Fly.io CLI
curl -L https://fly.io/install.sh | sh

# 登录并创建应用
fly auth login
fly apps create ai-daily-collector

# 部署
fly deploy
```

### 5. Coolify

1. 自托管 Coolify 或使用托管服务
2. 创建新项目，连接 GitHub 仓库
3. 配置:
   - Docker Compose 文件
   - 环境变量
4. 启用自动部署

### 6. Zeabur

1. 登录 [Zeabur](https://zeabur.com)
2. 点击 "New Project"
3. 选择 GitHub 仓库
4. 选择服务类型: "Docker"
5. 配置环境变量
6. 点击 "Deploy"

---

## 环境变量配置

### 必须配置

```bash
# Zhipu AI (用于总结生成)
ZAI_API_KEY=your_zhipu_api_key

# 飞书推送（可选）
FEISHU_WEBHOOK_URL=your_feishu_webhook_url

# 钉钉推送（可选）
DINGTALK_WEBHOOK_URL=your_dingtalk_webhook_url

# 企业微信推送（可选）
WEWORK_WEBHOOK_URL=your_wework_webhook_url

# Telegram 推送（可选）
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 可选配置

```bash
# Notion（用于保存日报）
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id

# Redis 缓存（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# 代理配置（可选）
PROXY_URL=http://your-proxy:7890
```

### 在 Docker Compose 中配置

```yaml
version: '3.8'

services:
  ai-daily:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - FEISHU_WEBHOOK_URL=${FEISHU_WEBHOOK_URL}
      - TZ=Asia/Shanghai
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
    restart: unless-stopped
```

---

## 监控和维护

### 检查服务状态

```bash
# Docker 状态
docker-compose ps

# API 健康检查
curl http://localhost:8000/health

# 查看日志
docker-compose logs -f --tail=100
```

### 备份数据

```bash
# 备份数据目录
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/

# 备份 Docker 镜像
docker save -o ai-daily-collector.tar.gz $DOCKERHUB_USERNAME/ai-daily-collector:latest
```

### 更新服务

```bash
# 拉取最新代码
git pull origin master

# 重建并重启
docker-compose down
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

### 监控资源使用

```bash
# 查看资源使用
docker stats

# 查看磁盘使用
df -h

# 查看 Docker 磁盘使用
docker system df
```

---

## 故障排除

### 1. Docker 构建失败

```bash
# 清理 Docker 构建缓存
docker builder prune -a

# 重新构建
docker-compose build --no-cache
```

### 2. 端口被占用

```bash
# 查看端口占用
lsof -i:8000

# 修改端口
# 编辑 docker-compose.yml 中的端口映射
```

### 3. 权限问题

```bash
# 创建数据目录并设置权限
mkdir -p data
chmod -R 777 data
```

### 4. 内存不足

```bash
# 查看内存使用
free -h

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 安全建议

1. **不要提交 .env 文件到 GitHub**
2. **定期更新 API Key**
3. **使用 HTTPS**
4. **限制服务器 SSH 访问**
5. **定期备份数据**
6. **启用防火墙**
