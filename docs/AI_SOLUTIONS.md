# AI 推理方案对比文档

本文档对比了多种在 GitHub Actions 中进行 AI 推理（摘要、分类）的方案，方便根据需求切换。

---

## 方案概览

| # | 方案 | 免费额度 | GPU | 速度 | 中文支持 | 隐私 | 复杂度 |
|---|------|----------|-----|------|----------|------|--------|
| 1 | 智谱 API (ZHIPU) | GLM-4-Flash 永久免费，新用户送2000万 Tokens | - | 快 | ✅✅ | ❌ | 低 |
| 2 | 通义千问 (阿里云) | Qwen-Max: 100万 Tokens/90天 | - | 快 | ✅ | ❌ | 低 |
| 3 | Groq API | 有免费额度（需注册查看） | ✅ | 最快 | 一般 | ❌ | 低 |
| 4 | Gemini API | 15 RPM，100K TPM（约1500次/天） | ✅ | 快 | ✅ | ❌ | 低 |
| 5 | Kimi (Moonshot AI) | 注册送100万 Tokens（限时） | - | 快 | ✅ | ❌ | 低 |
| 6 | Jina Reader | 200次/分钟 | ❌ | 快 | ✅ | ✅ | 低 |
| 7 | HuggingFace Spaces | 2核CPU，16GB RAM | ❌ | 慢 | ✅ | ✅ | 中 |
| 8 | Cloudflare Workers AI | 10K Neurons/天（严重不足） | ✅ | 快 | ✅ | ✅ | 低 |

---

## 场景需求估算

### 每日 30 篇文章摘要的需求

| 方案 | 每日消耗 | 免费额度 | 是否够用 |
|------|---------|----------|----------|
| 智谱 | ~60K tokens | GLM-4-Flash 免费 | ✅ 充足 |
| 通义千问 | ~60K tokens | 100万/90天 | ✅ 充足 |
| Groq | ~60K tokens | 有额度 | ⚠️ 需确认 |
| Gemini | ~60K tokens | 15 RPM × 1440分钟 ≈ 21,600次/天 | ❌ 不够 |
| Cloudflare Workers AI | ~1500K Neurons | 10K Neurons/天 | ❌ 严重不足 |

---

## 方案详情

### 方案一：智谱 API（最推荐）

**优势**
- GLM-4-Flash 模型永久免费
- 新用户赠送 2000万 Tokens 体验包
- 每分钟 60 次请求
- 中文理解能力极强
- 国内访问速度快

**劣势**
- 数据需发送到第三方

**实现方式**
```python
from zhipuai import ZhipuAI

def summarize(text):
    client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": f"用50字概括：{text[:2000]}"}]
    )
    return response.choices[0].message.content
```

**配置步骤**
1. 注册 https://open.bigmodel.cn
2. 获取 API Key
3. 添加到 GitHub Secrets: `ZHIPU_API_KEY`

**切换指数**：⭐⭐⭐⭐（免费额度最充足）

---

### 方案二：通义千问（阿里云）

**优势**
- 100万 Tokens/90天有效期
- 极低价格：¥1.6/百万 Token
- 国内访问快

**劣势**
- 需要阿里云账号

**实现方式**
```python
import requests

def summarize(text):
    response = requests.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        headers={"Authorization": f"Bearer {os.getenv('QWEN_API_KEY')}"},
        json={
            "model": "qwen-max",
            "input": f"总结：{text[:2000]}"
        }
    )
    return response.json()["Output"]["text"]
```

**切换指数**：⭐⭐⭐

---

### 方案三：Gemini API

**优势**
- 上下文极长（100万 Token）
- Google 基础设施，稳定
- 无需信用卡
- 免费额度：15 RPM, 100K TPM

**劣势**
- 国内访问可能不稳定
- 免费额度有限

**实现方式**
```python
import requests

def summarize(text):
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        params={"key": os.getenv("GEMINI_API_KEY")},
        json={"contents": [{"parts": [{"text": f"总结：{text}"}]}]}
    )
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
```

**切换指数**：⭐⭐⭐

---

### 方案四：Groq API

**优势**
- 推理速度最快
- 支持 Llama 3, Mixtral, Gemma 等模型
- 免费额度尚可

