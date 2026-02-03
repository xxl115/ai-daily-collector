#!/bin/bash
# 部署前端到 Cloudflare Pages

echo "🚀 部署 AI Daily 前端到 Cloudflare Pages"
echo "=========================================="

# 检查环境变量 (支持多种写法)
API_TOKEN="${CLOUDFLARE_API_TOKEN}"
if [ -z "$API_TOKEN" ]; then
    API_TOKEN="${CF_API_TOKEN}"
fi

if [ -z "$API_TOKEN" ]; then
    echo "❌ 错误: Cloudflare API Token 未设置"
    echo "请确保 GitHub Secrets 中配置了 CF_API_TOKEN 或 CLOUDFLARE_API_TOKEN"
    exit 1
fi

ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID}"
if [ -z "$ACCOUNT_ID" ]; then
    ACCOUNT_ID="${CF_ACCOUNT_ID}"
fi

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ 错误: Cloudflare Account ID 未设置"
    echo "请确保 GitHub Secrets 中配置了 CF_ACCOUNT_ID 或 CLOUDFLARE_ACCOUNT_ID"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo "   Account ID: ${ACCOUNT_ID:0:8}..."

# 安装 wrangler
echo ""
echo "📦 安装 Wrangler..."
npm install -g wrangler

# 部署
echo ""
echo "🚀 部署到 Cloudflare Pages..."
cd "$(dirname "$0")"

# 创建或更新项目
echo "📝 创建 Pages 项目..."
wrangler pages project create ai-daily-collector --production-branch=master 2>/dev/null || true

# 部署
echo "📤 上传文件..."
wrangler pages deploy . --project-name=ai-daily-collector --commit-dirty=true

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址: https://ai-daily-collector.pages.dev"
echo "=========================================="
