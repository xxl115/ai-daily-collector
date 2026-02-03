# 数据源架构重构设计

**日期**: 2025-02-03
**作者**: AI Assistant
**状态**: 设计完成，待实施

---

## 一、问题概述

### 当前问题

1. **配置文件未被使用**：`config/sources.yaml` 定义了 9 个数据源，但没有脚本读取它
2. **GitHub Actions 使用硬编码脚本**：`scripts/collect-real.py` 完全没有使用配置文件
3. **中文数据源缺失**：36氪、机器之心、钛媒体、雷锋网、量子位等中文源都没有被采集
4. **脚本导入错误**：`scripts/daily-ai-workflow.py` 导入了不存在的 `collectors` 模块
5. **fetchers 未被使用**：`fetchers/` 目录有完整的抓取器实现，但都没被调用

### 设计目标

1. **单一配置源**：`sources.yaml` 作为唯一数据源配置
2. **支持中文数据源**：必须支持 36氪、机器之心、钛媒体、雷锋网、量子位
3. **修复现有脚本**：让 `daily-ai-workflow.py` 可以正常运行
4. **配置驱动**：添加/禁用数据源只需修改 YAML，无需改代码

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    config/sources.yaml                      │
│                    (唯一配置源)                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │   读取配置 & 调度      │
                │   scripts/collect*.py │
                └───────────┬───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ tech_media.py│   │  qbitai.py   │   │   v2ex.py    │
│ (中英文媒体) │   │  (量子位API) │   │  (V2EX)      │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────┴────────┐
                    │  data/daily.json│
                    └────────────────┘
```

### 2.2 类型映射

| sources.yaml type | 对应模块 | 说明 |
|-------------------|----------|------|
| `tech_media` | `fetchers/tech_media.py` | 中英文科技媒体 RSS |
| `api` | `fetchers/qbitai.py` | 量子位 API |
| `v2ex` | `fetchers/v2ex.py` | V2EX 热门 |
| `newsnow` | `fetchers/newsnow.py` | NewsNow 中文热点 |
| `reddit` | `fetchers/reddit.py` | Reddit |

---

## 三、配置文件结构

### 3.1 sources.yaml 扩展

```yaml
sources:
  # 英文科技媒体
  - name: "MIT Tech Review"
    type: "tech_media"
    media_id: "mit-tech"
    url: "https://www.technologyreview.com/feed/"
    enabled: true
    language: "en"
    filters:
      keyword: "AI|artificial intelligence"
      hours: 24
      max_articles: 10

  # 中文科技媒体
  - name: "36氪"
    type: "tech_media"
    media_id: "36kr"
    url: "https://36kr.com/feed/"
    enabled: true
    language: "zh"
    filters:
      keyword: "AI|人工智能|大模型"
      hours: 24
      max_articles: 30

  - name: "机器之心"
    type: "tech_media"
    media_id: "jiqizhixin"
    url: "https://www.jiqizhixin.com/rss"
    enabled: true
    language: "zh"
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 20

  - name: "钛媒体"
    type: "tech_media"
    media_id: "tmtpost"
    url: "https://www.tmtpost.com/feed"
    enabled: true
    language: "zh"
    filters:
      keyword: "AI|人工智能"
      hours: 24
      max_articles: 20

  - name: "雷锋网"
    type: "tech_media"
    media_id: "leiphone"
    url: "https://www.leiphone.com/feed"
    enabled: true
    language: "zh"
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 20

  # API 源
  - name: "量子位"
    type: "api"
    url: "https://api.qbitai.com/v1/articles"
    enabled: true
    language: "zh"
    filters:
      keyword: "AI"
      hours: 24
      max_articles: 30
