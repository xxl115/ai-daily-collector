#!/bin/bash
# 完整部署脚本 (Worker + Frontend)

echo "🚀 AI Daily Collector - 完整部署"
echo "=================================="

# 检查环境变量
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "❌ 错误: CLOUDFLARE_API_TOKEN 未设置"
    exit 1
fi

if [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
    echo "❌ 错误: CLOUDFLARE_ACCOUNT_ID 未设置"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo "   Account ID: ${CLOUDFLARE_ACCOUNT_ID:0:8}..."

# 安装 wrangler
echo ""
echo "📦 安装 Wrangler..."
npm install -g wrangler

cd "$(dirname "$0")"

# 1. 部署 Worker
echo ""
echo "🚀 步骤 1/2: 部署 Cloudflare Worker..."
wrangler deploy --env production 2>&1 || {
    echo "❌ Worker 部署失败"
    exit 1
}
echo "✅ Worker 部署完成"

# 2. 部署 Frontend
echo ""
echo "🚀 步骤 2/2: 部署 Cloudflare Pages..."
wrangler pages project create ai-daily-collector --production-branch=master 2>/dev/null || true
wrangler pages deploy . --project-name=ai-daily-collector --commit-dirty=true 2>&1 || {
    echo "❌ Frontend 部署失败"
    exit 1
}
echo "✅ Frontend 部署完成"

echo ""
echo "=================================="
echo "✅ 完整部署完成!"
echo ""
echo "🌐 Worker: https://ai-daily-collector.workers.dev"
echo "🌐 Frontend: https://ai-daily-collector.pages.dev"
echo ""
echo "📊 测试:"
echo "   curl https://ai-daily-collector.workers.dev/health"
echo "   curl https://ai-daily-collector.workers.dev/api/hotspots"
echo "=================================="
