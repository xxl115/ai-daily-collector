#!/bin/bash
# quick-install.sh - 一键安装开发工具

echo "🔧 安装 Claude Code 开发工具..."

# 1. 安装系统工具（需要 sudo 密码）
echo "📦 安装系统工具..."
sudo apt update
sudo apt install -y ripgrep fd-find httpie jq

# 2. 安装 Python 开发工具
echo "🐍 安装 Python 工具..."
pip install black flake8 mypy pytest pytest-cov

# 3. 安装 Node.js 工具（如果需要）
echo "📦 安装 Node.js 工具..."
npm install -g @upstash/context7-mcp

# 4. 配置 Claude Code
echo "⚙️ 配置 Claude Code..."

# 备份现有配置
cp ~/.claude/settings.local.json ~/.claude/settings.local.json.backup

# 更新配置
cat > ~/.claude/settings.local.json <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(find:*)",
      "Bash(sqlite3:*)",
      "Bash(env:*)",
      "Bash(echo:*)",
      "Bash(journalctl:*)",
      "Bash(claude:*)",
      "Bash(ls:*)",
      "Bash(curl:*)",
      "Bash(netstat:*)",
      "Bash(ss:*)",
      "Bash(kill:*)",
      "Bash(ripgrep:*)",
      "Bash(fd:*)",
      "Bash(rg:*)",
      "Bash(fdfind:*)"
    ]
  },
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
EOF

echo "✅ 安装完成！"
echo ""
echo "📝 下一步："
echo "1. 重启 Claude Code"
echo "2. 如果需要 GitHub 集成，添加 GitHub Personal Access Token"
echo "3. 运行 'claude --help' 查看帮助"
