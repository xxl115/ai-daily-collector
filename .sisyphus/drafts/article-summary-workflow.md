# 文章摘要和分类工作流程

## 概述

AI Daily Collector 支持两种部署方式：

1. **本地 FastAPI** - 开发测试用
2. **Cloudflare Worker** - 生产环境（推荐）

本文档说明如何使用 Cloudflare Worker API。

---

## Cloudflare Worker API

Worker 部署后可直接调用，无需启动本地服务器。

### API 基础信息

```
Worker URL: https://ai-daily-collector.xxl185.workers.dev
（根据你的 Cloudflare 配置可能不同）
```

> ⚠️ **网络说明**: 国内访问可能需要代理
> ```bash
> curl --socks5-hostname 127.0.0.1:1080 "https://ai-daily-collector.xxl185.workers.dev/..."
> ```

### MCP 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/mcp` | POST | 执行 MCP 工具 |
| `/mcp/tools` | GET | 获取工具列表 |

### 1. 获取工具列表

```bash
# 查看可用的 MCP 工具
curl "https://ai-daily-collector.xxl185.workers.dev/mcp/tools"
```

**响应示例：**
```json
{
  "tools": [
    {"name": "get_articles_needing_summary", "description": "获取需要总结的文章列表"},
    {"name": "update_article_summary_and_category", "description": "更新摘要并自动分类"},
    {"name": "classify_article", "description": "自动分类文章"},
    {"name": "list_categories", "description": "列出分类规则"}
  ]
}
```

---

### 2. 获取需要处理的文章

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_articles_needing_summary",
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
      "content_preview": "文章内容前300字符..."
    }
  ]
}
```

### 3. 提交摘要并自动分类

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "文章ID",
      "summary": "你撰写的中文摘要",
      "auto_classify": true
    }
  }'
```

**参数说明：**
| 参数 | 类型 | 说明 |
|------|------|------|
| article_id | string | 文章唯一标识（URL） |
| summary | string | 中文摘要（用户手工撰写） |
| auto_classify | boolean | 是否自动分类，默认 true |

**响应示例：**
```json
{
  "success": true,
  "message": "Updated article xxx",
  "category": "大厂/人物",
  "tags": ["LLM", "中国", "融资"]
}
```

---

### 4. 单独分类文章

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "classify_article",
    "arguments": {
      "article_id": "文章ID"
    }
  }'
```

---

### 5. 查看分类规则

```bash
# 查看所有分类
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_categories"}'
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
| 国际 | 美国, 欧洲, 日本, 海外 |
| 创业 | 创业, 创始人, CEO |
| IPO | IPO, 港交所, 上市 |

---

## 手动操作流程

### 使用 Cloudflare Worker API（推荐）

```bash
WORKER_URL="https://ai-daily-collector.xxl185.workers.dev"

# 1. 获取待处理文章
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_articles_needing_summary", "arguments": {"limit": 5}}'

# 2. 手工撰写摘要后提交
curl -X POST "$WORKER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "https://example.com/article",
      "summary": "本文介绍了...",
      "auto_classify": true
    }
  }'
```

### 使用本地 API（开发测试）

```bash
# 启动本地 API
make api

# 然后使用 localhost:8000
curl "http://localhost:8000/mcp/articles/need-summary?limit=5"
```

### Python 脚本示例

```python
import requests

WORKER_URL = "https://ai-daily-collector.xxl185.workers.dev"

# 获取待处理文章
response = requests.post(
    f"{WORKER_URL}/mcp",
    json={"tool": "get_articles_needing_summary", "arguments": {"limit": 5}}
)
articles = response.json()["articles"]

# 处理每篇文章
for article in articles:
    article_id = article["id"]
    content = article.get("content_preview", "")
    
    # 手工撰写摘要
    summary = input(f"请为 '{article['title']}' 撰写摘要: ")
    
    # 提交
    result = requests.post(
        f"{WORKER_URL}/mcp",
        json={
            "tool": "update_article_summary_and_category",
            "arguments": {
                "article_id": article_id,
                "summary": summary,
                "auto_classify": True
            }
        }
    )
    print(result.json())
```

---

## 数据库修复（编码问题）

### 问题描述

早期版本存在双重编码问题，中文被存储为 Unicode 转义序列：
- **错误**: `\u949b\u5a92\u4f53\u5206\u6790`
- **正确**: `钛媒体分析`

### 解决方案

代码中已添加 `_decode_double_encoded()` 方法自动处理：

```python
# ingestor/storage/d1_adapter.py

def _decode_double_encoded(self, text: str) -> str:
    """Decode double-encoded Unicode strings."""
    if not text or '\\u' not in text:
        return text
    try:
        return text.encode('utf-8').decode('unicode_escape')
    except Exception:
        return text
```

### 手动修复现有数据

```bash
# 查看有问题的数据
npx wrangler d1 execute ai-daily-collector \
  --command "SELECT id, summary FROM articles WHERE summary LIKE '%\\u%'" \
  --remote
```

---

## 快速参考

### Cloudflare Worker（生产）

| 操作 | 命令 |
|------|------|
| 工具列表 | `curl https://your-worker.workers.dev/mcp/tools` |
| 获取待处理 | `curl -X POST https://your-worker.workers.dev/mcp -d '{"tool":"get_articles_needing_summary"}'` |
| 提交摘要 | `curl -X POST https://your-worker.workers.dev/mcp -d '{"tool":"update_article_summary_and_category",...}'` |
| 部署 Worker | `npx wrangler deploy` |

### 本地开发

| 操作 | 命令 |
|------|------|
| 启动 API | `make api` |
| 获取待处理 | `curl localhost:8000/mcp/articles/need-summary` |
| 提交摘要 | `curl -X POST localhost:8000/mcp/call -d '{"tool":"update_article_summary_and_category",...}''` |

---

## 部署 Cloudflare Worker

### 1. 配置环境变量

```bash
# 设置 Cloudflare API Token
wrangler secret put CF_API_TOKEN
# 输入你的 Cloudflare API Token

# 设置 D1 数据库 ID
wrangler secret put CF_D1_DATABASE_ID
# 输入 D1 数据库 ID: 62f5766f-e837-402c-9237-390d4dbbdb52
```

### 2. 部署 Worker

```bash
npx wrangler deploy
```

### 3. 测试部署

```bash
# 健康检查
curl "https://your-worker.workers.dev/health"

# 获取工具列表
curl "https://your-worker.workers.dev/mcp/tools"
```

---

## 文件位置

| 文件 | 说明 |
|------|------|
| `worker.py` | Cloudflare Worker 主文件（含 MCP 逻辑） |
| `api/mcp.py` | 本地 FastAPI MCP 接口 |
| `scripts/classifiers/rule_classifier.py` | 规则分类器 |
| `ingestor/storage/d1_adapter.py` | D1 数据库适配器 |
| `wrangler.toml` | Cloudflare Worker 配置 |
