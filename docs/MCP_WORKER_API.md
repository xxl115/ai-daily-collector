# 文章摘要和分类工作流程

## 概述

AI Daily Collector 支持两种部署方式：

1. **本地 FastAPI** - 开发测试用
2. **Cloudflare Worker** - 生产环境（推荐）

本文档说明如何使用 Cloudflare Worker API。

---

## 快速开始

### 手动摘要文章流程

```bash
WORKER_URL="https://ai-daily-collector.xxl185.workers.dev"

# 1. 获取需要处理的文章（需要总结、分类或标签）
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_articles_needing_processing", "arguments": {"limit": 5}}'

# 2. 手动撰写摘要后提交更新（可手动指定标签）
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary",
    "arguments": {
      "article_id": "雷峰网-07f58b44",
      "summary": "三星发布Galaxy S26系列，强化与Gemini系统整合...",
      "auto_classify": true,
      "tags": ["三星", "谷歌", "Gemini"]
    }
  }'
```

---

## MCP 工具

### 工具列表

| 工具 | 说明 |
|------|------|
| `get_articles_needing_processing` | 获取需要处理的文章列表（需要总结、分类或标签） |
| `update_article_summary` | 更新文章摘要（支持自动分类和手动指定标签） |
| `classify_article` | 自动分类文章 |
| `list_categories` | 列出分类规则 |

### 1. 获取需要处理的文章

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
  "count": 3,
  "articles": [
    {
      "id": "https://36kr.com/newsflashes/xxx",
      "title": "文章标题",
      "url": "https://...",
      "source": "36kr",
      "needs_summary": true,
      "needs_category": false,
      "needs_tags": false,
      "content_preview": "文章内容前300字符...",
      "content_length": 450
    }
  ]
}
```

**字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `needs_summary` | boolean | 是否需要总结（summary 为空） |
| `needs_category` | boolean | 是否需要分类（categories 为空） |
| `needs_tags` | boolean | 是否需要标签（tags 为空） |
| `content_preview` | string | 文章内容前 300 字符预览 |
| `content_length` | number | 文章内容总长度 |

---

### 2. 提交摘要（支持自动分类和手动指定标签）

#### 方式一：自动分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary",
    "arguments": {
      "article_id": "https://36kr.com/newsflashes/xxx",
      "summary": "本文介绍了 OpenAI GPT-5 的最新特性，包括多模态理解能力和100万token的上下文长度。",
      "auto_classify": true
    }
  }'
```

#### 方式二：手动指定标签

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary",
    "arguments": {
      "article_id": "https://36kr.com/newsflashes/xxx",
      "summary": "本文介绍了 OpenAI GPT-5 的最新特性...",
      "auto_classify": false,
      "tags": ["LLM", "多模态", "发布", "研究"]
    }
  }'
```

#### 方式三：自动分类 + 手动指定标签（标签覆盖自动分类）

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary",
    "arguments": {
      "article_id": "https://36kr.com/newsflashes/xxx",
      "summary": "本文介绍了 OpenAI GPT-5 的最新特性...",
      "auto_classify": true,
      "tags": ["LLM", "发布", "国际"]
    }
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `article_id` | string | ✅ | 文章唯一标识（URL） |
| `summary` | string | ✅ | 中文摘要（用户手工撰写） |
| `auto_classify` | boolean | ❌ | 是否自动分类，默认 true |
| `tags` | array | ❌ | 手动指定标签数组 |

**标签优先级：**
1. 如果提供 `tags` 参数，使用手动指定的标签
2. 如果未提供 `tags` 且 `auto_classify=true`，使用自动分类的标签
3. 如果 `auto_classify=false`，不修改分类和标签

---

### 3. 按日期总结文章

```bash
# 总结昨天的文章
python scripts/summarize_by_date.py

# 总结指定日期的文章
python scripts/summarize_by_date.py --date 2026-03-01

# 总结日期范围的文章
python scripts/summarize_by_date.py --date-start 2026-03-01 --date-end 2026-03-07

# 预览模式
python scripts/summarize_by_date.py --date 2026-03-01 --dry-run

# 输出结果到 JSON
python scripts/summarize_by_date.py --date 2026-03-01 --output reports/summary.json
```

---

## 分类规则

### 8 大分类

| 分类 | 关键词 |
|------|--------|
| 大厂/人物 | OpenAI, Anthropic, Google, Meta, 微软, 英伟达, 马斯克, GPT, Claude, Llama, Qwen, 通义, Kimi, MiniMax 等 |
| Agent工作流 | Agent, 智能体, MCP, A2A, Autogen, CrewAI, LangChain, LangGraph, RAG, 工作流 |
| 编程助手 | Cursor, Windsurf, Cline, GitHub Copilot, Devin, v0, IDE, VS Code |
| 内容生成 | Midjourney, DALL-E, Stable Diffusion, Sora, 视频生成, 语音合成, Suno, 多模态 |
| 工具生态 | LangChain, LlamaIndex, Hugging Face, PyTorch, Ollama, LM Studio, vLLM |
| 安全风险 | 安全, 漏洞, 攻击, 隐私, Deepfake, 幻觉, Prompt注入, 黑客 |
| 算力基建 | GPU, TPU, 芯片, 算力, 训练, 推理, 部署, A100, H100, 自动驾驶 |
| 商业应用 | 电商, 金融, 医疗, 教育, 营销, 创业, 融资, IPO, 手机, 财报 |

### 12 标签

| 标签 | 关键词 |
|------|--------|
| LLM | 大模型, 语言模型, GPT, Claude, AI |
| 编程 | 编程, 代码, 开发, GitHub |
| 多模态 | 视觉, 图像, 视频, 音频 |
| 开源 | 开源, Open Source, Apache, MIT |
| 发布 | 发布, 上线, 更新, 新功能 |
| 研究 | 论文, arXiv, 研究, 学术 |
| 融资 | 融资, 投资, 估值, IPO |
| 财报 | 财报, 营收, 利润, 业绩 |
| 中国 | 中国, 国产, 北京, 上海, 深圳 |
| 国际 | 美国, 欧洲, 日本, 海外, 全球 |
| 创业 | 创业, 创始人, CEO |
| IPO | IPO, 港交所, 上市 |

---

## 文件位置

| 文件 | 说明 |
|------|------|
| `api/mcp.py` | 本地 FastAPI MCP 接口 |
| `scripts/summarize_by_date.py` | 按日期批量总结脚本 |
