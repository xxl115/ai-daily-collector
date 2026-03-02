# MCP Worker API 文档

## 概述

AI Daily Collector 支持两种 MCP 部署方式：

1. **本地 FastAPI** - 开发测试用 (`api/mcp.py`)
2. **Cloudflare Worker** - 生产环境推荐 (`worker.py`)

本文档说明 Cloudflare Worker MCP API 的使用方法。

---

## 快速开始

### 手动摘要文章流程

```bash
WORKER_URL="https://ai-daily-collector.xxl185.workers.dev"

# 1. 获取需要处理的文章
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_articles_needing_processing", "arguments": {"limit": 5}}'

# 2. 提交摘要并自动分类
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "雷峰网-07f58b44",
      "summary": "三星发布Galaxy S26系列，强化与Gemini系统整合，提升AI体验。",
      "auto_classify": true,
      "tags": ["三星", "谷歌", "Gemini"]
    }
  }'
```

---

## MCP 工具列表

| 工具 | 说明 |
|------|------|
| **文章获取** | |
| `get_articles_needing_processing` | 获取需要处理的文章（详细状态） |
| **文章更新** | |
| `update_article_summary_and_category` | 更新摘要并分类（核心工具） |
| `classify_article` | 单独对文章进行自动分类 |
| **分类查看** | |
| `list_categories` | 列出所有分类规则（硬编码） |
| `get_categories` | 获取数据库中的分类 |
| **分类管理** | |
| `create_category` | 创建新分类 |
| `update_category` | 更新分类 |
| `delete_category` | 删除分类 |
| **标签管理** | |
| `get_tags` | 获取数据库中的标签 |
| `create_tag` | 创建新标签 |
| `update_tag` | 更新标签 |
| `delete_tag` | 删除标签 |
| **初始化** | |
| `init_default_categories` | 初始化默认分类和标签数据 |

---

## 1. 获取需要处理的文章

### `get_articles_needing_processing`

获取需要处理的文章列表，返回详细的状态信息。

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_articles_needing_processing",
    "arguments": {"limit": 10}
  }'
```

**响应示例：**
```json
{
  "success": true,
  "count": 2,
  "articles": [
    {
      "id": "雷峰网-5f07e827",
      "title": "百度四季度AI业务收入占43% 超预期",
      "url": "https://www.leiphone.com/...",
      "source": "雷峰网",
      "needs_summary": false,
      "needs_category": true,
      "needs_tags": true,
      "content_preview": "文章内容前300字符...",
      "content_length": 7246,
      "ingested_at": "2026-03-02T12:55:54.578591"
    }
  ]
}
```

**字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `needs_summary` | boolean | 是否需要总结 |
| `needs_category` | boolean | 是否需要分类 |
| `needs_tags` | boolean | 是否需要标签 |
| `content_preview` | string | 文章内容前 300 字符预览 |
| `content_length` | number | 文章内容总长度 |

---

## 2. 更新文章摘要并分类

### `update_article_summary_and_category`

核心更新工具，支持多种使用方式。

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `article_id` | string | ✅ | 文章唯一标识 |
| `summary` | string | ✅ | 中文摘要 |
| `category` | string | ❌ | 手动指定分类（如"大厂/人物"） |
| `tags` | array | ❌ | 手动指定标签（如["LLM", "中国"]） |
| `auto_classify` | boolean | ❌ | 是否自动分类，默认 true |

### 使用方式

#### 方式一：自动分类（推荐）

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "雷峰网-5f07e827",
      "summary": "百度发布Q4财报，AI业务收入占比43%，超市场预期。",
      "auto_classify": true
    }
  }'
```

**返回：**
```json
{
  "success": true,
  "message": "Updated article 雷峰网-5f07e827",
  "category": "商业应用",
  "tags": ["财报", "百度"]
}
```

#### 方式二：手动指定分类和标签

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "雷峰网-5f07e827",
      "summary": "OpenAI 发布 GPT-5，支持100万token上下文。",
      "category": "大厂/人物",
      "tags": ["LLM", "发布", "国际"],
      "auto_classify": false
    }
  }'
