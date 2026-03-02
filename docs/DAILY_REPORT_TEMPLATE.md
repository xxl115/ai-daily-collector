# 昨日文章总结报告模板

## 使用方法

```bash
# 生成昨天的报告（默认）
python scripts/generate_daily_report.py

# 生成指定日期的报告
python scripts/generate_daily_report.py --date 2026-03-01
```

---

## 报告模板

### 基础版本

```markdown
# AI Daily Report - 2026年03月01日

**生成时间**: 2026-03-02 09:00:00
**文章总数**: 15

---

## 大厂/人物 (3 篇)

### 1. OpenAI 发布 GPT-5
**摘要**: OpenAI 今天正式发布了 GPT-5 最新版本，在推理能力、多模态理解和代码生成方面有显著提升。
**标签**: LLM, 多模态, 发布, 研究
**链接**: https://example.com/article1

### 2. Anthropic 发布 Claude 4
**摘要**: Claude 4 在安全性、准确性和多轮对话能力上都有巨大提升。
**标签**: LLM, 安全, 发布, 国际
**链接**: https://example.com/article2

### 3. Google 发布 Gemini 2.0
**摘要**: Google 今天发布了 Gemini 2.0，支持100万token的上下文长度。
**标签**: LLM, 多模态, 发布, 国际
**链接**: https://example.com/article3

---

## Agent工作流 (2 篇)

### 1. MCP 规范发布
**摘要**: MCP 协议标准化工作今天正式启动，多个厂商承诺支持。
**标签**: Agent, MCP, 开源, 发布
**链接**: https://example.com/article4

### 2. LangChain 发布新版本
**摘要**: LangChain v0.2 发布，增强了 Agent 协作能力。
**标签**: Agent, 框架, 发布, 开源
**链接**: https://example.com/article5

---

## 编程助手 (5 篇)

### 1. Cursor IDE 新功能
**摘要**: Cursor 发布重大更新，新增 AI 代码重构功能，支持多种编程语言。
**标签**: 编程, IDE, 发布
**链接**: https://example.com/article6

### 2. GitHub Copilot 更新
**摘要**: GitHub Copilot 支持 Python 项目，提升了代码生成质量。
**标签**: 编程, GitHub, 发布
**链接**: https://example.com/article7

### 3. Windsurf 发布
**摘要**: Windsurf 支持 RAG，可以连接知识库。
**标签**: 编程, RAG, 发布
**链接**: https://example.com/article8

### 4. v0 发布
**摘要**: v0 新增多模态支持，可以分析图片和视频。
**标签**: 编程, 多模态, 发布
**链接**: https://example.com/article9

### 5. Cline 更新
**摘要**: Cline 增强了代码理解能力，支持复杂重构。
**标签**: 编程, 发布
**链接**: https://example.com/article10

---

## 统计信息

| 分类 | 数量 |
|------|------|
| 大厂/人物 | 3 |
| Agent工作流 | 2 |
| 编程助手 | 5 |
| 内容生成 | 1 |
| 工具生态 | 2 |
| 安全风险 | 1 |
| 算力基建 | 1 |

### 标签统计

| 标签 | 出现次数 |
|------|----------|
| LLM | 8 |
| 发布 | 5 |
| 多模态 | 3 |
| 编程 | 5 |
| Agent | 2 |
| 开源 | 2 |
| 国际 | 2 |
| 安全 | 1 |
| 研究 | 1 |

---

## 其他 (1 篇)

### 1. 未分类文章
**链接**: https://example.com/article15
```

---

### 简洁版本

```markdown
# AI日报 - 2026-03-01

## 今日焦点

- [OpenAI 发布 GPT-5](https://example.com/article1) - 在推理、多模态和代码生成方面有显著提升
- [Claude 4 发布](https://example.com/article2) - 安全性和准确性都有巨大提升

## 大厂/人物

1. **[OpenAI 发布 GPT-5](https://example.com/article1)**
   - 在推理、多模态理解和代码生成方面有显著提升
   - 标签: LLM, 多模态, 发布, 研究

2. **[Claude 4 发布](https://example.com/article2)**
   - 安全性和准确性都有巨大提升
   - 标签: LLM, 安全, 发布, 国际

## Agent工作流

1. **[MCP 规范发布](https://example.com/article4)**
   - MCP 协议标准化工作正式启动
   - 标签: Agent, MCP, 开源, 发布

2. **[LangChain v0.2](https://example.com/article5)**
   - 增强了 Agent 协作能力
   - 标签: Agent, 框架, 发布, 开源

## 编程助手

1. **[Cursor AI 代码重构](https://example.com/article6)**
   - 支持多种编程语言
   - 标签: 编程, IDE, 发布

2. **[GitHub Copilot Python](https://example.com/article7)**
   - 提升代码生成质量
   - 标签: 编程, GitHub, 发布

## 其他

- 未分类文章: 1 篇

---

## 统计

| 分类 | 数量 |
|------|------|
| 大厂/人物 | 3 |
| Agent工作流 | 2 |
| 编程助手 | 5 |
| 其他 | 1 |
| **总计** | **11** |

热门标签: LLM (8), 发布 (5), 编程 (5)
```

---

## 自定义模板

你可以修改 `scripts/generate_daily_report.py` 中的以下部分来自定义报告样式：

### 报告标题

```python
# 基础版本
report_lines.append(f"# AI Daily Report - {target_date.strftime('%Y年%m月%d日')}")

# 简洁版本
report_lines.append(f"# AI日报 - {target_date.strftime('%Y-%m-%d')}")
```

### 分类标题

```python
# 详细版本
report_lines.append(f"\n## {category} ({len(articles_in_cat)} 篇)\n")

# 简洁版本
report_lines.append(f"\n## {category}")
```

### 文章格式

```python
# 详细版本（包含所有信息）
report_lines.append(f"### {i}. {title}")
report_lines.append(f"**摘要**: {summary}")
report_lines.append(f"**标签**: {', '.join(tags)}")
report_lines.append(f"**链接**: {url}")

# 简洁版本（只显示关键信息）
report_lines.append(f"1. **[{title}]({url})**")
report_lines.append(f"   - {summary}")
```

---

## 输出文件

报告默认保存到：
```
ai/reports/daily_report_YYYYMMDD.md
```

例如：`ai/reports/daily_report_20260301.md`
