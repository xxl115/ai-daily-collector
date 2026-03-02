# Fix: D1 数据库编码问题修复

## 问题描述

数据库中的 summary、categories、tags 字段存在双重编码问题：
- **现象**: summary 字段存储的是原始 UTF-8 转义序列（如 `\u949b\u5a92\u4f53`），而不是正确的中文字符
- **原因**: 文本被 JSON 编码两次，编码后的字符串被当作普通文本存储

## 已完成

✅ 修复现有数据 - 22 条双重编码的记录已修复

## 待完成

### 修改 D1 适配器代码

修改 `ingestor/storage/d1_adapter.py`:

1. **添加 `_decode_double_encoded()` 方法** (在 `_article_to_row` 之前):

```python
def _decode_double_encoded(self, text: str) -> str:
    """Decode double-encoded Unicode strings.

    This handles the case where text has been JSON-encoded twice,
    resulting in strings like '\\u949b\\u5a92\\u4f53' instead of Chinese characters.

    Args:
        text: Potentially double-encoded text

    Returns:
        Decoded text
    """
    if not text:
        return text

    # Check if the text contains Unicode escape sequences
    if '\\u' not in text:
        return text

    try:
        # Try to decode the double-encoded string
        return text.encode('utf-8').decode('unicode_escape')
    except Exception:
        return text
```

2. **修改 `_article_to_row()` 方法**:
   - 对 `categories_json` 和 `tags_json` 添加 `ensure_ascii=False`
   - 对 `summary` 字段调用 `_decode_double_encoded`

```python
# 修改这两行:
categories_json = json.dumps(categories, ensure_ascii=False) if categories else "[]"
tags_json = json.dumps(tags, ensure_ascii=False) if tags else "[]"

# 添加 summary 解码:
summary = get("summary")
if summary:
    summary = self._decode_double_encoded(summary)
```

## 验证

修复代码后，测试 upsert_article 功能确保新的 summary 不会被双重编码。
