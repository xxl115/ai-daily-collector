#!/bin/bash
# Cloudflare Workers 部署脚本
# 使用方法: 
#   export CF_API_TOKEN="你的token"
#   export CF_ACCOUNT_ID="你的account-id"
#   bash deploy-cf.sh

set -e

echo "🚀 AI Daily Collector - Cloudflare Workers 部署"
echo "================================================"
echo ""

# 检查环境变量
if [ -z "$CF_API_TOKEN" ]; then
    echo "❌ 错误: CF_API_TOKEN 未设置"
    echo ""
    echo "请先获取 Cloudflare API Token:"
    echo "1. 访问: https://dash.cloudflare.com/profile/api-tokens"
    echo "2. 点击 'Create Custom Token'"
    echo "3. 配置权限: Workers and Workers KV:Edit"
    echo "4. 复制 token 并设置:"
    echo "   export CF_API_TOKEN='你的token'"
    echo "   export CF_ACCOUNT_ID='你的account-id'"
    echo ""
    exit 1
fi

if [ -z "$CF_ACCOUNT_ID" ]; then
    echo "❌ 错误: CF_ACCOUNT_ID 未设置"
    echo "请设置: export CF_ACCOUNT_ID='你的account-id'"
    echo "(Account ID 可从 https://dash.cloudflare.com 获取)"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo "   Account ID: ${CF_ACCOUNT_ID:0:8}..."
echo ""

# 设置环境变量
export CLOUDFLARE_API_TOKEN="$CF_API_TOKEN"

# 检查 wrangler
if ! command -v wrangler &> /dev/null; then
    echo "📦 安装 Wrangler..."
    npm install -g wrangler
else
    echo "✅ Wrangler 已安装: $(wrangler --version)"
fi

# 部署
echo ""
echo "🚀 部署中..."
cd "$(dirname "$0")"

# 备份 wrangler.toml
cp wrangler.toml wrangler.toml.bak 2>/dev/null || true

# 更新 wrangler.toml
cat > wrangler.toml << 'TOML'
name = "ai-daily-collector"
main = "./api/cloudflare_worker.js"
compatibility_date = "2024-01-01"

[vars]
TZ = "Asia/Shanghai"
LOG_LEVEL = "INFO"
TOML

# 部署
echo ""
echo "📤 上传 Worker..."
wrangler deploy 2>&1 || {
    echo ""
    echo "❌ 部署失败"
    # 恢复备份
    mv wrangler.toml.bak wrangler.toml 2>/dev/null || true
    exit 1
}

# 恢复原配置
mv wrangler.toml.bak wrangler.toml 2>/dev/null || true

# 测试
echo ""
echo "🧪 测试部署..."
sleep 2

HEALTH=$(curl -s --max-time 10 "https://ai-daily-collector.workers.dev/health" 2>&1 || echo "FAILED")
echo "健康检查: $HEALTH"

echo ""
echo "================================================"
echo "✅ 部署完成!"
echo ""
echo "📝 访问地址:"
echo "   - Worker: https://ai-daily-collector.workers.dev"
echo "   - 健康检查: https://ai-daily-collector.workers.dev/health"
echo "   - API 热点: https://ai-daily-collector.workers.dev/api/hotspots"
echo "   - RSS: https://ai-daily-collector.workers.dev/rss/latest.xml"
echo "================================================"
