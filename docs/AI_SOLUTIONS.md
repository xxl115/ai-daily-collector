# AI 推理方案对比文档

本文档对比了多种在 GitHub Actions 中进行 AI 推理（摘要、分类）的方案，方便根据需求切换。

---

## 方案概览

| # | 方案 | 免费额度 | GPU | 速度 | 中文支持 | 隐私 | 复杂度 |
|---|------|----------|-----|------|----------|------|--------|
| 1 | Cloudflare Workers AI | 10万次/天 | ✅ | 快 | ✅ | ✅ | 低 |
| 2 | 智谱 API | 200万Token/月 | - | 快 | ✅✅ | ❌ | 低 |
| 3 | Groq API | 有速率限制 | ✅ | 最快 | 一般 | ❌ | 低 |
| 4 | Gemini API | 15次/分钟 | ✅ | 快 | ✅ | ❌ | 低 |
| 5 | HuggingFace Spaces | 2核CPU | ❌ | 慢 | ✅ | ✅ | 中 |
| 6 | 本地 Ollama | 无限 | 自备 | 慢 | ✅ | ✅ | 中 |

---

## 方案详情

### 方案一：Cloudflare Workers AI（推荐）

**优势**
- 每天 10 万次免费请求
- 无需额外 API Key（与 Worker 绑定）
- 全球 CDN，延迟低
- 支持 Llama 3, Mistral, Gemma 等 50+ 模型

**劣势**
- 免费额度有速率限制
- 模型选择受限

**实现方式**
```python
# worker.py 中添加 AI 端点
from workers import WorkerEntrypoint

class Default(WorkerEntrypoint):
    async def on_fetch(self, request, env, ctx):
        # 调用 Workers AI
        response = await env.AI.run(
            "@cf/meta/llama-3-8b-instruct",
            {"prompt": f"总结：{text}"}
        )
```

**切换指数**：⭐⭐⭐⭐⭐（最简单，已在 Cloudflare 生态中）

---

### 方案二：智谱 API（国内首选）

**优势**
- 中文理解能力极强
- 免费额度充足（200万Token/月）
- 国内访问速度快
- 价格便宜

**劣势**
- 需要注册获取 API Key
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

**切换指数**：⭐⭐⭐⭐

---

### 方案三：Groq API

**优势**
- 推理速度最快
- 支持 Llama 3, Mixtral 等
- 免费额度尚可

**劣势**
- 国内访问可能不稳定
- 速率限制严格

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

### 方案四：Gemini API

**优势**
- 上下文极长（100万Token）
- Google 基础设施，稳定

**劣势**
- 国内访问不稳定
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

### 方案五：HuggingFace Spaces

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

**切换指数**：⭐⭐

---

### 方案六：本地 Ollama

**优势**
- 完全免费，无限使用
- 隐私最好

**劣势**
- GitHub Actions 无 GPU，无法运行
- 适合本地使用

**实现方式**
```python
import requests

def summarize(text):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5:1.5b", "prompt": f"总结：{text}"}
    )
    return response.json()["response"]
```

**切换指数**：⭐（需本地运行）

---

## 成本对比

| 方案 | 费用 | 超出费用 |
|------|------|----------|
| Cloudflare Workers AI | **免费** | 无 |
| 智谱 API | 免费额度 | ¥1/百万Token |
| Groq | 免费额度 | $0.05/千Token |
| Gemini | 免费额度 | $0.075/千Token |
| HuggingFace | 免费(CPU) | $0.26/小时(GPU) |
| 本地 Ollama | 需自备 GPU | 电费 |

---

## 推荐选择

| 场景 | 推荐方案 |
|------|----------|
| 个人项目，免费优先 | Cloudflare Workers AI |
| 高质量中文摘要 | 智谱 API |
| 追求最快速度 | Groq |
| 完全离线/隐私 | 本地 Ollama |

---

## 当前实现状态

- **摘要生成**：`scripts/summarizers/ollama_summarizer.py`（支持降级到原文截取）
- **分类**：`scripts/classifiers/bge_classifier.py`
- **Worker API**：`worker.py`

---

## 切换指南

### 切换到 Cloudflare Workers AI
1. 在 wrangler.toml 添加 AI binding
2. 修改 worker.py 添加 /api/v1/summarize 端点
3. 修改 content_processor.py 调用 Worker API

### 切换到智谱 API
1. 注册获取 API Key
2. 添加到 GitHub Secrets
3. 修改 `scripts/summarizers/ollama_summarizer.py` 为 `zhipu_summarizer.py`
4. 更新 content_processor.py 使用新 summarizer

---

## 相关链接

- [Cloudflare Workers AI 文档](https://developers.cloudflare.com/workers-ai/)
- [智谱 AI 开放平台](https://open.bigmodel.cn)
- [Groq Console](https://console.groq.com)
- [Google AI Studio](https://aistudio.google.com/app/apikey)
