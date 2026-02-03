# 🤖 AI Daily Collector

> 自动化采集、总结和分发 AI 热点资讯的完整工作流

[![GitHub stars](https://img.shields.io/github/stars/xxl115/ai-daily-collector)](https://img.shields.io/github/stars/xxl115/ai-daily-collector)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/xxl115/ai-daily-collector/ci.yml?branch=master)](https://github.com/xxl115/ai-daily-collector/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/xxl115/ai-daily-collector/ci.yml?branch=master&label=tests)](https://github.com/xxl115/ai-daily-collector/actions)

**English** | [中文](README_CN.md)

## ✨ 特性

- 📡 **多源采集**: 支持 RSS、API 多种来源（MIT Tech Review、Hacker News、GitHub、36氪、机器之心等）
- 📝 **智能总结**: 使用智谱 AI 生成中文摘要
- 📰 **日报生成**: 自动按分类整理成结构化日报
- 🌐 **多平台同步**: 自动推送到 GitHub 和 Notion
- ⏰ **定时任务**: 每天自动执行，无需人工干预
- 🔌 **REST API**: 提供 FastAPI 接口，支持程序化访问
- 🐳 **Docker 支持**: 一键部署，开箱即用

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
# 克隆并启动
git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 启动容器
docker-compose up -d
```

### 方式二：本地安装

```bash
# 克隆项目
git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 安装依赖
make install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 运行完整工作流
make run
```

### 方式三：仅使用 API

```bash
# 启动 API 服务
make api

# 访问 http://localhost:8000/docs 查看 API 文档
```

## 📁 项目结构

```
ai-daily-collector/
├── api/                    # FastAPI 接口
│   └── main.py            # API 主程序
├── scripts/               # 核心脚本
│   ├── ai-hotspot-crawler-simple.py  # RSS 采集
│   ├── summarize-articles.py         # AI 总结生成
│   ├── generate-daily-report.py      # 日报生成
│   ├── push-to-notion.py             # Notion 同步
│   └── daily-ai-workflow.py          # 完整工作流
├── ai/                     # 数据目录
│   ├── articles/
│   │   ├── original/       # 原始文章
│   │   └── summary/        # 中文总结
│   └── daily/              # 每日日报
├── config/                 # 配置文件
│   └── sources.yaml        # RSS 源配置
├── tests/                  # 测试用例
├── .github/workflows/      # CI/CD 配置
├── Dockerfile              # Docker 镜像
├── docker-compose.yml      # Docker Compose
├── Makefile                # 命令行工具
├── requirements.txt        # Python 依赖
└── README.md               # 本文档
```

## 📖 使用指南

### 单独运行脚本

```bash
# 1. 采集今日 AI 热点
make crawl

# 2. 生成中文总结
make summarize

# 3. 生成日报
make report

# 4. 推送到 Notion（可选）
python scripts/push-to-notion.py
```

### 使用 Make 命令

```bash
make help              # 查看所有命令
make install           # 安装依赖
make test              # 运行测试
make lint              # 代码检查
make format            # 代码格式化
make docker-build      # 构建镜像
make deploy            # 部署到生产
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/v1/report/today` | GET | 获取今日日报 |
| `/api/v1/articles` | GET | 获取文章列表 |
| `/api/v1/categories` | GET | 获取分类列表 |
| `/api/v1/stats` | GET | 获取统计信息 |
| `/docs` | GET | Swagger API 文档 |

## 📊 分类体系

日报按以下分类整理：

| 编号 | 分类 | 说明 |
|------|------|------|
| 1️⃣ | 今日焦点 | 最重要的单篇报道 |
| 2️⃣ | 大厂/人物 | Anthropic、OpenAI、Google 等动向 |
| 3️⃣ | Agent 工作流 | MCP、A2A、Autogen 等框架 |
| 4️⃣ | 编程助手 | Cursor、Windsurf、Cline 等工具 |
| 5️⃣ | 内容生成 | 多模态、写作、视频工具 |
| 6️⃣ | 工具生态 | OpenClaw、LangChain 等生态 |
| 8️⃣ | 安全风险 | 漏洞、恶意软件、深度伪造 |
| 7️⃣ | 灵感库 | 待深挖的方向（按需展开） |

## 🛠️ 自定义

### 添加新的 RSS 源

编辑 `config/sources.yaml`：

```yaml
sources:
  - name: "新源名称"
    url: "https://example.com/rss"
    enabled: true
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 10
```

### 修改分类规则

编辑 `scripts/generate_daily_report.py` 中的 `CATEGORIES` 配置。

### 禁用 Notion 同步

在 `.env` 中注释掉 `NOTION_API_KEY` 即可跳过 Notion 同步。

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行测试并检查覆盖率
make test-cov

# 代码风格检查
make lint

# 自动格式化
make format
```

## 🐳 Docker 部署

```bash
# 构建镜像
make docker-build

# 前台运行
make docker-run

# 使用 docker-compose（推荐）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## ⏰ 定时任务

### Linux/Mac (cron)

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天晚上 8 点）
0 20 * * * cd /path/to/ai-daily-collector && make run >> /var/log/ai-collector.log 2>&1
```

### GitHub Actions（自动）

项目已配置 GitHub Actions CI/CD，每次 push 会自动运行测试。

## 📦 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本变更。

## 🤝 贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

## 📝 许可证

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [智谱 AI](https://www.zhipuai.cn/) - 提供中文总结能力
- [Notion](https://www.notion.so/) - 日报同步平台
- [FastAPI](https://fastapi.tiangolo.com/) - API 框架
- [RSSHub](https://github.com/DIYgod/RSSHub) - RSS 聚合灵感

---

*如果这个项目对你有帮助，请 ⭐ Star 支持一下！*
