#!/bin/bash
# -*- coding: utf-8 -*-
"""
Cloudflare Workers 部署脚本

使用方式:
1. 交互式部署: bash deploy-cloudflare.sh
2. 自动化部署: CF_API_TOKEN=xxx CF_ACCOUNT_ID=xxx bash deploy-cloudflare.sh

前置要求:
1. 安装 Node.js 和 npm
2. 安装 Wrangler: npm install -g wrangler
3. 登录 Cloudflare: wrangler login
"""

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_color() {
    color=$1
    text=$2
    echo -e "${color}${text}${NC}"
}

echo_step() {
    echo_color $BLUE "📋 $1"
}

echo_success() {
    echo_color $GREEN "✅ $1"
}

echo_warning() {
    echo_color $YELLOW "⚠️ $1"
}

echo_error() {
    echo_color $RED "❌ $1"
}

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WRANGLER_TOML="$PROJECT_DIR/wrangler.toml"
CF_API_TOKEN="${CF_API_TOKEN:-}"
CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-}"
WORKER_NAME="ai-daily-collector"

# 检查依赖
check_dependencies() {
    echo_step "检查依赖..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo_error "未安装 Node.js"
        echo "请安装 Node.js: https://nodejs.org/"
        exit 1
    fi
    echo_success "Node.js: $(node -v)"
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo_error "未安装 npm"
        exit 1
    fi
    echo_success "npm: $(npm -v)"
    
    # 检查 Wrangler
    if ! command -v wrangler &> /dev/null; then
        echo_warning "未安装 Wrangler，正在安装..."
        npm install -g wrangler
    fi
    echo_success "Wrangler: $(wrangler --version)"
}

# 检查登录状态
check_login() {
    echo_step "检查 Cloudflare 登录状态..."
    
    if [ -z "$CF_API_TOKEN" ]; then
        echo_warning "未设置 CF_API_TOKEN 环境变量"
        echo "请选择登录方式:"
        echo "1. 使用 Wrangler 交互式登录"
        echo "2. 使用 API Token"
        read -p "请选择 (1/2): " choice
        
        if [ "$choice" = "2" ]; then
            read -p "请输入 Cloudflare API Token: " CF_API_TOKEN
            export CF_API_TOKEN
        else
            echo_step "请在浏览器中完成登录..."
            wrangler login
        fi
    else
        echo_success "已设置 API Token"
    fi
    
    # 验证登录
    if ! echo "$CF_API_TOKEN" | wrangler login --api-token 2>/dev/null; then
        echo_warning "API Token 验证失败，尝试交互式登录..."
        wrangler login
    fi
}

# 获取 Account ID
get_account_id() {
    echo_step "获取 Cloudflare Account ID..."
    
    if [ -z "$CF_ACCOUNT_ID" ]; then
        echo_warning "未设置 CF_ACCOUNT_ID 环境变量"
        echo "尝试从 Wrangler 配置中获取..."
        
        CF_ACCOUNT_ID=$(wrangler whoami 2>/dev/null | grep -oP 'Account ID: \K[a-z0-9-]+' | head -1 || echo "")
        
        if [ -z "$CF_ACCOUNT_ID" ]; then
            echo_error "无法获取 Account ID"
            echo "请访问: https://dash.cloudflare.com/"
            echo "在右侧面板中找到 Account ID"
            read -p "请输入 Account ID: " CF_ACCOUNT_ID
        fi
    fi
    
    export CF_ACCOUNT_ID
    echo_success "Account ID: $CF_ACCOUNT_ID"
}

# 创建 KV 命名空间
create_kv_namespace() {
    echo_step "创建 KV 命名空间（用于缓存）..."
    
    # 检查是否已存在
    if wrangler kv:namespace list 2>/dev/null | grep -q "CACHE"; then
        echo_success "KV 命名空间 'CACHE' 已存在"
        KV_ID=$(wrangler kv:namespace list 2>/dev/null | grep -A1 "CACHE" | grep "id:" | awk '{print $2}' | head -1)
    else
        echo "正在创建 KV 命名空间 'CACHE'..."
        KV_OUTPUT=$(wrangler kv:namespace create "CACHE" 2>&1 || echo "")
        
        # 提取 ID
        KV_ID=$(echo "$KV_OUTPUT" | grep -oP 'id:\s*\K[a-z0-9-]+' | head -1 || echo "")
        
        if [ -z "$KV_ID" ]; then
            echo_warning "无法自动创建 KV 命名空间"
            echo "请手动创建: wrangler kv:namespace create \"CACHE\""
            read -p "请输入 KV Namespace ID (或按 Enter 跳过): " KV_ID
        else
            echo_success "KV 命名空间创建成功: $KV_ID"
        fi
    fi
    
    # 更新 wrangler.toml
    if [ -n "$KV_ID" ]; then
        echo_step "更新 wrangler.toml..."
        sed -i "s/YOUR_KV_NAMESPACE_ID/$KV_ID/g" "$WRANGLER_TOML"
        echo_success "已更新 KV ID: $KV_ID"
    fi
}

