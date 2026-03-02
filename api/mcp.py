"""MCP (Model Context Protocol) Tools for AI Daily Collector"""

from fastapi import APIRouter
from pydantic import BaseModel

from config.config import get_storage_adapter
from api.storage.dao import ArticleDAO


router = APIRouter(prefix="/mcp", tags=["MCP"])

CATEGORY_RULES = {
    "大厂/人物": [
        "OpenAI",
        "Anthropic",
        "Google",
        "Meta",
        "微软",
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
        "MiniMax",
        "阶跃星辰",
        "智谱",
        " Minimax",
    ],
    "Agent工作流": [
        "Agent",
        "智能体",
        "MCP",
        "A2A",
        "Autogen",
        "CrewAI",
        "LangChain",
        "LangGraph",
        "AutoGPT",
        "BabyAGI",
        "工作流",
        "Workflow",
        "RAG",
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
        "Devin",
        "v0",
        "GitHub",
        "Star",
        "开源",
        "V2EX",
    ],
    "内容生成": [
        "Midjourney",
        "DALL-E",
        "Stable Diffusion",
        "SDXL",
        "Runway",
        "视频生成",
        "Sora",
        "Pika",
        "Luma",
        "Kling",
        "可灵",
        "语音合成",
        "TTS",
        "ElevenLabs",
        "音乐生成",
        "Suno",
        "Udio",
        "多模态",
        "图像生成",
        "AI绘画",
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
        "框架",
        "API",
        "SDK",
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
        "黑客",
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
        "E-bike",
        "电动车",
        "新能源车",
        "自动驾驶",
        "无人驾驶",
        "智能驾驶",
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
        "IPO",
        "港交所",
        "医疗",
        "健康",
        "血糖仪",
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
        "收购",
        "并购",
        "手机",
        "魅族",
        "小米",
        "OPPO",
        "VIVO",
        "荣耀",
        "订单",
        "财报",
        "营收",
        "利润",
        "业绩",
    ],
}

TAG_RULES = {
    "LLM": ["大模型", "语言模型", "LLM", "GPT", "Claude", "AI", "模型"],
    "编程": ["编程", "代码", "开发", "程序员", "技术", "GitHub"],
    "多模态": ["多模态", "视觉", "图像", "视频", "音频", "语音"],
    "开源": ["开源", "Open Source", "Apache", "MIT", "GitHub", "社区"],
    "发布": ["发布", "上线", "更新", "版本", "新功能", "公测"],
    "研究": ["论文", "arXiv", "研究", "实验", "学术", "技术报告", "白皮书"],
    "融资": ["融资", "投资", "估值", "IPO", "收购", "并购", "上市"],
    "财报": ["财报", "营收", "利润", "业绩", "收入", "增长", "季度", "股价"],
    "中国": ["中国", "国产", "本土", "国内", "北京", "上海", "深圳"],
    "国际": ["美国", "欧洲", "日本", "韩国", "海外", "全球", "国际"],
    "创业": ["创业", "创始人", "CEO", "创业", "公司成立"],
    "IPO": ["IPO", "港交所", "上市", "融资", "估值"],
}

DEFAULT_CATEGORY = "其他"


def classify(text: str) -> dict:
    if not text:
        return {"category": DEFAULT_CATEGORY, "tags": [], "scores": {}}

    text_lower = text.lower()
    scores = {}

    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        category = max(scores, key=scores.get)
        confidence = scores[category] / sum(scores.values())
    else:
        category = DEFAULT_CATEGORY
        confidence = 0.0

    tags = []
    for tag, keywords in TAG_RULES.items():
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(tag)

    return {
        "category": category,
        "category_confidence": round(confidence, 2),
        "tags": tags[:5],
    }


class MCPRequest(BaseModel):
    tool: str
    arguments: dict = {}


class ArticleSummaryRequest(BaseModel):
    summary: str
    auto_classify: bool = True
    tags: list[str] | None = None


@router.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "get_articles_needing_processing",
                "description": "获取需要处理的文章列表（需要总结、分类或标签）",
            },
            {
                "name": "update_article_summary",
                "description": "更新文章摘要（支持自动分类和手动指定标签）",
            },
            {"name": "classify_article", "description": "自动分类文章"},
            {"name": "list_categories", "description": "列出分类规则"},
        ]
    }


