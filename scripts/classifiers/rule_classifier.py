"""
基于关键词的规则分类器
用于 AI / 科技新闻文章分类
"""

# 分类规则：category -> 关键词列表（按优先级排序）
CATEGORY_RULES = {
    "大厂/人物": [
        # 大厂
        "OpenAI",
        "Anthropic",
        "Google",
        "Meta",
        "微软",
        "Apple",
        "Apple",
        "Amazon",
        "英伟达",
        "NVIDIA",
        "AMD",
        "Intel",
        "高通",
        "三星",
        "华为",
        "阿里",
        "腾讯",
        "百度",
        "字节",
        "特斯拉",
        "Tesla",
        "SpaceX",
        "马斯克",
        "Sam Altman",
        "黄仁勋",
        "苏姿丰",
        # 大模型
        "GPT",
        "Claude",
        "Gemini",
        "Llama",
        "Mistral",
        "Qwen",
        "通义",
        "文心",
        "Kimi",
        "豆包",
    ],
    "Agent工作流": [
        "Agent",
        "智能体",
        "MCP",
        "Model Context Protocol",
        "A2A",
        "Autogen",
        "CrewAI",
        "LangChain",
        "LangGraph",
        "AutoGPT",
        "BabyAGI",
        "OpenAI Agents",
        "Agentic",
        "工作流",
        "Workflow",
        "RAG",
        "检索增强",
        "向量数据库",
    ],
    "编程助手": [
        "Cursor",
        "Windsurf",
        "Cline",
        "GitHub Copilot",
        "Codeium",
        "Tabnine",
        "IDE",
        "VS Code",
        "JetBrains",
        "编程",
        "代码生成",
        "代码补全",
        "重构",
        "Devin",
        "v0",
        "bolt.new",
        "Replit",
        " Lovable",
    ],
    "内容生成": [
        "Midjourney",
        "DALL-E",
        "Stable Diffusion",
        "SDXL",
        "Flux",
        "Runway",
        "视频生成",
        "Sora",
        "Runway",
        "Pika",
        "Luma",
        "Kling",
        "可灵",
        "语音合成",
        "TTS",
        "ElevenLabs",
        "音频生成",
        "音乐生成",
        "Suno",
        "Udio",
        "多模态",
        "图像生成",
        "AI绘画",
        "文字转视频",
        "文生视频",
        "图生视频",
    ],
    "工具生态": [
        "LangChain",
        "LlamaIndex",
        "Hugging Face",
        "PyTorch",
        "TensorFlow",
        "JAX",
        "Ollama",
        "LM Studio",
        "vLLM",
        "TensorRT",
        "llama.cpp",
        "Weights & Biases",
        "MLflow",
        "Comet",
        "LangSmith",
        "LangFuse",
        "API",
        "SDK",
        "开源",
        "框架",
        "库",
        "生态",
    ],
    "安全风险": [
        "安全",
        "漏洞",
        "攻击",
        "恶意",
        "病毒",
        "木马",
        "勒索",
        "隐私",
        "数据泄露",
        "GDPR",
        "合规",
        "监管",
        "Deepfake",
        "深度伪造",
        "幻觉",
        "AI幻觉",
        "投毒",
        "对抗",
        "越狱",
        "Prompt注入",
        "APT",
        "黑客",
        "数据安全",
        "网络安全",
    ],
    "算力基建": [
        "GPU",
        "TPU",
        "NPU",
        "芯片",
        "处理器",
        "算力",
        "智算中心",
        "训练",
        "推理",
        "部署",
        "模型压缩",
        "量化",
        "蒸馏",
        "A100",
        "H100",
        "H200",
        "B100",
        "昇腾",
        "寒武纪",
        "摩尔线程",
        "一体机",
        "服务器",
        "云计算",
        "AWS",
        "Azure",
        "GCP",
        "阿里云",
        "腾讯云",
    ],
    "商业应用": [
        "电商",
        "购物",
        "外卖",
        "餐饮",
        "零售",
        "物流",
        "供应链",
        "金融",
        "银行",
        "保险",
        "支付",
        "投资",
        "股票",
        "AI量化",
        "医疗",
        "教育",
        "法律",
        "咨询",
        "营销",
        "广告",
        "销售",
        "企业",
        "B2B",
        "SaaS",
        "创业",
        "融资",
        "IPO",
        "收购",
    ],
}