**劣势**
- 速率限制严格
- 国内访问可能不稳定

**实现方式**
```python
import requests

def summarize(text):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
        json={
            "model": "llama-3.1-70b-versatile",
            "messages": [{"role": "user", "content": f"总结：{text}"}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

**切换指数**：⭐⭐⭐

---

### 方案五：Kimi (Moonshot AI)

**优势**
- 注册送 100万 Tokens（限时）
- 中文好
- Tier 0 有免费版本

**劣势**
- 通过 OpenRouter 调用

**实现方式**
```python
import requests

def summarize(text):
    response = requests.post(
        "https://api.moonshot.cn/v1/chat",
        headers={"Authorization": f"Bearer {os.getenv('KIMI_API_KEY')}"},
        json={"model": "kimi", "messages": [{"role": "user", "content": f"总结：{text}"}]}
    )
    return response.json()["choices"][0]["message"]["content"]
```

**切换指数**：⭐⭐⭐

---

### 方案六：Jina Reader（已有集成）

**优势**
- 你已集成在项目中
- 200次/分钟
- 免费（有 API key）

**劣势**
- 仅内容提取，非推理

**切换指数**：⭐⭐⭐（已在使用）

---

### 方案七：HuggingFace Spaces

**优势**
- 完全免费（CPU）
- 隐私性好

**劣势**
- CPU 推理极慢
- 容易超时

**实现方式**
```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
result = summarizer(text, max_length=100, min_length=30)
```

**切换指数**：⭐（不推荐，太慢）

---

### 方案八：Cloudflare Workers AI

**优势**
- 每天 10K Neurons 免费额度
- 全球 CDN，延迟低
- 无需额外 API Key

**劣势**
- 免费额度严重不足

**成本计算**
- 10K Neurons ≈ 2,000-4,000 tokens
- 每篇摘要约需 50K Neurons（2000 tokens）
- 10K Neurons 只能处理约 0.04-0.2 篇文章
- 每天处理 30 篇 ≈ 1500K Neurons，超出免费额度

**结论**：❌ 免费额度严重不足，不推荐用于内容处理

---

## 成本对比

| 方案 | 费用 | 超出费用 |
|------|------|----------|
| 智谱 API | 免费 + 调用量限制 | ¥1/百万 Token |
| 通义千问 | 免费（100万/90天） | ¥1.6/百万 Token |
| Groq | 免费额度 | $0.05/千 Token |
| Gemini | 免费额度 | $0.075/千 Token |
| HuggingFace | 免费(CPU) | $0.26/小时(GPU) |
| Cloudflare Workers AI | 免费 | 超出需付费 |

---

## 推荐选择

| 场景 | 推荐方案 |
|------|----------|
| 中文摘要为主，免费额度充足 | **智谱** (GLM-4-Flash 永久免费) |
| 追求最快推理速度 | **Groq** |
| 100万长上下文 | **Gemini** |
| 内容提取 | **Jina Reader**（已集成） |

---

## 当前实现状态

- **摘要生成**：`scripts/summarizers/ollama_summarizer.py`（支持降级到原文截取）
- **分类**：`scripts/classifiers/bge_classifier.py`
- **Worker API**：`worker.py`
- **Jina Reader**：已集成

---

## 切换指南

### 切换到智谱 API
1. 注册获取 API Key
2. 添加到 GitHub Secrets: `ZHIPU_API_KEY`
3. 创建 `scripts/summarizers/zhipu_summarizer.py`
4. 更新 `content_processor.py` 使用新 summarizer

### 切换到通义千问
1. 获取阿里云 API Key
2. 添加到 GitHub Secrets: `QWEN_API_KEY`
3. 创建 `scripts/summarizers/qwen_summarizer.py`
4. 更新 `content_processor.py` 使用新 summarizer

---

## 相关链接

- [智谱 AI 开放平台](https://open.bigmodel.cn)
- [通义千问](https://help.aliyun.com/zh/model-studio)
- [Groq Console](https://console.groq.com)
- [Google AI Studio](https://aistudio.google.com/app/apikey)
- [Cloudflare Workers AI 文档](https://developers.cloudflare.com/workers-ai/)