@router.post("/call")
async def call_mcp_tool(request: MCPRequest):
    tool_name = request.tool
    arguments = request.arguments

    storage = get_storage_adapter()
    dao = ArticleDAO(storage) if storage else None

    if not dao:
        return {"error": "Storage not configured"}

    if tool_name == "get_articles_needing_processing":
        # 统一获取需要处理的文章（需要总结、分类或标签）
        limit = arguments.get("limit", 10)
        articles = dao.fetch_articles(limit=100)
        result = []
        for a in articles:
            if a.content:
                needs_summary = not a.summary or a.summary == ""
                needs_category = not a.categories or len(a.categories) == 0
                needs_tags = not a.tags or len(a.tags) == 0
                # 只返回需要处理的文章
                if needs_summary or needs_category or needs_tags:
                    result.append(
                        {
                            "id": a.id,
                            "title": a.title,
                            "url": a.url,
                            "source": a.source,
                            "needs_summary": needs_summary,
                            "needs_category": needs_category,
                            "needs_tags": needs_tags,
                            "content_preview": (
                                a.content[:300] + "..."
                                if len(a.content) > 300
                                else a.content
                            ),
                            "content_length": len(a.content) if a.content else 0,
                        }
                    )
                    if len(result) >= limit:
                        break
        return {"success": True, "count": len(result), "articles": result}

    elif tool_name == "update_article_summary":
        article_id = arguments.get("article_id")
        summary = arguments.get("summary")
        auto_classify = arguments.get("auto_classify", True)
        tags = arguments.get("tags")

        if not article_id or not summary:
            return {"error": "Missing article_id or summary"}

        article = dao.fetch_article_by_id(article_id)
        if not article:
            return {"error": "Article not found"}

        article.summary = summary

        # 自动分类（可选）
        category_result = None
        if auto_classify and article.content:
            text = article.content + " " + (article.title or "") + " " + summary
            category_result = classify(text)
            article.categories = [category_result["category"]]
            article.tags = category_result["tags"]

        # 手动指定标签（可选）
        if tags is not None:
            article.tags = tags if isinstance(tags, list) else [tags]

        storage.upsert_article(article)

        return {
            "success": True,
            "message": f"Updated article {article_id}",
            "category": category_result["category"] if category_result else None,
            "tags": article.tags if article.tags else [],
        }

    elif tool_name == "classify_article":
        article_id = arguments.get("article_id")
        content = arguments.get("content", "")

        if not article_id:
            return {"error": "Missing article_id"}

        article = dao.fetch_article_by_id(article_id)
        if not article:
            return {"error": "Article not found"}

        if not content:
            content = (article.content or "") + " " + (article.title or "")

        result = classify(content)

        article.categories = [result["category"]]
        article.tags = result["tags"]
        storage.upsert_article(article)

        return {
            "success": True,
            "article_id": article_id,
            "category": result["category"],
            "confidence": result["category_confidence"],
            "tags": result["tags"],
        }

    elif tool_name == "list_categories":
        categories = [
            {"name": cat, "keyword_count": len(kw), "sample_keywords": kw[:5]}
            for cat, kw in CATEGORY_RULES.items()
        ]
        return {"success": True, "categories": categories, "default": DEFAULT_CATEGORY}

    else:
        return {"error": f"Unknown tool: {tool_name}"}


@router.get("/articles/needing-processing")
async def get_articles_needing_processing(limit: int = 10):
    """获取需要处理的文章（HTTP 端点）"""
    storage = get_storage_adapter()
    dao = ArticleDAO(storage) if storage else None

    if not dao:
        return {"error": "Storage not configured"}

    articles = dao.fetch_articles(limit=limit)
    result = []
    for a in articles:
        if a.content:
            needs_summary = not a.summary or a.summary == ""
            needs_category = not a.categories or len(a.categories) == 0
            needs_tags = not a.tags or len(a.tags) == 0
            if needs_summary or needs_category or needs_tags:
                result.append(
                    {
                        "id": a.id,
                        "title": a.title,
                        "url": a.url,
                        "source": a.source,
                        "needs_summary": needs_summary,
                        "needs_category": needs_category,
                        "needs_tags": needs_tags,
                        "content_preview": (
                            a.content[:300] + "..."
                            if a.content and len(a.content) > 300
                            else a.content
                        ),
                        "content_length": len(a.content) if a.content else 0,
                    }
                )
            if len(result) >= limit:
                break
    return {"success": True, "count": len(result), "articles": result}


@router.get("/articles/need-summary")
async def get_articles_needing_summary(limit: int = 10):
    storage = get_storage_adapter()
    dao = ArticleDAO(storage) if storage else None

    if not dao:
        return {"error": "Storage not configured"}

    # 查询有内容但没有摘要的文章
    result = storage._execute_sql(
        'SELECT * FROM articles WHERE content IS NOT NULL AND content != "" AND (summary IS NULL OR summary = "") LIMIT ?',
        [limit],
    )
    rows = storage._parse_result(result)

    from shared.models import ArticleModel

    result_articles = []
    for row in rows:
        categories = []
        tags = []
        try:
            import json

            categories = json.loads(row.get("categories", "[]"))
            tags = json.loads(row.get("tags", "[]"))
        except:
            pass

        article = ArticleModel(
            id=row.get("id", ""),
            title=row.get("title", ""),
            content=row.get("content", ""),
            url=row.get("url", ""),
            source=row.get("source", ""),
            categories=categories,
            tags=tags,
            summary=row.get("summary"),
            ingested_at=row.get("ingested_at", ""),
        )
        result_articles.append(
            {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "content_preview": (
                    article.content[:300] + "..."
                    if article.content and len(article.content) > 300
                    else article.content
                ),
                "content_length": len(article.content) if article.content else 0,
            }
        )

    return {"success": True, "count": len(result_articles), "articles": result_articles}


@router.post("/articles/{article_id}/summarize")
async def update_summary(article_id: str, request: ArticleSummaryRequest):
    storage = get_storage_adapter()
    dao = ArticleDAO(storage) if storage else None

    if not dao:
        return {"error": "Storage not configured"}

    article = dao.fetch_article_by_id(article_id)
    if not article:
        return {"error": "Article not found"}

    article.summary = request.summary

    category_result = None
    if request.auto_classify and article.content:
        text = article.content + " " + (article.title or "") + " " + request.summary
        category_result = classify(text)
        article.categories = [category_result["category"]]
        article.tags = category_result["tags"]

    # 手动指定标签（可选）
    if request.tags is not None:
        article.tags = request.tags

    storage.upsert_article(article)

    return {
        "success": True,
        "message": f"Updated article {article_id}",
        "category": category_result["category"] if category_result else None,
        "tags": article.tags if article.tags else [],
    }


@router.get("/categories")
async def list_categories():
    categories = [
        {"name": cat, "keyword_count": len(kw), "sample_keywords": kw[:5]}
        for cat, kw in CATEGORY_RULES.items()
    ]
    return {"success": True, "categories": categories, "default": DEFAULT_CATEGORY}