# 默认分类
DEFAULT_CATEGORY = "其他"

# 标签关键词（更细粒度）
TAG_RULES = {
    "LLM": ["大模型", "语言模型", "LLM", "GPT", "Claude", "Llama", "参数", "模型能力"],
    "多模态": ["多模态", "视觉", "图像", "视频", "音频", "语音", "理解"],
    "开源": ["开源", "Open Source", "Apache", "MIT", "GitHub", "社区"],
    "发布": ["发布", "上线", "更新", "版本", "新功能", "正式版", "公测"],
    "研究": ["论文", "arXiv", "研究", "实验", "学术", "技术报告", "白皮书"],
    "融资": ["融资", "投资", "估值", "IPO", "收购", "并购", "上市"],
    "财报": ["财报", "营收", "利润", "业绩", "收入", "增长", "季度"],
    "中国": ["中国", "国产", "本土", "国内", "北京", "上海", "深圳"],
    "国际": ["美国", "欧洲", "日本", "韩国", "海外", "全球", "国际"],
}


def classify(text: str) -> dict:
    """
    基于关键词规则对文章进行分类

    Args:
        text: 文章标题 + 内容

    Returns:
        {
            "category": "分类名称",
            "tags": ["标签1", "标签2", ...]
        }
    """
    if not text:
        return {"category": DEFAULT_CATEGORY, "tags": []}

    text_lower = text.lower()

    # 计算每个分类的匹配分数
    scores = {}
    for category, keywords in CATEGORY_RULES.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        if score > 0:
            scores[category] = score

    # 选择得分最高的分类
    if scores:
        category = max(scores, key=scores.get)
    else:
        category = DEFAULT_CATEGORY

    # 提取标签
    tags = []
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                tags.append(tag)
                break

    # 去重并限制标签数量
    tags = list(dict.fromkeys(tags))[:5]

    return {"category": category, "tags": tags}


def classify_with_confidence(text: str) -> dict:
    """
    带置信度的分类

    Returns:
        {
            "category": "分类名称",
            "category_score": 0.85,
            "tags": ["标签1", "标签2", ...],
            "all_scores": {"大厂/人物": 5, "Agent工作流": 2}
        }
    """
    if not text:
        return {
            "category": DEFAULT_CATEGORY,
            "category_score": 0.0,
            "tags": [],
            "all_scores": {},
        }

    text_lower = text.lower()

    # 计算每个分类的匹配分数
    scores = {}
    for category, keywords in CATEGORY_RULES.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        if score > 0:
            scores[category] = score

    # 计算置信度
    if scores:
        max_score = max(scores.values())
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0
        category = max(scores, key=scores.get)
    else:
        category = DEFAULT_CATEGORY
        confidence = 0.0

    # 提取标签
    tags = []
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                tags.append(tag)
                break

    tags = list(dict.fromkeys(tags))[:5]

    return {
        "category": category,
        "category_score": confidence,
        "tags": tags,
        "all_scores": scores,
    }


if __name__ == "__main__":
    # 测试
    test_texts = [
        "OpenAI 发布 GPT-5，带来全新多模态能力",
        "Cursor 推出新功能，支持自然语言编程",
        "英伟达发布 H200 芯片，推理性能提升 2 倍",
        "研究发现 GPT-4 存在严重幻觉问题",
        "阿里云推出 AI 一体机解决方案",
    ]

    for text in test_texts:
        result = classify_with_confidence(text)
        print(f"\n标题: {text}")
        print(f"分类: {result['category']} (置信度: {result['category_score']:.2f})")
        print(f"标签: {result['tags']}")
