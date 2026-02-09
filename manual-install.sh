#!/bin/bash
# manual-install.sh - 手动安装开发工具

echo "🔧 Claude Code 开发工具 - 手动安装"
echo "===================================="
echo ""

# 1. ripgrep（需要 sudo）
echo "📦 1/3 安装 ripgrep..."
echo "需要输入 sudo 密码:"
sudo apt update
sudo apt install -y ripgrep
echo "✅ ripgrep 安装完成"
echo ""

# 2. 安装 pipx
echo "📦 2/3 安装 pipx..."
sudo apt install -y pipx
pipx ensurepath
echo "✅ pipx 安装完成"
echo ""

# 3. 使用 pipx 安装 Python 工具
echo "📦 3/3 安装 Python 开发工具..."
pipx install black
pipx install pytest
pipx install git-delta
echo "✅ Python 工具安装完成"
echo ""

echo "===================================="
echo "✅ 所有工具安装完成！"
echo ""
echo "📝 重新打开终端，然后运行:"
echo "   rg --version"
echo "   black --version"
echo "   pytest --version"
echo "   delta --version"
