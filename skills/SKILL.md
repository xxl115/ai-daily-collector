# AI Daily Report Generator

根据已有数据生成 AI 日报，自动筛选 AI 相关文章并进行分类、打标。

## 功能

- 获取指定日期的文章
- 根据标题筛选 AI 相关文章
- 自动分类和标签提取
- 生成 Markdown 日报

## MCP 工具

### get_articles_by_date

获取指定日期的文章

**参数：**
- `date` (必填): 日期，格式 `YYYY-MM-DD`
- `limit` (可选): 返回文章数量，默认 20

**返回：**
```json
{
  "success": true,
  "date": "2026-03-11",
  "count": 100,
  "articles": [
    {
      "id": "...",
      "title": "...",
      "url": "...",
      "source": "...",
      "content": "...",
      "raw_markdown": "...",
      "summary": "...",
      "categories": [],
      "tags": [],
      "ingested_at": "..."
    }
  ]
}
```

## 使用方式

### 方式 1: 使用脚本（推荐）

```bash
cd ~/.openclaw/skills/ai-daily-report
python3 generate_report.py
```

### 方式 2: 指定日期

```bash
python3 generate_report.py 2026-03-10
```

### 方式 3: 直接调用 MCP（仅获取，不处理）

```bash
curl -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_articles_by_date",
    "arguments": {
      "date": "2026-03-11",
      "limit": 100
    }
  }'
```

## AI 关键词库

AI, 人工智能, LLM, GPT, 大模型, 模型, 机器学习, 深度学习,
神经网络, OpenAI, Claude, Gemini, 文心, 通义, 智谱,
芯片, GPU, 算力, 自动驾驶, 机器人, 智能驾驶, 智能汽车,
论文, arXiv, 研究, 算法, 训练, 推理, RAG, Embedding,
Agent, 多模态, Sora, 视频生成, 图像生成, AIGC, AGI,
千问, 通义, 文心, 智谱, MiniMax, 阶跃, 月之暗面,
Sora, Runway, Pika, Midjourney, DALL-E,
自动驾驶, 智能驾驶, FSD, NOA,
大模型, 参数, 训练, 推理, 微调, RAG, 向量数据库

## 预设分类

| 分类 | 关键词示例 |
|------|-----------|
| 大厂 | 阿里, 腾讯, 百度, 字节, 华为, 小米, OpenAI, Google |
| 人物 | 教授, CEO, 创始人, CTO, 副总裁, 总监 |
| 产品 | 发布, 推出, 新品, 开售, 上市 |
| 技术 | 论文, 研究, 实验, 数据, 算法 |
| 商业 | 融资, 投资, 上市, 股价, 财报, 营收, 利润 |
| 学术 | 大学, 研究院, 实验室, arXiv |
| 其他 | 其他 |

## 配置

| 配置项 | 默认值 | 说明 |
|--------|---------|------|
| WORKER_URL | https://ai-daily-collector.xxl185.workers.dev | Cloudflare Worker 地址 |
| DATE | today | 要生成日报的日期 |
| LIMIT | 100 | 获取文章数量 |
| MAX_SUMMARY_LENGTH | 50 | 摘要最大长度 |
| MAX_TAGS | 3 | 每篇文章最大标签数 |

## 输出

### 文件

- 日报: `docs/reports/daily_report_YYYYMMDD.md`
- 处理后的文章: `docs/reports/processed_articles_YYYYMMDD.json`

### 数据库更新

自动更新数据库中的以下字段：
- `summary`: 摘要（使用标题）
- `categories`: 分类（单分类）
- `tags`: 标签（最多 3 个）

### MCP 工具

更新数据库使用 `update_article_summary_and_category` 工具

**参数：**
- `article_id` (必填): 文章 ID
- `summary` (必填): 中文摘要
- `category` (必填): 分类
- `tags` (必填): 标签数组
- `auto_classify` (可选): 是否自动分类，默认 true，脚本设为 false
