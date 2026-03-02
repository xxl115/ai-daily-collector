# Worker MCP 端点修复计划

## TL;DR

> **快速摘要**: 修复 Cloudflare Worker MCP 端点中缺失的 `upsert_article` 方法，使 `update_article_summary_and_category` 工具能正常工作
> 
> **预计工作量**: 简单
> **并行执行**: 否（顺序任务）

---

## 问题描述

MCP 工具 `update_article_summary_and_category` 调用时报错：
```
'dict' object has no attribute 'summary'
```

**根本原因**: `WorkersD1StorageAdapter` 类缺少 `upsert_article` 方法。

MCP 工具代码尝试调用 `storage.upsert_article(article)`，但该方法不存在。

---

## 修复任务

### 1. 添加 upsert_article 方法

**文件**: `worker.py`

**位置**: 在 `WorkersD1StorageAdapter` 类的 `fetch_article_by_id` 方法之后（约第 793 行）

**代码**:
```python
async def upsert_article(self, article):
    """Insert or update an article (accepts dict)"""
    if not article:
        return {"success": False, "error": "No article data"}

    article_id = article.get("id")
    if not article_id:
        return {"success": False, "error": "No article ID"}

    import json

    sql = """
        UPDATE articles SET
            title = ?, content = ?, url = ?, published_at = ?,
            source = ?, categories = ?, tags = ?, summary = ?, ingested_at = ?
        WHERE id = ?
    """

    params = [
        article.get("title", ""),
        article.get("content", ""),
        article.get("url", ""),
        article.get("published_at"),
        article.get("source", ""),
        json.dumps(article.get("categories", [])),
        json.dumps(article.get("tags", [])),
        article.get("summary", ""),
        article.get("ingested_at", ""),
        article_id,
    ]

    return await self._execute_sql(sql, params)
```

### 2. 部署 Worker

```bash
cd /Users/young/xiaobailong/ai-code/ai-daily-collector
wrangler deploy
```

### 3. 测试 MCP 端点

**测试命令**:
```bash
curl -s --socks5-hostname 127.0.0.1:1080 -X POST "https://ai-daily-collector.xxl185.workers.dev/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "update_article_summary_and_category",
    "arguments": {
      "article_id": "https://www.leiphone.com/category/ai/0MDVe9YV554G4RYM.html",
      "summary": "测试摘要：甲骨文面临严峻的资金压力..."
    }
  }'
```

**预期结果**: 返回 `{"success": true, "message": "Updated article ...", "category": "...", "tags": [...]}`

---

## 验证步骤

1. ✅ Worker 部署成功
2. ✅ MCP 端点返回成功响应
3. ✅ 文章摘要已更新到数据库

---

## 完成后

- 提交代码到 GitHub
- 更新文档（如需要）
