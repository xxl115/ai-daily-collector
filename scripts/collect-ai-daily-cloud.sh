#!/bin/bash
# AI Daily Collector - 云端增强版（使用 Python 配置驱动）
# 从 sources.yaml 读取配置，支持中文数据源

set -e

echo "============================================"
echo "AI Daily Collector (Cloud Enhanced)"
echo "日期: $(date +%Y-%m-%d)"
echo "============================================"
echo ""

# 运行 Python 采集脚本（从 sources.yaml 读取配置）
python3 scripts/collect-for-cloud.py --total-limit 50

echo ""
echo "🔄 提交到 GitHub..."

# 配置 git 用户信息（使用 GitHub Actions bot）
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

# 提交新文件
DATE=$(date +%Y-%m-%d)
ARTICLE_DIR="ai/articles/original/${DATE}"

if [ -d "$ARTICLE_DIR" ]; then
    git add "$ARTICLE_DIR/"

    if git diff --cached --quiet; then
        echo "无新内容需要提交"
    else
        git commit -m "AI Daily: $DATE - 云端采集（配置驱动）" || echo "提交失败"

        # 配置远程 URL 使用 token 认证
        git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/xxl115/ai-daily-collector.git"
        git push origin master || echo "推送失败"
    fi
else
    echo "⚠️ 未生成文章目录: $ARTICLE_DIR"
fi

echo ""
echo "✅ 全部完成!"
