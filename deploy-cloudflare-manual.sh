#!/bin/bash
# Cloudflare Workers 手动部署脚本
# 使用方法: bash deploy-cloudflare-manual.sh

set -e

echo "🚀 AI Daily Collector - Cloudflare Workers 部署"
echo "================================================"
echo ""

# 检查环境变量
if [ -z "$CF_API_TOKEN" ]; then
    echo "❌ 错误: CF_API_TOKEN 未设置"
    echo "请设置: export CF_API_TOKEN='你的token'"
    exit 1
fi

if [ -z "$CF_ACCOUNT_ID" ]; then
    echo "❌ 错误: CF_ACCOUNT_ID 未设置"
    echo "请设置: export CF_ACCOUNT_ID='你的account-id'"
    exit 1
fi

if [ -z "$CF_WORKER_NAME" ]; then
    CF_WORKER_NAME="ai-daily-collector"
    echo "⚠️ 使用默认 worker 名称: $CF_WORKER_NAME"
fi

echo "📋 配置信息:"
echo "   Worker 名称: $CF_WORKER_NAME"
echo "   Account ID: ${CF_ACCOUNT_ID:0:8}..."
echo ""

# 1. 安装 Wrangler
echo "📦 步骤 1/4: 安装 Wrangler..."
if ! command -v wrangler &> /dev/null; then
    npm install -g wrangler
else
    echo "   ✅ Wrangler 已安装"
fi

# 2. 登录 Cloudflare
echo ""
echo "🔐 步骤 2/4: 登录 Cloudflare..."
echo "$CF_API_TOKEN" | wrangler login --api-token

# 3. 验证配置
echo ""
echo "✅ 步骤 3/4: 验证配置..."
cd "$(dirname "$0")"
cat wrangler.toml

# 4. 部署
echo ""
echo "🚀 步骤 4/4: 部署到 Cloudflare Workers..."
wrangler deploy --env production

# 5. 测试
echo ""
echo "🧪 测试部署结果..."
echo ""

# 健康检查
echo "1. 健康检查:"
HEALTH=$(curl -s --max-time 10 "https://$CF_WORKER_NAME.workers.dev/health" 2>&1 || echo "请求失败")
if [ "$HEALTH" != "请求失败" ]; then
    echo "   ✅ $HEALTH"
else
    echo "   ⚠️ 健康检查失败，可能是 Workers 还在初始化"
fi

echo ""
echo "================================================"
echo "✅ 部署完成!"
echo ""
echo "📝 下一步:"
echo "   - 健康检查: https://$CF_WORKER_NAME.workers.dev/health"
echo "   - API 端点: https://$CF_WORKER_NAME.workers.dev/api/hotspots"
echo "   - RSS 订阅: https://$CF_WORKER_NAME.workers.dev/rss/latest.xml"
echo ""
