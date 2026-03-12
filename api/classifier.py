"""文章分类模块"""

# 默认分类规则
DEFAULT_CATEGORY = "其他"

CATEGORY_RULES = {
    "大厂": ["阿里", "腾讯", "百度", "字节", "华为", "小米", "京东", "美团", "拼多多", "网易", "滴滴", "快手", "抖音", "字节跳动"],
    "人物": ["马斯克", "黄仁勋", "Sam Altman", "山姆·奥特曼", "纳德拉", "皮查伊", "扎克伯格", "库克", "周鸿祎", "张一鸣", "马化腾", "马云", "李彦宏", "雷军"],
    "产品": ["发布", "新品", "产品", "上市", "发布", "推出", "上线", "发布"],
    "技术": ["芯片", "模型", "算法", "论文", "研究", "GPT", "LLM", "AI", "大模型", "训练", "推理", "GPU", "NLP", "CV"],
    "投资": ["融资", "投资", "收购", "估值", "IPO", "上市", "亿美元", "亿元", "融资"],
    "安全": ["漏洞", "攻击", "隐私", "安全", "黑客", "勒索", "数据泄露"],
    "商业": ["财报", "营收", "利润", "增长", "市场", "份额", "竞争"],
    "其他": [],
}

TAG_RULES = {
    "AI": ["AI", "人工智能", "大模型", "GPT", "LLM", "AGI"],
    "大模型": ["大模型", "LLM", "GPT-4", "Claude", "Gemini"],
    "芯片": ["芯片", "GPU", "NPU", "处理器", "半导体"],
    "自动驾驶": ["自动驾驶", "无人驾驶", "Robotaxi", "智驾"],
    "机器人": ["机器人", "人形机器人", "机器狗"],
    "投资": ["融资", "投资", "收购", "IPO"],
    "产品发布": ["发布", "新品", "上市", "推出"],
}


def classify(text, category_rules=None, tag_rules=None):
    """
    分类函数
    
    Args:
        text: 待分类文本
        category_rules: 可选的分类规则
        tag_rules: 可选的标签规则
    
    Returns:
        dict: {
            "category": str,      # 分类
            "category_confidence": float,  # 置信度
            "tags": list        # 标签列表
        }
    """
    if not text:
        return {
            "category": DEFAULT_CATEGORY,
            "category_confidence": 0.0,
            "tags": [],
            "scores": {}
        }
    
    # 使用传入的规则或默认规则
    rules = category_rules if category_rules else CATEGORY_RULES
    tags_rules = tag_rules if tag_rules else TAG_RULES
    
    text_lower = text.lower()
    scores = {}
    
    # 计算每个分类的得分
    for category, keywords in rules.items():
        if not keywords:  # 跳过空规则
            continue
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score
    
    # 选择最高分类
    if scores:
        category = max(scores, key=scores.get)
        confidence = scores[category] / sum(scores.values())
    else:
        category = DEFAULT_CATEGORY
        confidence = 0.0
    
    # 提取标签
    tags = []
    for tag, keywords in tags_rules.items():
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(tag)
    
    return {
        "category": category,
        "category_confidence": round(confidence, 2),
        "tags": tags[:5],  # 最多 5 个标签
        "scores": scores,
    }


def classify_by_title(title, category_rules=None, tag_rules=None):
    """仅用标题分类"""
    return classify(title, category_rules, tag_rules)


# 测试
if __name__ == "__main__":
    test_texts = [
        "马斯克发布新款特斯拉AI芯片",
        "阿里云发布新一代大模型",
        "腾讯财报营收增长20%",
        "研究人员提出新的NLP算法",
    ]
    
    for text in test_texts:
        result = classify(text)
        print(f"文本: {text[:20]}...")
        print(f"  分类: {result['category']} ({result['category_confidence']})")
        print(f"  标签: {result['tags']}")
        print()
