#!/bin/bash
# configure-delta.sh - 配置 delta Git diff 工具

echo "🔧 配置 Git Delta..."

# 1. 查找 delta
DELTA_PATH=$(which delta 2>/dev/null || find /usr/local/bin -name "delta" 2>/dev/null | head -1)

if [ -z "$DELTA_PATH" ]; then
    echo "❌ delta 未找到，请先安装:"
    echo "   cd /tmp"
    echo "   curl -LO https://github.com/dandavison/delta/releases/download/0.18.2/delta-0.18.2-x86_64-unknown-linux-gnu.tar.gz"
    echo "   tar -xzf delta-*.tar.gz"
    echo "   sudo cp delta-*/delta /usr/local/bin/"
    echo "   rm -rf delta-*"
    exit 1
fi

echo "✅ delta 找到: $DELTA_PATH"

# 2. 配置 Git
git config --global core.pager "delta"
git config --global delta.line-numbers true
git config --global delta.navigate true

echo "✅ Git 已配置使用 delta"
echo ""
echo "📝 测试:"
echo "   git diff"