# 配置环境变量
configure_env() {
    echo_step "配置环境变量..."
    
    # 创建 .cloudflare 环境文件
    ENV_FILE="$PROJECT_DIR/.cloudflare.env"
    cat > "$ENV_FILE" << EOF
# Cloudflare Workers 环境变量
# 请勿将此文件提交到 GitHub

CF_ACCOUNT_ID=$CF_ACCOUNT_ID
CF_WORKER_NAME=$WORKER_NAME
EOF
    
    echo_success "已创建 $ENV_FILE"
    echo "请添加以下 Secrets 到 GitHub:"
    echo "  - CF_API_TOKEN"
    echo "  - CF_ACCOUNT_ID"
}

# 部署到生产环境
deploy_production() {
    echo_step "部署到 Cloudflare Workers..."
    
    cd "$PROJECT_DIR"
    
    # 检查 wrangler.toml
    if [ ! -f "wrangler.toml" ]; then
        echo_error "未找到 wrangler.toml"
        exit 1
    fi
    
    # 验证 KV 配置
    if grep -q "YOUR_KV_NAMESPACE_ID" wrangler.toml; then
        echo_warning "KV Namespace ID 未配置"
        echo "请先运行: bash deploy-cloudflare.sh --setup"
        exit 1
    fi
    
    # 部署
    echo "正在部署到生产环境..."
    if wrangler deploy --env production; then
        echo_success "部署成功!"
        echo ""
        echo "🌐 Worker URL:"
        echo "  https://$WORKER_NAME.workers.dev"
        echo ""
        echo "📋 可用端点:"
        echo "  - GET /health"
        echo "  - GET /api/hotspots"
        echo "  - GET /api/v2ex"
        echo "  - GET /api/reddit"
        echo "  - GET /api/newsnow"
        echo "  - GET /api/github"
        echo "  - GET /rss"
        echo "  - GET /api/stats"
    else
        echo_error "部署失败"
        exit 1
    fi
}

# 开发模式预览
preview_dev() {
    echo_step "启动开发模式预览..."
    
    cd "$PROJECT_DIR"
    wrangler dev
}

# 测试部署
test_deployment() {
    echo_step "测试部署结果..."
    
    WORKER_URL="https://$WORKER_NAME.workers.dev"
    
    # 测试健康检查
    echo "测试 /health..."
    if curl -s "$WORKER_URL/health" | grep -q "ok"; then
        echo_success "健康检查通过"
    else
        echo_warning "健康检查失败"
    fi
    
    # 测试统计信息
    echo "测试 /api/stats..."
    STATS=$(curl -s "$WORKER_URL/api/stats" 2>/dev/null | head -c 500 || echo "")
    if [ -n "$STATS" ]; then
        echo_success "统计信息获取成功"
        echo "$STATS" | head -c 200
        echo "..."
    else
        echo_warning "统计信息获取失败"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
Cloudflare Workers 部署脚本

使用方式:
  $0              # 交互式部署
  $0 --setup      # 设置 KV 命名空间
  $0 --deploy     # 直接部署
  $0 --preview    # 开发模式预览
  $0 --test       # 测试部署
  $0 --help       # 显示帮助

环境变量:
  CF_API_TOKEN    # Cloudflare API Token
  CF_ACCOUNT_ID   # Cloudflare Account ID

示例:
  # 交互式部署
  bash deploy-cloudflare.sh
  
  # 自动化部署
  CF_API_TOKEN=xxx CF_ACCOUNT_ID=xxx bash deploy-cloudflare.sh --deploy

EOF
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "  🚀 Cloudflare Workers 部署脚本"
    echo "========================================"
    echo ""
    
    case "${1:-}" in
        --setup)
            check_dependencies
            check_login
            get_account_id
            create_kv_namespace
            configure_env
            ;;
        --deploy)
            check_dependencies
            deploy_production
            ;;
        --preview)
            check_dependencies
            preview_dev
            ;;
        --test)
            test_deployment
            ;;
        --help|-h)
            show_help
            ;;
        "")
            check_dependencies
            check_login
            get_account_id
            create_kv_namespace
            configure_env
            deploy_production
            test_deployment
            ;;
        *)
            echo_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
    
    echo ""
    echo "========================================"
    echo "  ✅ 操作完成!"
    echo "========================================"
    echo ""
}

main "$@"
