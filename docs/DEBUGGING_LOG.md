# AI Daily Collector API 问题排查与解决记录

## 问题描述

部署到 Cloudflare Workers 后，API `/api/v2/articles?page_size=5` 返回空数据：
```json
{"total": 0, "articles": []}
```

尽管 D1 数据库中已有数据，但 API 无法正常读取。

---

## 环境信息

- **平台**: Cloudflare Workers (Python)
- **数据库**: Cloudflare D1
- **部署方式**: GitHub Actions
- **Worker URL**: https://ai-daily-collector.xxl185.workers.dev

---

## 解决过程

### 1. 初步诊断 - 数据库连接问题

#### 现象
```json
{
  "database": {
    "connected": false,
    "error": "'NoneType' object has no attribute 'DB'"
  }
}
```

#### 原因分析
Python Workers 中访问 D1 绑定的正确方式是通过 `self.env.DB`，而不是方法参数 `env`。

#### 错误代码
```python
async def on_fetch(self, request, env, ctx):
    db = env.DB  # ❌ 错误！参数 env 不是绑定对象
```

#### 修复方案
```python
async def on_fetch(self, request, env, ctx):
    db = self.env.DB  # ✅ 正确！通过 self.env 访问绑定
```

#### 参考文档
- [Query D1 from Python Workers](https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/)

---

### 2. 异步操作问题 - "await wasn't used with future"

#### 现象
```json
{
  "schema_error": "Failed to create table: [{'message': \"await wasn't used with future\"}]"
}
```

#### 原因分析
D1 API 的所有操作都是异步的，必须使用 `await`。同步调用会导致运行时错误。

#### 错误代码
```python
def _execute_sql(self, sql, params=None):
    stmt = self.db.prepare(sql)
    result = stmt.all()  # ❌ 错误！缺少 await
```

#### 修复方案
```python
async def _execute_sql(self, sql, params=None):
    stmt = self.db.prepare(sql)
    result = await stmt.all()  # ✅ 正确！使用 await
```

#### 影响范围
1. `_execute_sql` 改为 `async def`
2. `fetch_articles` 改为 `async def`
3. `get_stats` 改为 `async def`
4. `fetch_article_by_id` 改为 `async def`
5. `_list_tables` 改为 `async def`
6. 所有调用处添加 `await`

#### 额外优化
移除了不必要的表创建逻辑（`CREATE TABLE`），因为表已经通过数据采集任务创建好了。

---

### 3. GitHub Actions 部署失败 - 凭据错误

#### 现象
```
Error: Bad credentials - https://docs.github.com/rest
```

#### 原因分析
`setup-uv` action 的 `enable-cache: true` 需要 GitHub token，但配置有问题导致凭据验证失败。

#### 错误配置
```yaml
- uses: astral-sh/setup-uv@v4
  with:
    version: 'latest'
    enable-cache: true  # ❌ 导致凭据错误
```

#### 修复方案
```yaml
- uses: astral-sh/setup-uv@v4
  with:
    version: 'latest'
    enable-cache: false  # ✅ 禁用缓存避免凭据问题
```

---

## 最终结果

### 健康检查响应
```json
{
  "status": "healthy",
  "version": "2.2.0",
  "database": {
    "connected": true,
    "article_count": 162,
    "error": null
  },
  "database_details": {
    "sources": {
      "36氪": 30,
      "ArXiv": 15,
      "Hacker News": 11,
      "MIT Technology Review": 10,
      "TechCrunch": 20,
      "V2EX": 19,
      "VentureBeat": 7,
      "机器之心": 12,
      "钛媒体": 18,
      "雷峰网": 20
    }
  },
  "env_info": {
    "env_type": "<class 'workers._workers._EnvWrapper'>",
    "has_DB": true
  }
}
```

### API 测试
```bash
curl https://ai-daily-collector.xxl185.workers.dev/api/v2/articles?page_size=5
```

**成功返回 162 篇文章数据！** ✅

---

## 关键知识点总结

### 1. Python Workers 绑定访问
- 使用 `self.env.BINDING_NAME` 访问绑定
- 不是通过方法参数 `env`
- 绑定名称必须与 `wrangler.toml` 中的 `binding` 一致

### 2. D1 数据库操作
- 所有 D1 API 调用都是异步的
- 必须使用 `await` 关键字
- 包括：`prepare()`, `all()`, `run()`, `first()` 等

### 3. 错误处理
- 添加 try-except 捕获详细错误信息
- 使用 `type(e).__name__` 获取异常类型
- 记录完整的错误堆栈便于调试

### 4. GitHub Actions 配置
- `setup-uv` 的 cache 功能可能需要额外的 token 配置
- 遇到凭据问题时可以禁用 cache

---

## 相关代码变更

### worker.py 主要修改

#### 绑定访问修复
```python
# 获取 D1 数据库绑定
try:
    worker_env = self.env
    if hasattr(worker_env, 'DB'):
        db = worker_env.DB
except Exception as e:
    db_error = f"Error accessing self.env.DB: {str(e)}"
```

#### 异步方法定义
```python
async def _execute_sql(self, sql, params=None):
    """通过 Workers D1 绑定执行 SQL（异步）"""
    try:
        stmt = self.db.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        result = await stmt.all()  # 关键：使用 await
        # ...
```

#### 文章查询
```python
async def fetch_articles(self, filters=None, limit=50, offset=0):
    """Fetch articles with optional filtering"""
    filters = filters or {}
    sql = "SELECT * FROM articles WHERE 1=1"
    params = []
    
    if "source" in filters:
        sql += " AND source = ?"
        params.append(filters["source"])
    
    sql += " ORDER BY ingested_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    result = await self._execute_sql(sql, params)  # 使用 await
    
    articles = []
    if result.get("success"):
        for row in result.get("results", []):
            articles.append(self._row_to_dict(row))
    
    return articles
```

---

## Git 提交记录

1. `debug: 添加 D1 数据库连接调试信息`
2. `debug: 添加 env 对象诊断信息`
3. `fix: 使用 self.env.DB 访问 D1 数据库绑定`
4. `feat: 自动创建 D1 数据库表结构`
5. `fix: 处理 D1 API 返回的不同结果格式`
6. `debug: 添加 schema 创建错误诊断`
7. `fix: D1 操作使用异步 await`
8. `debug: 改进错误处理，显示详细错误信息`
9. `fix: 禁用 uv cache 避免凭据错误`

---

## 经验教训

1. **仔细阅读官方文档**：Cloudflare Workers Python 的绑定访问方式与 JavaScript 不同
2. **注意异步操作**：Python Workers 中很多 API 都是异步的，容易遗漏 `await`
3. **添加详细日志**：在关键位置添加调试信息，便于快速定位问题
4. **分步骤排查**：从连接、查询、数据处理逐层排查

---

**解决时间**: 2026-02-12  
**总提交次数**: 9 次  
**最终状态**: ✅ 已解决，API 正常工作
