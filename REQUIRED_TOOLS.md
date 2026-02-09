# Claude Code 开发环境 - 完整工具清单

> 创建日期: 2026-02-09

---

## 🎯 必装工具（优先级排序）

### 🔥 第一优先级（开发效率核心）

| 工具 | 安装命令 | 用途 |
|------|----------|------|
| **ripgrep (rg)** | `sudo apt install -y ripgrep` | 快速代码搜索，比 grep 快 10 倍 |
| **fd** | `sudo apt install -y fd-find` | 快速文件查找，比 find 快 |
| **jq** | `sudo apt install -y jq` | JSON 命令行处理 |
| **httpie** | `sudo apt install -y httpie` | HTTP 调试，比 curl 更友好 |
| **delta** | `pip install git-delta` | Git diff 高亮显示 |

### 🔥 第二优先级（AI/代码分析）

| 工具 | 安装命令 | 用途 |
|------|----------|------|
| **Context7** | `npm install -g @upstash/context7-mcp` | 代码库上下文分析 |
| **GitHub CLI** | `sudo apt install -y gh` | 直接在终端操作 GitHub |
| **Greptile** | `cargo install greptile` | AI 驱动的代码搜索 |

### 🔥 第三优先级（Python 开发）

| 工具 | 安装命令 | 用途 |
|------|----------|------|
| **black** | `pip install black` | Python 代码格式化 |
| **flake8** | `pip install flake8` | Python 代码检查 |
| **mypy** | `pip install mypy` | Python 类型检查 |
| **pytest** | `pip install pytest` | 测试框架 |
| **ipython** | `pip install ipython` | 交互式 Python shell |

---

## 📦 一键安装脚本

```bash
#!/bin/bash

echo "🔧 安装 Claude Code 必备工具..."

# 1. 系统工具
echo "📦 安装系统工具..."
sudo apt update
sudo apt install -y ripgrep fd-find httpie jq gh

# 2. Python 工具
echo "📦 安装 Python 开发工具..."
pip install black flake8 mypy pytest pytest-cov ipython git-delta

# 3. AI 工具
echo "📦 安装 AI 工具..."
npm install -g @upstash/context7-mcp

# 4. Cargo（如果需要 rust 工具）
if ! command -v cargo &> /dev/null; then
    echo "📦 安装 Rust/Cargo..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
fi

# 安装 greptile
cargo install greptile

echo "✅ 安装完成！"
```

---

## 🐍 Python 项目依赖

### ai-daily-collector 必装

```bash
cd /home/young/code/ai-daily-collector

# 核心依赖
pip install requests feedparser beautifulsoup4 python-dateutil pytz PyYAML

# API 服务
pip install fastapi uvicorn pydantic

# 缓存和工具
pip install redis colorlog cryptography

# 测试
pip install pytest pytest-cov pytest-asyncio

# 代码质量
pip install black flake8 mypy
```

### 其他常用 Python 库

```bash
# 数据处理
pip install pandas numpy

# HTTP 客户端
pip install httpx aiohttp

# 异步支持
pip install asyncio aiofiles

# YAML 处理
pip install pyyaml rich
```

---

## 🔧 Git 配置

```bash
# 安装 delta（更好的 git diff）
pip install git-delta

# 配置 git 使用 delta
git config --global core.pager "delta"
git config --global delta.navigate true

# 配色
git config --global delta.line-numbers true
git config --global delta.hunk-header-decoration-style "blue"
```

---

## 📝 快速对比

### 原始工具 vs 升级工具

| 原始 | 升级后 | 提升 |
|------|--------|------|
| `grep` | `rg` | 速度快 10 倍 |
| `find` | `fd` | 语法更简单，速度快 |
| `curl` | `httpie` | 语法更友好 |
| `cat` | `bat` | 高亮显示，支持语法 |
| `git diff` | `git-delta` | 更好看的 diff |

---

## ✅ 最小必装清单（5 分钟内）

只安装最核心的：

```bash
# 必装
sudo apt install -y ripgrep fd-find httpie jq

# 可选（推荐）
pip install black pytest
```

---

## 🔗 相关文档

- [CLAUDE_CODE_SETUP.md](./CLAUDE_CODE_SETUP.md) - 详细配置指南
- [install-dev-tools.sh](./install-dev-tools.sh) - 安装脚本

---

## 📋 安装检查清单

运行此命令检查安装状态：

```bash
echo "=== 工具检查 ==="
echo "rg:      $(which rg || echo '❌ 未安装')"
echo "fd:      $(which fd || echo '❌ 未安装')"
echo "http:    $(which http || echo '❌ 未安装')"
echo "jq:      $(which jq || echo '❌ 未安装')"
echo "gh:      $(which gh || echo '❌ 未安装')"
echo "black:   $(which black || echo '❌ 未安装')"
echo "pytest:  $(which pytest || echo '❌ 未安装')"
echo ""
echo "=== Python 版本 ==="
python3 --version
echo ""
echo "=== Node.js 版本 ==="
node --version
```
