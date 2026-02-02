# 🤖 AI Daily Collector

> 自动化采集、总结和分发 AI 热点资讯的完整工作流

[![GitHub stars](https://img.shields.io/github/stars/xxl115/ai-daily-collector)](https://github.com/xxl115/ai-daily-collector/stargazers)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## ✨ 特性

- 📡 **多源采集**: 支持 RSS、API 多种来源（MIT Tech Review、Hacker News、GitHub、36氪、机器之心等）
- 📝 **智能总结**: 使用智谱 AI 生成中文摘要
- 📰 **日报生成**: 自动按分类整理成结构化日报
- 🌐 **多平台同步**: 自动推送到 GitHub 和 Notion
- ⏰ **定时任务**: 每天自动执行，无需人工干预

## 🚀 快速开始

### 前置要求

- Python 3.10+
- 智谱 AI API Key (`ZAI_API_KEY`)
- Notion Integration Token（可选，用于同步到 Notion）
- Git（用于版本管理）

### 安装

```bash
# 克隆项目
git clone https://github.com/xxl115/ai-daily-collector.git
cd ai-daily-collector

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

### 配置

编辑 `.env` 文件：

```bash
# 智谱 AI API（必须）
export ZAI_API_KEY="your_zhipu_api_key"

# Notion（可选）
export NOTION_API_KEY="your_notion_token"
```

### 使用

```bash
# 运行完整工作流
python scripts/daily-ai-workflow.py

# 或分步骤执行
python scripts/ai-hotspot-crawler-simple.py    # 1. 采集文章
python scripts/summarize-articles.py            # 2. 生成总结
python scripts/generate-daily-report.py         # 3. 生成日报
python scripts/push-to-notion.py                # 4. 同步 Notion
```

## 📁 项目结构

```
ai-daily-collector/
├── ai/
│   ├── articles/
│   │   ├── original/          # 原始文章（按日期归档）
│   │   └── summary/           # 中文总结（按日期归档）
│   ├── daily/                 # 每日日报
│   └── tools/                 # 工具脚本
├── scripts/                   # 核心脚本
│   ├── ai-hotspot-crawler-simple.py  # RSS 采集
│   ├── summarize-articles.py         # AI 总结生成
│   ├── generate-daily-report.py      # 日报生成
│   ├── push-to-notion.py             # Notion 同步
│   └── daily-ai-workflow.py          # 完整工作流
├── config/
│   └── sources.yaml          # RSS 源配置
├── tests/                    # 测试用例
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖
├── LICENSE                   # 开源协议
└── README.md                 # 本文档
```

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

## ⏰ 定时任务

项目内置定时任务配置（`.github/workflows/` 或系统 cron）：

```bash
# 每天晚上 8 点自动执行
0 20 * * * cd /path/to/ai-daily-collector && python scripts/daily-ai-workflow.py
```

## 🛠️ 自定义

### 添加新的 RSS 源

编辑 `config/sources.yaml`：

```yaml
sources:
  - name: "新源名称"
    url: "https://example.com/rss"
    enabled: true
    filters:
      - keyword: "AI"      # 关键词过滤
      - hours: 24          # 只抓取最近24小时
```

### 修改分类规则

编辑 `scripts/generate-daily-report.py` 中的 `CATEGORIES` 配置。

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📝 许可证

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [智谱 AI](https://www.zhipuai.cn/) - 提供中文总结能力
- [Notion](https://www.notion.so/) - 日报同步平台
- 所有 RSS 源提供者