```

---

## 四、Fetcher 扩展

### 4.1 扩展 fetchers/tech_media.py

在 `MEDIA` 字典中增加中文科技媒体：

```python
MEDIA = {
    # ... 现有英文媒体 ...

    # 中文科技媒体
    "36kr": {
        "name": "36氪",
        "url": "https://36kr.com/",
        "rss": "https://36kr.com/feed/",
        "language": "zh",
        "selectors": {
            "article": ".item-item",
            "title": ".item-title a",
            "link": ".item-title a",
            "summary": ".item-desc",
        }
    },
    "jiqizhixin": {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/",
        "rss": "https://www.jiqizhixin.com/rss",
        "language": "zh",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
    "tmtpost": {
        "name": "钛媒体",
        "url": "https://www.tmtpost.com/",
        "rss": "https://www.tmtpost.com/feed",
        "language": "zh",
        "selectors": {
            "article": ".post-item",
            "title": ".post-title a",
            "link": ".post-title a",
            "summary": ".post-excerpt",
        }
    },
    "leiphone": {
        "name": "雷锋网",
        "url": "https://www.leiphone.com/",
        "rss": "https://www.leiphone.com/feed",
        "language": "zh",
        "selectors": {
            "article": "article",
            "title": "h2 a",
            "link": "h2 a",
            "summary": ".summary",
        }
    },
}
```

### 4.2 新建 fetchers/qbitai.py

```python
"""
量子位 API 抓取器
"""

from typing import List, Dict
import requests
from datetime import datetime

class QbitaiFetcher:
    """量子位 API 抓取器"""

    API_URL = "https://api.qbitai.com/v1/articles"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    def fetch(self, limit: int = 30, keyword: str = "AI") -> List[Dict]:
        """采集量子位文章"""
        articles = []

        try:
            # 量子位 API 具体实现需要根据实际 API 调整
            response = self.session.get(
                self.API_URL,
                params={"limit": limit, "keyword": keyword},
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            for item in data.get("articles", []):
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": item.get("summary", "")[:300],
                    "source": "量子位",
                    "published_at": item.get("published_at", ""),
                    "timestamp": datetime.now().isoformat(),
                    "hot_score": item.get("views", 0),
                })

        except Exception as e:
            print(f"❌ 量子位 API 失败: {e}")

        return articles

# 全局实例
qbitai_fetcher = QbitaiFetcher()

def fetch_qbitai(limit: int = 30) -> List[Dict]:
    """采集量子位"""
    return qbitai_fetcher.fetch(limit)
```

### 4.3 统一调度接口

在 `fetchers/__init__.py` 中增加：

```python
def fetch_by_config(source_config: dict) -> List[Dict]:
    """
    根据 sources.yaml 中的配置调用对应的 fetcher

    Args:
        source_config: 单个数据源的配置字典

    Returns:
        采集到的文章列表
    """
    source_type = source_config.get("type")

    if source_type == "tech_media":
        media_id = source_config.get("media_id")
        limit = source_config.get("filters", {}).get("max_articles", 10)
        result = tech_media_fetcher.fetch_rss(media_id)
        if not result:
            result = tech_media_fetcher.fetch_html(media_id)
        return result[:limit] if result else []

    elif source_type == "api":
        limit = source_config.get("filters", {}).get("max_articles", 30)
        return fetch_qbitai(limit=limit)

    elif source_type == "v2ex":
        limit = source_config.get("filters", {}).get("max_articles", 20)
        return fetch_v2ex_hotspots(limit=limit)

    elif source_type == "newsnow":
        limit = source_config.get("filters", {}).get("max_articles", 30)
        return fetch_newsnow_hotspots(limit=limit)

    else:
        print(f"⚠️ 未知的数据源类型: {source_type}")
        return []