```

#### 方式三：自动分类 + 部分手动标签

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "雷峰网-5f07e827",
      "summary": "百度发布Q4财报，AI业务收入占比43%。",
      "auto_classify": true,
      "tags": ["百度", "中国"]
    }
  }'
```

### 优先级规则

1. **分类**：`category` 参数 > 自动分类
2. **标签**：`tags` 参数 > 自动分类标签

---

## 3. 单独分类文章

### `classify_article`

对已有文章进行自动分类。

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "classify_article",
    "arguments": {
      "article_id": "雷峰网-5f07e827"
    }
  }'
```

---

## 4. 分类和标签管理

### 获取所有分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_categories"}'
```

### 创建分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_category",
    "arguments": {
      "name": "新分类名称",
      "keywords": ["关键词1", "关键词2", "关键词3"]
    }
  }'
```

### 更新分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_category",
    "arguments": {
      "id": 1,
      "name": "更新后的分类名",
      "keywords": ["新关键词1", "新关键词2"]
    }
  }'
```

### 删除分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "delete_category",
    "arguments": {"id": 1}
  }'
```

### 标签管理

标签管理与分类类似，工具名为：
- `get_tags` - 获取所有标签
- `create_tag` - 创建标签
- `update_tag` - 更新标签
- `delete_tag` - 删除标签

### 初始化默认数据

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "init_default_categories"}'
```

---

## 分类规则

### 8 大分类（硬编码）

| 分类 | 关键词示例 |
|------|-----------|
| 大厂/人物 | OpenAI, Anthropic, Google, Meta, 微软, 英伟达, 马斯克, GPT, Claude, Llama, Qwen, 通义, Kimi |
| Agent工作流 | Agent, MCP, A2A, Autogen, CrewAI, LangChain, LangGraph, RAG |
| 编程助手 | Cursor, Windsurf, Cline, GitHub Copilot, Devin, v0, IDE |
| 内容生成 | Midjourney, DALL-E, Stable Diffusion, Sora, 视频生成, Suno, 多模态 |
| 工具生态 | LangChain, LlamaIndex, Hugging Face, PyTorch, Ollama, vLLM |
| 安全风险 | 安全, 漏洞, 攻击, 隐私, Deepfake, 幻觉, Prompt注入 |
| 算力基建 | GPU, 芯片, 算力, 训练, 推理, A100, H100 |
| 商业应用 | 电商, 金融, 医疗, 教育, 融资, IPO, 手机, 财报 |

### 12 标签（硬编码）

| 标签 | 关键词示例 |
|------|-----------|
| LLM | 大模型, 语言模型, GPT, Claude |
| 编程 | 编程, 代码, 开发, GitHub |
| 多模态 | 视觉, 图像, 视频, 音频 |
| 开源 | 开源, Open Source, Apache, MIT |
| 发布 | 发布, 上线, 更新, 新功能 |
| 研究 | 论文, arXiv, 学术 |
| 融资 | 融资, 投资, 估值, IPO |
| 财报 | 财报, 营收, 利润, 业绩 |
| 中国 | 中国, 国产, 北京, 上海 |
| 国际 | 美国, 欧洲, 日本, 海外 |
| 创业 | 创业, 创始人, CEO |

### 数据库规则

Worker 支持从数据库读取动态分类和标签规则，优先级：
1. 数据库规则（`get_categories` / `get_tags`）
2. 硬编码规则（回退）

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/mcp/tools` | GET | 获取工具列表 |
| `/mcp` | POST | 调用 MCP 工具 |
| `/` | GET | 健康检查 |
| `/api/v2/articles` | GET | 获取文章列表 |
| `/api/v2/stats` | GET | 获取统计信息 |

---

## 文件位置

| 文件 | 说明 |
|------|------|
| `worker.py` | Cloudflare Worker MCP 实现 |
| `api/mcp.py` | 本地 FastAPI MCP 实现 |
| `wrangler.toml` | Worker 部署配置 |
| `.github/workflows/cloudflare-deploy.yml` | 自动部署配置 |

---

## 部署

```bash
# 本地测试
make api

# 部署到 Cloudflare
git push origin master
# GitHub Actions 自动部署
```

---

*最后更新：2026-03-02*
