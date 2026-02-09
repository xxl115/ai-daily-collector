#!/bin/bash
# install-dev-tools.sh - Claude Code 开发工具安装脚本

set -e

echo "🔧 Claude Code 开发工具安装"
echo "================================"

# 1. 安装 Context7 MCP（代码库分析）
echo ""
echo "📦 1/3 安装 Context7 MCP..."
npm install -g @upstash/context7-mcp
echo "✅ Context7 MCP 已安装"

# 2. 配置 GitHub Personal Access Token
echo ""
echo "📦 2/3 GitHub 集成（可选）"
echo "访问: https://github.com/settings/tokens"
echo "需要权限: repo, read:org"
read -p "粘贴 GitHub Token (直接回车跳过): " GH_TOKEN
if [ -n "$GH_TOKEN" ]; then
    export GITHUB_PERSONAL_ACCESS_TOKEN="$GH_TOKEN"
    echo "✅ GitHub Token 已配置"
else
    echo "⏭️ 跳过 GitHub 配置"
fi

# 3. 安装系统工具
echo ""
echo "📦 3/3 安装系统工具..."
echo "需要 sudo 权限..."

# 安装 ripgrep
if ! command -v rg &> /dev/null; then
    echo "安装 ripgrep..."
    sudo apt update && sudo apt install -y ripgrep
else
    echo "✅ ripgrep 已安装"
fi

# 安装 fd
if ! command -v fd &> /dev/null; then
    echo "安装 fd..."
    sudo apt install -y fd-find
else
    echo "✅ fd 已安装"
fi

# 安装 httpie
if ! command -v http &> /dev/null; then
    echo "安装 httpie..."
    sudo apt install -y httpie
else
    echo "✅ httpie 已安装"
fi

# 安装 jq
if ! command -v jq &> /dev/null; then
    echo "安装 jq..."
    sudo apt install -y jq
else
    echo "✅ jq 已安装"
fi

echo ""
echo "================================"
echo "✅ 所有工具安装完成！"
echo ""
echo "📝 下一步："
echo "1. 重启 Claude Code 终端"
echo "2. 测试 Context7: claude '分析 ai-daily-collector 的架构'"
echo "3. 如果配置了 GitHub: claude '列出 ai-daily-collector 的 open issues'"
