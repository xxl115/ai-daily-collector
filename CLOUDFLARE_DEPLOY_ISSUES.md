# Cloudflare Python Workers 部署问题记录

> 记录将 AI Daily Collector 部署到 Cloudflare Python Workers 过程中遇到的所有问题及解决方案

## 部署环境
- **Worker 名称**: `ai-daily-collector`
- **数据库**: Cloudflare D1
- **部署方式**: GitHub Actions + pywrangler
- **Python 版本**: 3.12+

---

## 问题清单

### 问题 1: 缺少 `python_workers` 兼容性标志

**错误信息**:
```
The `python_workers` compatibility flag is required to use Python
```

**原因**: 
Cloudflare Python Workers 处于 Beta 阶段，需要显式启用兼容性标志。

**解决方案**:
在 `wrangler.toml` 中添加：
```toml
compatibility_flags = ["python_workers"]
```

---

### 问题 2: 不支持 `requirements.txt`

**错误信息**:
```
Specifying Python Packages in requirements.txt is no longer supported, 
please use pyproject.toml instead.

requirements.txt exists. Delete the file to continue. Exiting.
```

**原因**:
`pywrangler` 只支持 `pyproject.toml`，不再支持 `requirements.txt`。

**解决方案**:
1. 删除 `requirements.txt`
2. 将所有依赖迁移到 `pyproject.toml` 的 `[project.dependencies]`

---

### 问题 3: Python 版本不兼容

**错误信息**:
```
Because the requested Python version (>=3.10) does not satisfy Python>=3.12 
and all versions of workers-runtime-sdk depend on Python>=3.12
```

**原因**:
`workers-runtime-sdk` 要求 Python >= 3.12。

**解决方案**:
更新 `pyproject.toml`：
```toml
requires-python = ">=3.12"
```

同时生成 `uv.lock` 文件用于依赖锁定。

---

### 问题 4: 缺少 `uv.lock` 文件

**错误信息**:
```
No matches found for glob **/uv.lock
make sure you have checked out the target repository
```

**原因**:
GitHub Actions 的 `astral-sh/setup-uv@v4` 需要 `uv.lock` 文件进行缓存。

**解决方案**:
```bash
uv lock
```
生成 `uv.lock` 文件并提交到仓库。

---

### 问题 5: 包不兼容 Workers（无预编译 wheel）

**错误信息**:
```
Because sgmllib3k==1.0.0 has no usable wheels and only sgmllib3k==1.0.0 is available
Because feedparser>=6.0.10 depends on sgmllib3k, we can conclude that feedparser>=6.0.10 cannot be used
```

**原因**:
Cloudflare Python Workers 运行在 WebAssembly/Pyodide 环境中，只支持有预编译 wheel 的包。`feedparser` 依赖的 `sgmllib3k` 没有可用 wheel。

**解决方案**:
将不兼容 Workers 的依赖移到 `[project.optional-dependencies]`：

```toml
[project]
dependencies = []  # 只放 Workers 兼容的包

[project.optional-dependencies]
local = [
    "requests>=2.31.0",
    "feedparser>=6.0.10",
    # ... 其他不兼容 Workers 的包
]
```

**Workers 不兼容的常见包**:
- `feedparser` (依赖 `sgmllib3k`)
- `requests` (可以用 `httpx` 替代)
- `PyYAML`
- `cryptography`
- `uvicorn`

---

### 问题 6: Worker 大小超过免费版限制

**错误信息**:
```
Your Worker exceeded the size limit of 3 MiB. 
Please upgrade to a paid plan to deploy Workers up to 10 MiB.

Here are the 5 largest dependencies:
- python_modules/pydantic_core/_pydantic_core.cpython-312-wasm32-emscripten.so - 4302.84 KiB
```

**原因**:
- 免费版限制：3 MiB
- 付费版限制：10 MiB
- `pydantic` 包单独就占 4.3 MiB

**解决方案**:
完全清空主依赖，Worker 只使用 Python 标准库：

```toml
[project]
dependencies = []  # 空的！
```

Worker 代码使用：
- `json` (标准库)
- `datetime` (标准库)
- `workers` SDK (由 Cloudflare 提供)

---

## 最终配置

### pyproject.toml

```toml
[project]
name = "ai-daily-collector"
version = "0.2.0"
requires-python = ">=3.12"
dependencies = []  # Workers 只使用标准库

[project.optional-dependencies]
# 本地开发使用（不兼容 Workers）
local = [
    "requests>=2.31.0",
    "feedparser>=6.0.10",
    "python-dateutil>=2.8.2",
    "PyYAML>=6.0.1",
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
]

# Cloudflare Python Workers 开发依赖
[dependency-groups]
dev = [
    "workers-py",
    "workers-runtime-sdk"
]
```

### wrangler.toml

```toml
name = "ai-daily-collector"
main = "worker.py"
compatibility_date = "2024-01-15"
compatibility_flags = ["python_workers"]

[[d1_databases]]
binding = "DB"
database_name = "ai-daily-collector"
database_id = "your-database-id-here"
```

### worker.py 关键结构

```python
from workers import WorkerEntrypoint, Response
import json
from datetime import datetime

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 处理请求
        pass
```

---

## 部署命令

本地测试：
```bash
uv run pywrangler dev
```

部署：
```bash
uv run pywrangler deploy
```

---

## 参考文档

- [Cloudflare Python Workers](https://developers.cloudflare.com/workers/languages/python/)
- [Python Workers Packages](https://developers.cloudflare.com/workers/languages/python/packages/)
- [Python Workers Basics](https://developers.cloudflare.com/workers/languages/python/basics/)
- [Worker Size Limits](https://developers.cloudflare.com/workers/platform/limits/#worker-size)

---

## 总结

Cloudflare Python Workers 的限制：
1. **Beta 阶段**: 需要 `python_workers` 兼容性标志
2. **依赖管理**: 只支持 `pyproject.toml`，不支持 `requirements.txt`
3. **Python 版本**: 要求 >= 3.12
4. **包兼容性**: 只支持有预编译 wheel 的包
5. **大小限制**: 免费版 3 MiB，付费版 10 MiB
6. **标准库**: 推荐使用纯标准库代码以控制大小

**最佳实践**: 
- Worker 代码保持最小化，只用标准库
- 数据收集逻辑在 GitHub Actions 中运行
- Worker 只负责 API 查询和数据库读取
