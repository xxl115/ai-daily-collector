# AI Daily Collector - 代码审查问题追踪

> 创建日期: 2026-02-09
> 审查人: OpenClaw AI Assistant

---

## 🔴 高优先级问题

### 1. CORS 配置不安全

**位置**: `config/settings.py`
```python
cors_origins = os.environ.get("API_CORS_ORIGINS", "*").split(",")
```

**问题**: `*` 允许任何来源访问 API

**建议修复**:
```python
# 移除默认 *
cors_origins = os.environ.get("API_CORS_ORIGINS", "").split(",")
cors_origins = [o.strip() for o in cors_origins if o.strip()]  # 过滤空字符串
```

**严重度**: Medium | **状态**: 待修复

---

### 2. 缺少并发采集

**位置**: `scripts/daily-ai-workflow.py`

**问题**: 所有数据源顺序同步执行，效率低
```python
for source in sources_config.get('sources', []):
    items = fetch_by_config(source)  # 阻塞等待
```

**建议修复**: 使用 asyncio 并发采集
```python
import asyncio

async def collect_all_concurrent(sources):
    tasks = [fetch_by_config(s) for s in sources if s.get('enabled')]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**严重度**: Medium | **状态**: 待修复

---

## 🟡 中优先级问题

### 3. API Key 未加密

**位置**: `config/settings.py`

**问题**: API Keys 以明文存储在环境变量和配置文件中

**建议**:
- 使用加密密钥管理（如 HashiCorp Vault、AWS Secrets Manager）
- 或简单加密配置文件

**严重度**: Low | **状态**: 待修复

### 4. 缺少输入验证

**位置**: `config/settings.py`

**问题**: 环境变量没有验证类型和范围
```python
api_port = int(os.environ.get("API_PORT", 8000))  # 可能抛出异常
retry_times = int(os.environ.get("RETRY_TIMES", 3))
```

**建议修复**:
```python
def validate_port(value, default=8000):
    try:
        port = int(value)
        if 1 <= port <= 65535:
            return port
        raise ValueError("Port out of range")
    except (ValueError, TypeError):
        return default

api_port = validate_port(os.environ.get("API_PORT"))
```

**严重度**: Low | **状态**: 待修复

### 5. 硬编码数值

**位置**: `scripts/daily-ai-workflow.py`

**问题**:
```python
limit = config.get("max_articles", 50)  # 硬编码 50
articles[:30]  # 硬编码 30
```

**建议**: 移入配置文件或命令行参数

**严重度**: Low | **状态**: 待修复

---

## 📋 改进建议汇总

### 代码质量

| 问题 | 影响 | 建议 |
|------|------|------|
| 顺序执行采集 | 慢（所有源等待最慢的） | 改为并发 |
| 无重试机制 | 网络抖动导致失败 | 添加指数退避重试 |
| 错误日志简单 | 难以排查问题 | 添加请求 ID、状态码 |

### 安全性

| 问题 | 影响 | 建议 |
|------|------|------|
| CORS:* | 任何网站可调用 API | 限制来源 |
| 明文 Key | 泄露风险 | 加密存储 |

### 性能

| 问题 | 影响 | 建议 |
|------|------|------|
| 无缓存层 | 重复请求 | 添加 Redis 缓存 |
| 无限速 | 可能被封 IP | 实现速率限制 |

---

## 📝 待办清单

- [ ] 修复 CORS 配置
- [ ] 实现并发采集
- [ ] 添加环境变量验证
- [ ] 移除硬编码数值
- [ ] 实现错误重试机制
- [ ] 补充单元测试

---

## 📚 相关文档

- `ARCHITECTURE.md` - 系统架构
- `config/settings.py` - 配置详情
- `scripts/daily-ai-workflow.py` - 主工作流
