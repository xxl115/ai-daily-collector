#!/bin/bash
# 部署前端到 Cloudflare Pages

echo "🚀 部署 AI Daily 前端到 Cloudflare Pages"
echo "=========================================="

# 检查参数
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

# 安装 wrangler
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
wrangler pages deploy . --project-name=ai-daily-collector

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址: https://ai-daily-collector.pages.dev"
echo "=========================================="
