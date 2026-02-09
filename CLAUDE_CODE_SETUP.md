# Claude Code 开发效率提升配置

> 创建日期: 2026-02-09
> 目标: 提升 Claude Code 开发效率

---

## 🔧 已安装的配置

### 模型配置
- **默认模型**: GLM-4.7 (智谱 AI)
- **Base URL**: https://open.bigmodel.cn/api/anthropic
- **位置**: `~/.claude/settings.json`

### 权限配置
- 已配置 `settings.local.json`
- 允许的 Bash 命令: find, sqlite3, env, curl, netstat, ss, kill 等

---

## 📦 推荐安装的 MCP 服务器

### 1. 🔥 必装 - Context7
**功能**: 代码库上下文分析，让 AI 更好地理解项目结构

**安装**:
```bash
# 安装
npx -y @upstash/context7-mcp

# 在 Claude Code 中配置
# 添加到 ~/.claude/settings.local.json 的 mcpServers 节
```

**配置**:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

**效果**: AI 可以理解整个代码库结构，提供更准确的建议

---

### 2. 🐙 GitHub 集成
**功能**: 直接在对话中操作 GitHub（PR、Issue、代码搜索）

**安装**:
```bash
# 需要 GitHub Personal Access Token
export GITHUB_PERSONAL_ACCESS_TOKEN="your-token"
```

**配置**:
```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

**可用命令**:
- `gh issue list` - 列出 Issues
- `gh pr list` - 列出 PRs
- `gh repo view` - 查看仓库
- 搜索代码、创建 Issue 等

---

### 3. 📝 实用 MCP 工具箱

| MCP | 功能 | 推荐度 | 安装命令 |
|-----|------|--------|----------|
| **Context7** | 代码库分析 | ⭐⭐⭐⭐⭐ | `npx -y @upstash/context7-mcp` |
| **GitHub** | GitHub 操作 | ⭐⭐⭐⭐⭐ | 配置 token |
| **GitLab** | GitLab 操作 | ⭐⭐⭐ | 配置 token |
| **Slack** | Slack 通知 | ⭐⭐⭐ | 配置 token |
| **Linear** | 项目管理 | ⭐⭐⭐ | 配置 token |
| **Playwright** | 浏览器测试 | ⭐⭐⭐⭐ | `npm i -D playwright` |

---

## 🛠️ 推荐安装的 CLI 工具

### 系统工具
```bash
# 搜索和文件处理
sudo apt install ripgrep fd-find

# Git 增强
pip install git-delta  # 更好的 diff

# 代码搜索
cargo install greptile  # AI 代码搜索
```

### 开发工具
```bash
# Docker 和容器
sudo apt install docker.io docker-compose

# 网络工具
sudo apt install curl wget httpie jq

# Python 开发
pip install black flake8 mypy pytest
```

---

## 🎯 项目配置

### 为 ai-daily-collector 配置专属设置

在项目根目录创建 `.claude/` 配置：

```bash
mkdir -p /home/young/code/ai-daily-collector/.claude
```

创建 `settings.json`:
```json
{
  "project": {
    "name": "AI Daily Collector",
    "description": "Automated AI news collection system",
    "type": "python"
  },
  "agents": {
    "reviewer": {
      "description": "Reviews code changes",
      "prompt": "You are a code reviewer. Focus on: security, performance, code quality."
    },
    "tester": {
      "description": "Writes and runs tests",
      "prompt": "You are a test engineer. Write comprehensive unit and integration tests."
    }
  }
}
```

---

## 📋 快速安装脚本

```bash
#!/bin/bash
# claude-dev-tools.sh - 安装 Claude Code 开发工具

echo "🔧 安装 Claude Code 开发效率工具..."

# 1. 安装 Context7 MCP
echo "📦 安装 Context7 MCP..."
npx -y @upstash/context7-mcp

# 2. 配置 GitHub Token
read -p "输入 GitHub Personal Access Token (可选): " GH_TOKEN
if [ -n "$GH_TOKEN" ]; then
    export GITHUB_PERSONAL_ACCESS_TOKEN="$GH_TOKEN"
    echo "✅ GitHub Token 已配置"
fi

# 3. 更新 Claude 设置
cat >> ~/.claude/settings.local.json <<EOF
,
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
EOF

echo "✅ 安装完成！重启 Claude Code 生效"
```

---

## 🎨 常用 Claude Code 技巧

### 1. 指定 Agent
```bash
# 代码审查
claude --agent reviewer "审查 ai-daily-collector 的代码质量"

# 编写测试
claude --agent tester "为 fetchers 模块编写单元测试"
```

### 2. 自定义 Agent
在 `~/.claude/settings.json` 中添加:
```json
{
  "agents": {
    "frontend": {
      "description": "Frontend developer",
      "prompt": "You are an expert frontend developer. Prefer clean UI/UX."
    },
    "backend": {
      "description": "Backend developer",
      "prompt": "You are an expert backend developer. Focus on API design and performance."
    }
  }
}
```

### 3. 跳过确认
```bash
# 对于自动化脚本
claude --allow-dangerously-skip-permissions "执行部署脚本"
```

---

## 📚 相关文档

- **Claude Code 官方文档**: https://docs.claude.com/
- **MCP 服务器列表**: https://github.com/anthropics/claude-plugins-official
- **Context7 文档**: https://github.com/upstash/context7-mcp

---

## ✅ 待办

- [ ] 安装 Context7 MCP
- [ ] 配置 GitHub Personal Access Token
- [ ] 安装 ripgrep、fd-find
- [ ] 为 ai-daily-collector 创建 .claude 配置
- [ ] 测试新工具链