```

---

## 五、统一采集脚本

### 5.1 重构 scripts/collect-real.py

```python
#!/usr/bin/env python3
"""
AI Daily Collector - 统一采集脚本
从 sources.yaml 读取配置，调用对应的 fetcher
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 导入 fetchers
from fetchers import fetch_by_config

def load_sources_config() -> dict:
    """加载 sources.yaml"""
    config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def collect_with_fallback(sources_config: dict) -> tuple[List[Dict], List[str]]:
    """
    带降级策略的采集

    Returns:
        (成功采集的数据, 失败的数据源名称列表)
    """
    results = []
    failures = []

    print("📥 开始采集数据源...")

    for source in sources_config['sources']:
        if not source.get('enabled', False):
            continue

        source_name = source['name']
        print(f"\n📡 采集: {source_name}")

        try:
            items = fetch_by_config(source)
            if items:
                results.extend(items)
                print(f"   ✅ {len(items)} 条")
            else:
                print(f"   ⚠️ 无数据")
                failures.append(source_name)
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failures.append(source_name)

    if failures:
        print(f"\n⚠️ 失败的数据源: {', '.join(failures)}")

    return results, failures

def sort_by_hot_score(items: List[Dict]) -> List[Dict]:
    """按热度排序"""
    return sorted(items, key=lambda x: x.get('hot_score', 0), reverse=True)

def generate_report(items: List[Dict]) -> dict:
    """生成日报"""
    return {
        'success': True,
        'title': f'AI Daily - {datetime.now().strftime("%Y-%m-%d")}',
        'generated_at': datetime.now().isoformat(),
        'total_collected': len(items),
        'hotspots': items,
    }

def main():
    print("🚀 AI Daily Collector - 统一采集")
    print("=" * 50)

    # 加载配置
    config = load_sources_config()
    print(f"📋 配置的数据源: {len(config['sources'])} 个")
    enabled = [s['name'] for s in config['sources'] if s.get('enabled')]
    print(f"✅ 已启用: {', '.join(enabled)}")

    # 采集数据
    items, failures = collect_with_fallback(config)

    if not items:
        print("\n❌ 没有采集到任何数据")
        return 1

    # 排序
    items = sort_by_hot_score(items)

    # 生成报告
    report = generate_report(items)

    # 保存
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    output_file = data_dir / 'daily.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("✅ 采集完成!")
    print(f"   总计: {report['total_collected']} 条")
    print(f"   文件: {output_file}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

---

## 六、修复 daily-ai-workflow.py

### 6.1 修复导入错误

```python
# 修改前（错误）:
from collectors.github import fetch_github_trending
from collectors.hackernews import fetch_hacker_news
from collectors.producthunt import fetch_product_hunt
from collectors.rss_collector import fetch_rss_sources

# 修改后（正确）:
from fetchers.v2ex import fetch_v2ex_hotspots
from fetchers.reddit import fetch_reddit_hotspots
from fetchers.tech_media import fetch_tech_media_hotspots
from fetchers.ai_blogs import fetch_ai_blog_hotspots
from fetchers.newsnow import fetch_newsnow_hotspots
```

### 6.2 使用配置文件

```python
import yaml

def load_sources_config():
    """加载 sources.yaml"""
    config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def collect_all_sources(config: Dict) -> Dict[str, List[Dict]]:
    """采集所有数据源（根据配置）"""
    results = {}
    sources_config = load_sources_config()

    for source in sources_config['sources']:
        if not source.get('enabled'):
            continue

        source_name = source['name']
        try:
            items = fetch_by_config(source)
            if items:
                results[source_name] = items
        except Exception as e:
            print(f"❌ {source_name}: {e}")

    return results
```

---

## 七、实施步骤

### 7.1 第一阶段：Fetcher 扩展

1. 扩展 `fetchers/tech_media.py`，添加中文媒体
2. 新建 `fetchers/qbitai.py`
3. 在 `fetchers/__init__.py` 中添加 `fetch_by_config()` 函数
4. 测试各个 fetcher 是否正常工作

### 7.2 第二阶段：脚本重构

1. 重构 `scripts/collect-real.py` 使用配置文件
2. 修复 `scripts/daily-ai-workflow.py` 的导入错误
3. 测试脚本是否正常运行

### 7.3 第三阶段：GitHub Actions 更新

1. 更新 `.github/workflows/scheduled-collection.yml`
2. 确保依赖包完整（PyYAML 等）
3. 运行测试 workflow

---

## 八、测试计划

### 8.1 单元测试

```bash
# 测试各个 fetcher
pytest tests/test_fetchers.py

# 测试配置加载
pytest tests/test_config.py
```

### 8.2 集成测试

```bash
# 运行完整采集脚本
python scripts/collect-real.py

# 检查输出
cat data/daily.json
```

### 8.3 中文数据源测试

```yaml
# 测试配置
test_sources:
  - name: "36氪"
    type: "tech_media"
    media_id: "36kr"
    enabled: true
```

---

## 九、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 中文媒体 RSS 不可用 | 中 | HTML 抓取作为备选 |
| 量子位 API 变化 | 低 | 版本控制，快速回滚 |
| 配置文件格式错误 | 低 | YAML schema 验证 |
| 部分数据源失败 | 低 | 优雅降级，继续采集其他源 |

---

## 十、后续优化

1. **配置验证**：添加 JSON Schema 验证配置文件格式
2. **性能优化**：并发采集多个数据源
3. **缓存机制**：避免重复采集
4. **监控告警**：数据源失败时发送通知
5. **单元测试**：为每个 fetcher 添加测试用例

---

**设计完成日期**: 2025-02-03
**预计工作量**: 4-6 小时
