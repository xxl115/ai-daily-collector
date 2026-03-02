"""
Cloudflare Workers Python 入口文件 - v2.2 DEBUG
"""

from workers import WorkerEntrypoint
from js import Response
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# 版本号用于强制刷新
VERSION = "2.2.0"


class Default(WorkerEntrypoint):
    """Cloudflare Python Workers 默认入口类"""

    async def on_fetch(self, request, env, ctx):
        """处理所有 HTTP 请求的主入口"""
        try:
            url_str = str(request.url)
            parsed_url = urlparse(url_str)
            path = parsed_url.path
            method = request.method

            # 获取 D1 数据库绑定 - 使用 self.env 而不是参数 env
            db = None
            db_error = None
            env_info = {}

            # 在 Python Workers 中，绑定通过 self.env 访问
            try:
                worker_env = self.env
                env_info = {
                    "env_type": str(type(worker_env)),
                    "has_DB": hasattr(worker_env, "DB"),
                }

                if hasattr(worker_env, "DB"):
                    db = worker_env.DB
                    if db is None:
                        db_error = "self.env.DB is None"
                else:
                    db_error = "self.env has no DB attribute"
            except Exception as e:
                db_error = f"Error accessing self.env.DB: {str(e)}"

            # 初始化存储适配器
            storage = WorkersD1StorageAdapter(db) if db else None

            # 初始化配置表（如果不存在）
            if storage:
                try:
                    await storage.init_config_tables()
                except Exception as e:
                    pass  # 表可能已存在

            # 健康检查端点 - 显示数据库连接状态
            if path == "/" or path == "/health":
                return await self._health_response(storage, db_error, env_info)

            # API 端点
            if path == "/api/v2/articles":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._articles_response(parsed_url, storage)

            elif path.startswith("/api/v2/articles/"):
                if method != "GET":
                    return self._method_not_allowed()
                return await self._article_detail_response(path, storage)

            elif path == "/api/v2/stats":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._stats_response(storage)

            elif path == "/api/v2/sources":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._sources_response(storage)

            elif path == "/api/v2/crawl-logs":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._crawl_logs_response(parsed_url, storage)

            elif path == "/api/v2/crawl-stats":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._crawl_stats_response(storage)

            # MCP 端点
            elif path == "/mcp" or path == "/api/mcp":
                if method == "POST":
                    return await self._mcp_request(request, storage)
                elif method == "GET":
                    return self._mcp_info()

            # MCP 工具列表
            elif path == "/mcp/tools" or path == "/api/mcp/tools":
                return self._mcp_tools_list()

            else:
                return self._json_response({"error": "Not found"}, status=404)

        except Exception as e:
            return self._json_response(
                {"error": "Internal server error", "message": str(e)}, status=500
            )

    async def _health_response(self, storage, db_error=None, env_info=None):
        """健康检查响应 - 显示数据库连接状态"""
        db_connected = storage is not None
        db_count = 0
        db_details = {}

        if storage:
            try:
                stats = await storage.get_stats()
                if isinstance(stats, dict):
                    db_count = stats.get("total", 0)
                    db_details = {
                        "sources": stats.get("sources", {}),
                        "tables": await storage._list_tables(),
                    }
                else:
                    db_count = f"ERROR: stats is not dict, type={type(stats)}"
            except Exception as e:
                db_count = f"ERROR: {type(e).__name__}: {str(e)}"

        response = {
            "status": "healthy",
            "version": VERSION,
            "database": {
                "connected": db_connected,
                "article_count": db_count,
                "error": db_error,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if db_details:
            response["database_details"] = db_details

        if env_info:
            response["env_info"] = env_info

        return self._json_response(response)

    async def _articles_response(self, parsed_url, storage):
        """文章列表响应 - 返回空列表当没有数据"""
        if not storage:
            return self._json_response(
                {
                    "total": 0,
                    "articles": [],
                    "page": 1,
                    "page_size": 20,
                    "message": "Database configured but no data yet",
                }
            )

        try:
            query_params = parse_qs(parsed_url.query)
            source = query_params.get("source", [None])[0]
            page = int(query_params.get("page", ["1"])[0])
            page_size = min(int(query_params.get("page_size", ["20"])[0]), 100)

            filters = {}
            if source:
                filters["source"] = source

            offset = (page - 1) * page_size
            articles = await storage.fetch_articles(filters=filters, limit=page_size, offset=offset)
            stats = await storage.get_stats()

            return self._json_response(
                {
                    "total": stats.get("total", len(articles)),
                    "articles": articles,
                    "page": page,
                    "page_size": page_size,
                }
            )
        except Exception as e:
            return self._json_response({"error": str(e), "total": 0, "articles": []}, status=500)

    async def _article_detail_response(self, path, storage):
        """单篇文章详情响应"""
        if not storage:
            return self._json_response({"error": "Database not configured"}, status=500)

        try:
            article_id = path.split("/")[-1]
            article = await storage.fetch_article_by_id(article_id)

            if not article:
                return self._json_response({"error": "Article not found"}, status=404)

            return self._json_response(article)
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _stats_response(self, storage):
        """统计信息响应"""
        if not storage:
            return self._json_response(
                {"total_articles": 0, "sources": [], "message": "No data yet"}
            )

        try:
            stats = await storage.get_stats()
            return self._json_response(
                {
                    "total_articles": stats.get("total", 0),
                    "sources": [
                        {"source": k, "count": v} for k, v in stats.get("sources", {}).items()
                    ],
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                }
            )
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _sources_response(self, storage):
        """数据源列表响应"""
        if not storage:
            return self._json_response([])

        try:
            stats = await storage.get_stats()
            return self._json_response(list(stats.get("sources", {}).keys()))
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _crawl_logs_response(self, parsed_url, storage):
        """抓取日志响应"""
        if not storage:
            return self._json_response({"total": 0, "logs": [], "page": 1, "page_size": 20})

        try:
            query_params = parse_qs(parsed_url.query)
            page = int(query_params.get("page", ["1"])[0])
            page_size = min(int(query_params.get("page_size", ["20"])[0]), 100)

            offset = (page - 1) * page_size
            logs = await storage.get_crawl_logs(limit=page_size, offset=offset)

            return self._json_response(
                {"total": len(logs), "logs": logs, "page": page, "page_size": page_size}
            )
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _crawl_stats_response(self, storage):
        """抓取统计响应"""
        if not storage:
            return self._json_response(
                {
                    "total_crawls": 0,
                    "status_counts": {},
                    "total_articles_captured": 0,
                    "avg_duration_ms": 0,
                }
            )

        try:
            stats = await storage.get_crawl_stats()
            return self._json_response(stats)
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    def _json_response(self, data, status=200):
        """创建 JSON 响应"""
        return Response.new(
            json.dumps(data, ensure_ascii=False, default=str),
            {"status": status, "headers": {"Content-Type": "application/json"}},
        )

    def _method_not_allowed(self):
        """405 Method Not Allowed"""
        return self._json_response({"error": "Method not allowed"}, status=405)

    # ============================================================
    # MCP 端点方法
    # ============================================================

    def _mcp_info(self):
        """返回 MCP 服务器信息"""
        return self._json_response(
            {
                "name": "D1 MCP Tools",
                "version": "1.0.0",
                "description": "AI Daily Collector D1 Tools for article summary and classification",
            }
        )

    def _mcp_tools_list(self):
        """列出可用工具"""
        tools = [
            {
                "name": "get_articles_needing_processing",
                "description": "获取需要处理的文章列表（需要总结、分类或标签），返回详细的处理状态",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "返回文章数量，默认10",
                        }
                    },
                },
            },
            {
                "name": "update_article_summary_and_category",
                "description": "更新文章摘要并自动分类，或手动指定分类和标签",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "article_id": {"type": "string", "description": "文章ID"},
                        "summary": {"type": "string", "description": "摘要内容"},
                        "category": {
                            "type": "string",
                            "description": "手动指定分类（如'大厂/人物'），优先级高于自动分类",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "手动指定标签数组（如['LLM', '中国']）",
                        },
                        "auto_classify": {
                            "type": "boolean",
                            "description": "当未指定category时是否自动分类，默认true",
                        },
                    },
                    "required": ["article_id", "summary"],
                },
            },
            {
                "name": "classify_article",
                "description": "对文章进行自动分类（基于关键词规则）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "article_id": {"type": "string", "description": "文章ID"},
                        "content": {
                            "type": "string",
                            "description": "文章内容（可选）",
                        },
                    },
                    "required": ["article_id"],
                },
            },
            {"name": "list_categories", "description": "列出所有分类规则"},
            # 分类管理
            {
                "name": "get_categories",
                "description": "获取所有分类（从数据库）",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "create_category",
                "description": "创建新分类",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "分类名称"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词数组",
                        },
                    },
                    "required": ["name", "keywords"],
                },
            },
            {
                "name": "update_category",
                "description": "更新分类",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number", "description": "分类ID"},
                        "name": {"type": "string", "description": "分类名称"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词数组",
                        },
                    },
                    "required": ["id", "name", "keywords"],
                },
            },
            {
                "name": "delete_category",
                "description": "删除分类",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number", "description": "分类ID"},
                    },
                    "required": ["id"],
                },
            },
            # 标签管理
            {
                "name": "get_tags",
                "description": "获取所有标签（从数据库）",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "create_tag",
                "description": "创建新标签",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "标签名称"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词数组",
                        },
                    },
                    "required": ["name", "keywords"],
                },
            },
            {
                "name": "update_tag",
                "description": "更新标签",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number", "description": "标签ID"},
                        "name": {"type": "string", "description": "标签名称"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词数组",
                        },
                    },
                    "required": ["id", "name", "keywords"],
                },
            },
            {
                "name": "delete_tag",
                "description": "删除标签",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number", "description": "标签ID"},
                    },
                    "required": ["id"],
                },
            },
            {
                "name": "init_default_categories",
                "description": "初始化默认分类和标签数据",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_articles_with_empty_summary",
                "description": "查询所有 summary 为空的文章（包括没有 content 的文章）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "number", "description": "返回文章数量，默认10"},
                    },
                },
            },
        ]

        return self._json_response({"tools": tools})

    async def _mcp_request(self, request, storage):
        """处理 MCP 请求"""
        try:
            body = await request.json()

            tool_name = body.get("tool")
            arguments = body.get("arguments", {})

            if not tool_name:
                return self._json_response({"error": "Missing 'tool' parameter"}, status=400)

            # 执行工具
            result = await self._execute_mcp_tool(tool_name, arguments, storage)

            return self._json_response(result)

        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _execute_mcp_tool(self, tool_name, arguments, storage):
        """执行 MCP 工具"""

        # 分类规则
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
                "语音合成",
                "TTS",
                "ElevenLabs",
                "音乐生成",
                "Suno",
                "多模态",
                "图像生成",
                "AI绘画",
                "文生视频",
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
                "开源",
                "框架",
            ],
            "安全风险": [
                "安全",
                "漏洞",
                "攻击",
                "恶意",
                "病毒",
                "隐私",
                "数据泄露",
                "监管",
                "Deepfake",
                "幻觉",
                "越狱",
                "黑客",
            ],
            "算力基建": [
                "GPU",
                "TPU",
                "芯片",
                "算力",
                "智算中心",
                "训练",
                "推理",
                "部署",
                "一体机",
                "服务器",
                "云计算",
            ],
            "商业应用": [
                "电商",
                "购物",
                "金融",
                "银行",
                "医疗",
                "教育",
                "企业",
                "融资",
            ],
        }

        TAG_RULES = {
            "LLM": ["大模型", "语言模型", "LLM", "GPT", "Claude"],
            "多模态": ["多模态", "视觉", "图像", "视频", "音频"],
            "开源": ["开源", "Open Source", "Apache", "MIT", "GitHub"],
            "发布": ["发布", "上线", "更新", "版本", "新功能"],
            "研究": ["论文", "arXiv", "研究", "实验", "学术"],
            "中国": ["中国", "国产", "本土", "国内"],
        }

        DEFAULT_CATEGORY = "其他"

        async def get_db_rules():
            """从数据库获取分类规则"""
            if storage:
                return await storage.get_classification_rules()
            return None, None

        def classify(text, category_rules=None, tag_rules=None):
            """分类函数 - 可选使用数据库规则或默认规则"""
            if not text:
                return {"category": DEFAULT_CATEGORY, "tags": [], "scores": {}}

            # 使用传入的规则或默认规则
            rules = category_rules if category_rules else CATEGORY_RULES
            tags_rules = tag_rules if tag_rules else TAG_RULES

            text_lower = text.lower()
            scores = {}

            for category, keywords in rules.items():
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
            for tag, keywords in tags_rules.items():
                if any(kw.lower() in text_lower for kw in keywords):
                    tags.append(tag)

            return {
                "category": category,
                "category_confidence": round(confidence, 2),
                "tags": tags[:5],
            }

        # 执行对应的工具
        if tool_name == "get_articles_needing_processing":
            # 统一获取需要处理的文章（需要总结、分类或标签）
            limit = arguments.get("limit", 10)
            articles = []
            rows = await storage.fetch_articles(limit=100) if storage else []

            for row in rows:
                if row.get("content"):
                    # 检查是否需要处理
                    needs_summary = not row.get("summary") or row.get("summary") == ""
                    needs_category = not row.get("categories") or not row.get("categories")
                    needs_tags = not row.get("tags") or not row.get("tags")

                    # 只返回需要处理的文章
                    if needs_summary or needs_category or needs_tags:
                        articles.append(
                            {
                                "id": row["id"],
                                "title": row["title"],
                                "url": row["url"],
                                "source": row["source"],
                                "needs_summary": needs_summary,
                                "needs_category": needs_category,
                                "needs_tags": needs_tags,
                                "content_preview": (
                                    row["content"][:300] + "..."
                                    if len(row["content"]) > 300
                                    else row["content"]
                                ),
                                "content_length": len(row["content"]) if row["content"] else 0,
                                "ingested_at": row["ingested_at"],
                            }
                        )
                    if len(articles) >= limit:
                        break

            return {"success": True, "count": len(articles), "articles": articles}

        elif tool_name == "update_article_summary_and_category":
            article_id = arguments.get("article_id")
            summary = arguments.get("summary")
            manual_category = arguments.get("category")  # 手动指定的分类
            manual_tags = arguments.get("tags")  # 手动指定的标签
            auto_classify = arguments.get("auto_classify", True)

            if not article_id or not summary:
                return {"error": "Missing article_id or summary"}

            article = await storage.fetch_article_by_id(article_id) if storage else None
            if not article:
                return {"error": "Article not found"}

            # article is a dict, update fields
            article["summary"] = summary

            # 处理分类和标签
            category_result = None
            if manual_category:
                # 手动指定分类
                article["categories"] = [manual_category]
            elif auto_classify and article.get("content"):
                # 自动分类 - 优先使用数据库规则
                db_category_rules, db_tag_rules = await get_db_rules()
                if db_category_rules:
                    # 使用数据库规则
                    category_result = classify(
                        article.get("content", "") + " " + summary,
                        db_category_rules,
                        db_tag_rules,
                    )
                else:
                    # 回退到默认规则
                    category_result = classify(article.get("content", "") + " " + summary)
                article["categories"] = [category_result["category"]]

            if manual_tags:
                # 手动指定标签
                article["tags"] = manual_tags
            elif category_result:
                # 使用自动分类的标签
                article["tags"] = category_result["tags"]

            await storage.upsert_article(article)

            return {
                "success": True,
                "message": f"Updated article {article_id}",
                "category": article["categories"][0] if article.get("categories") else None,
                "tags": article.get("tags", []),
            }

        elif tool_name == "classify_article":
            article_id = arguments.get("article_id")
            content = arguments.get("content", "")

            if not article_id:
                return {"error": "Missing article_id"}

            article = await storage.fetch_article_by_id(article_id) if storage else None
            if not article:
                return {"error": "Article not found"}

            # 如果没有传入 content，从文章获取
            if not content:
                content = (
                    (article.get("content", "") or "") + " " + (article.get("title", "") or "")
                )

            result = classify(content)

            # 更新数据库
            article["categories"] = [result["category"]]
            article["tags"] = result["tags"]
            await storage.upsert_article(article)

            return {
                "success": True,
                "article_id": article_id,
                "category": result["category"],
                "confidence": result["category_confidence"],
                "tags": result["tags"],
            }

        elif tool_name == "list_categories":
            categories = []
            for cat, keywords in CATEGORY_RULES.items():
                categories.append(
                    {
                        "name": cat,
                        "keyword_count": len(keywords),
                        "sample_keywords": keywords[:5],
                    }
                )
            return {
                "success": True,
                "categories": categories,
                "default": DEFAULT_CATEGORY,
            }

        # ========== 分类管理 ==========
        elif tool_name == "get_categories":
            categories = await storage.get_all_categories() if storage else []
            return {"success": True, "categories": categories}

        elif tool_name == "create_category":
            name = arguments.get("name")
            keywords = arguments.get("keywords", [])
            if not name:
                return {"error": "Missing name"}
            result = await storage.create_category(name, keywords) if storage else None
            return {"success": True, "message": f"Created category: {name}"}

        elif tool_name == "update_category":
            category_id = arguments.get("id")
            name = arguments.get("name")
            keywords = arguments.get("keywords", [])
            if not category_id or not name:
                return {"error": "Missing id or name"}
            result = await storage.update_category(category_id, name, keywords) if storage else None
            return {"success": True, "message": f"Updated category: {name}"}

        elif tool_name == "delete_category":
            category_id = arguments.get("id")
            if not category_id:
                return {"error": "Missing id"}
            result = await storage.delete_category(category_id) if storage else None
            return {"success": True, "message": f"Deleted category: {category_id}"}

        # ========== 标签管理 ==========
        elif tool_name == "get_tags":
            tags = await storage.get_all_tags() if storage else []
            return {"success": True, "tags": tags}

        elif tool_name == "create_tag":
            name = arguments.get("name")
            keywords = arguments.get("keywords", [])
            if not name:
                return {"error": "Missing name"}
            result = await storage.create_tag(name, keywords) if storage else None
            return {"success": True, "message": f"Created tag: {name}"}

        elif tool_name == "update_tag":
            tag_id = arguments.get("id")
            name = arguments.get("name")
            keywords = arguments.get("keywords", [])
            if not tag_id or not name:
                return {"error": "Missing id or name"}
            result = await storage.update_tag(tag_id, name, keywords) if storage else None
            return {"success": True, "message": f"Updated tag: {name}"}

        elif tool_name == "delete_tag":
            tag_id = arguments.get("id")
            if not tag_id:
                return {"error": "Missing id"}
            result = await storage.delete_tag(tag_id) if storage else None
            return {"success": True, "message": f"Deleted tag: {tag_id}"}

        elif tool_name == "get_articles_with_empty_summary":
            # 直接查询所有 summary 为空的文章（不限制必须有 content）
            limit = arguments.get("limit", 10)
            articles = []

            # 使用 SQL 直接查询
            if storage:
                sql = "SELECT * FROM articles WHERE summary IS NULL OR summary = '' LIMIT ?"
                result = await storage._execute_sql(sql, [limit])

                if result.get("success"):
                    for row in result.get("results", []):
                        articles.append(storage._row_to_dict(row))

            return {"success": True, "count": len(articles), "articles": articles}

        elif tool_name == "init_default_categories":
            # 初始化默认分类和标签
            default_categories = [
                (
                    "大厂/人物",
                    [
                        "OpenAI",
                        "Anthropic",
                        "Google",
                        "Meta",
                        "微软",
                        "英伟达",
                        "马斯克",
                        "GPT",
                        "Claude",
                        "Llama",
                    ],
                ),
                (
                    "Agent工作流",
                    ["Agent", "MCP", "A2A", "Autogen", "CrewAI", "LangChain", "工作流"],
                ),
                (
                    "编程助手",
                    ["Cursor", "Windsurf", "Cline", "GitHub Copilot", "Devin", "IDE"],
                ),
                (
                    "内容生成",
                    ["Midjourney", "DALL-E", "Sora", "视频生成", "Suno", "多模态"],
                ),
                (
                    "工具生态",
                    ["LangChain", "LlamaIndex", "Hugging Face", "PyTorch", "Ollama"],
                ),
                ("安全风险", ["安全", "漏洞", "攻击", "隐私", "Deepfake"]),
                ("算力基建", ["GPU", "芯片", "算力", "训练", "A100", "H100"]),
                ("商业应用", ["电商", "金融", "医疗", "营销", "融资", "财报"]),
            ]
            default_tags = [
                ("LLM", ["大模型", "语言模型", "GPT", "Claude"]),
                ("编程", ["编程", "代码", "开发"]),
                ("多模态", ["视觉", "图像", "视频", "音频"]),
                ("开源", ["开源", "Open Source"]),
                ("发布", ["发布", "上线", "新功能"]),
                ("研究", ["论文", "arXiv", "学术"]),
                ("融资", ["融资", "投资", "估值"]),
                ("中国", ["中国", "国产"]),
            ]

            created = 0
            for name, keywords in default_categories:
                try:
                    await storage.create_category(name, keywords)
                    created += 1
                except:
                    pass  # 可能已存在

            for name, keywords in default_tags:
                try:
                    await storage.create_tag(name, keywords)
                    created += 1
                except:
                    pass  # 可能已存在

            return {
                "success": True,
                "message": f"Initialized {created} categories/tags",
            }

        else:
            return {"error": f"Unknown tool: {tool_name}"}


class WorkersD1StorageAdapter:
    """适配 Cloudflare Workers D1 绑定的存储适配器"""

    def __init__(self, d1_binding):
        self.db = d1_binding

    async def _execute_sql(self, sql, params=None):
        """通过 Workers D1 绑定执行 SQL（异步）"""
        try:
            stmt = self.db.prepare(sql)
            if params:
                stmt = stmt.bind(*params)
            result = await stmt.all()

            # D1 API 返回的结果格式处理
            results = []
            if hasattr(result, "results"):
                results = list(result.results)
            elif isinstance(result, list):
                results = result
            elif hasattr(result, "__iter__"):
                results = list(result)

            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "errors": [{"message": str(e)}], "sql": sql}

    async def init_config_tables(self):
        """初始化配置表（categories 和 tags）"""
        # 创建 categories 表
        create_categories_sql = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            keywords TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        await self._execute_sql(create_categories_sql)

        # 创建 tags 表
        create_tags_sql = """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            keywords TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        await self._execute_sql(create_tags_sql)

    # ========== Categories CRUD ==========
    async def get_all_categories(self):
        """获取所有分类"""
        sql = "SELECT * FROM categories ORDER BY id"
        result = await self._execute_sql(sql)
        categories = []
        if result.get("success"):
            import json

            for row in result.get("results", []):
                # Handle both dict and object types
                if isinstance(row, dict):
                    categories.append(
                        {
                            "id": row.get("id"),
                            "name": row.get("name"),
                            "keywords": (
                                json.loads(row.get("keywords", "[]")) if row.get("keywords") else []
                            ),
                        }
                    )
                else:
                    # Handle object type from D1
                    categories.append(
                        {
                            "id": getattr(row, "id", None),
                            "name": getattr(row, "name", ""),
                            "keywords": (
                                json.loads(getattr(row, "keywords", "[]"))
                                if getattr(row, "keywords", None)
                                else []
                            ),
                        }
                    )
        return categories

    async def create_category(self, name, keywords):
        """创建分类"""
        import json

        sql = "INSERT INTO categories (name, keywords) VALUES (?, ?)"
        return await self._execute_sql(sql, [name, json.dumps(keywords)])

    async def update_category(self, category_id, name, keywords):
        """更新分类"""
        import json

        sql = "UPDATE categories SET name = ?, keywords = ? WHERE id = ?"
        return await self._execute_sql(sql, [name, json.dumps(keywords), category_id])

    async def delete_category(self, category_id):
        """删除分类"""
        sql = "DELETE FROM categories WHERE id = ?"
        return await self._execute_sql(sql, [category_id])

    # ========== Tags CRUD ==========
    async def get_all_tags(self):
        """获取所有标签"""
        sql = "SELECT * FROM tags ORDER BY id"
        result = await self._execute_sql(sql)
        tags = []
        if result.get("success"):
            import json

            for row in result.get("results", []):
                # Handle both dict and object types
                if isinstance(row, dict):
                    tags.append(
                        {
                            "id": row.get("id"),
                            "name": row.get("name"),
                            "keywords": (
                                json.loads(row.get("keywords", "[]")) if row.get("keywords") else []
                            ),
                        }
                    )
                else:
                    # Handle object type from D1
                    tags.append(
                        {
                            "id": getattr(row, "id", None),
                            "name": getattr(row, "name", ""),
                            "keywords": (
                                json.loads(getattr(row, "keywords", "[]"))
                                if getattr(row, "keywords", None)
                                else []
                            ),
                        }
                    )
        return tags

    async def create_tag(self, name, keywords):
        """创建标签"""
        import json

        sql = "INSERT INTO tags (name, keywords) VALUES (?, ?)"
        return await self._execute_sql(sql, [name, json.dumps(keywords)])

    async def update_tag(self, tag_id, name, keywords):
        """更新标签"""
        import json

        sql = "UPDATE tags SET name = ?, keywords = ? WHERE id = ?"
        return await self._execute_sql(sql, [name, json.dumps(keywords), tag_id])

    async def delete_tag(self, tag_id):
        """删除标签"""
        sql = "DELETE FROM tags WHERE id = ?"
        return await self._execute_sql(sql, [tag_id])

    async def get_classification_rules(self):
        """获取分类规则（供 classify 函数使用）"""
        categories = await self.get_all_categories()
        tags = await self.get_all_tags()

        category_rules = {}
        for cat in categories:
            category_rules[cat["name"]] = cat.get("keywords", [])

        tag_rules = {}
        for tag in tags:
            tag_rules[tag["name"]] = tag.get("keywords", [])

        return category_rules, tag_rules

    async def fetch_articles(self, filters=None, limit=50, offset=0):
        """Fetch articles with optional filtering"""
        filters = filters or {}

        sql = "SELECT * FROM articles WHERE 1=1"
        params = []

        if "source" in filters:
            sql += " AND source = ?"
            params.append(filters["source"])

        if "id" in filters:
            sql += " AND id = ?"
            params.append(filters["id"])

        sql += " ORDER BY ingested_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        result = await self._execute_sql(sql, params)

        articles = []
        if result.get("success"):
            for row in result.get("results", []):
                articles.append(self._row_to_dict(row))

        return articles

    async def fetch_article_by_id(self, article_id):
        """Get a single article by ID"""
        sql = "SELECT * FROM articles WHERE id = ? LIMIT 1"
        result = await self._execute_sql(sql, [article_id])

        if result.get("success") and result.get("results"):
            return self._row_to_dict(result["results"][0])

        return None

    async def upsert_article(self, article):
        """Insert or update an article (accepts dict)"""
        if not article:
            return {"success": False, "error": "No article data"}

        article_id = article.get("id")
        if not article_id:
            return {"success": False, "error": "No article ID"}

        import json

        # Helper to convert None to empty string for D1
        def val(v):
            return v if v is not None else ""

        # First try UPDATE
        sql = """
            UPDATE articles SET
                title = ?, content = ?, url = ?, published_at = ?,
                source = ?, categories = ?, tags = ?, summary = ?, ingested_at = ?
            WHERE id = ?
        """

        params = [
            val(article.get("title")),
            val(article.get("content")),
            val(article.get("url")),
            val(article.get("published_at")),
            val(article.get("source")),
            json.dumps(article.get("categories", [])),
            json.dumps(article.get("tags", [])),
            val(article.get("summary")),
            val(article.get("ingested_at")),
            article_id,
        ]

        result = await self._execute_sql(sql, params)

        # If update succeeded, check if any row was actually updated
        if result.get("success"):
            check_sql = "SELECT id FROM articles WHERE id = ?"
            check_result = await self._execute_sql(check_sql, [article_id])

            if not check_result.get("results"):
                # No existing row, do INSERT
                insert_sql = """
                    INSERT INTO articles (id, title, content, url, published_at, source, categories, tags, summary, ingested_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                insert_params = [
                    article_id,
                    val(article.get("title")),
                    val(article.get("content")),
                    val(article.get("url")),
                    val(article.get("published_at")),
                    val(article.get("source")),
                    json.dumps(article.get("categories", [])),
                    json.dumps(article.get("tags", [])),
                    val(article.get("summary")),
                    val(article.get("ingested_at")),
                ]
                return await self._execute_sql(insert_sql, insert_params)

        return result

    async def get_stats(self):
        """Get database statistics"""
        try:
            # Get total count
            count_result = await self._execute_sql("SELECT COUNT(*) as total FROM articles")
            total = 0
            if count_result.get("success") and count_result.get("results"):
                row = count_result["results"][0]
                if isinstance(row, dict):
                    total = row.get("total", 0)
                else:
                    total = getattr(row, "total", None) or getattr(row, "COUNT(*)", 0) or 0

            # Get sources breakdown
            sources_result = await self._execute_sql(
                "SELECT source, COUNT(*) as count FROM articles GROUP BY source"
            )
            sources = {}
            if sources_result.get("success"):
                for row in sources_result.get("results", []):
                    if isinstance(row, dict):
                        sources[row.get("source", "unknown")] = row.get("count", 0)
                    else:
                        source = getattr(row, "source", "unknown")
                        count = getattr(row, "count", 0) or getattr(row, "COUNT(*)", 0)
                        sources[source] = count

            return {"total": total, "sources": sources}
        except Exception as e:
            return {"total": 0, "sources": {}, "error": f"Stats error: {str(e)}"}

    async def _list_tables(self):
        """List all tables in the database"""
        try:
            result = await self._execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
            if result.get("success"):
                return [row.get("name") for row in result.get("results", [])]
            return []
        except Exception as e:
            return [f"Error listing tables: {str(e)}"]

    def _row_to_dict(self, row):
        """Convert database row to dict"""

        # Handle object-type rows (not just dict)
        def get_value(field, default=""):
            if isinstance(row, dict):
                return row.get(field, default)
            else:
                return getattr(row, field, default)

        categories = []
        tags = []

        cat_value = get_value("categories")
        if cat_value:
            try:
                categories = json.loads(cat_value)
            except:
                categories = []

        tag_value = get_value("tags")
        if tag_value:
            try:
                tags = json.loads(tag_value)
            except:
                tags = []

        return {
            "id": str(get_value("id", "")),
            "title": str(get_value("title", "")),
            "content": str(get_value("content", "")),
            "url": str(get_value("url", "")),
            "published_at": str(get_value("published_at")) if get_value("published_at") else None,
            "source": str(get_value("source", "")),
            "categories": categories,
            "tags": tags,
            "summary": str(get_value("summary", "")),
            "ingested_at": str(get_value("ingested_at", "")),
        }

    async def get_crawl_logs(self, limit=50, offset=0):
        """获取抓取日志"""
        try:
            sql = "SELECT * FROM crawl_logs ORDER BY crawled_at DESC LIMIT ? OFFSET ?"
            result = await self._execute_sql(sql, [limit, offset])

            logs = []
            if result.get("success"):
                for row in result.get("results", []):
                    logs.append(self._crawl_log_to_dict(row))

            return logs
        except Exception as e:
            return []

    async def get_crawl_stats(self):
        """获取抓取统计"""
        try:
            # Total crawls
            total_result = await self._execute_sql("SELECT COUNT(*) as total FROM crawl_logs")
            total = 0
            if total_result.get("success") and total_result.get("results"):
                total = total_result["results"][0].get("total", 0) or 0

            # Status breakdown
            status_result = await self._execute_sql(
                "SELECT status, COUNT(*) as count FROM crawl_logs GROUP BY status"
            )
            status_counts = {}
            if status_result.get("success"):
                for row in status_result.get("results", []):
                    status_counts[row.get("status", "")] = row.get("count", 0)

            # Total articles
            articles_result = await self._execute_sql(
                "SELECT SUM(articles_count) as total FROM crawl_logs WHERE status = 'success'"
            )
            total_articles = 0
            if articles_result.get("success") and articles_result.get("results"):
                total_articles = articles_result["results"][0].get("total", 0) or 0

            # Average duration
            avg_result = await self._execute_sql(
                "SELECT AVG(duration_ms) as avg_duration FROM crawl_logs WHERE status = 'success'"
            )
            avg_duration = 0
            if avg_result.get("success") and avg_result.get("results"):
                avg_duration = int(avg_result["results"][0].get("avg_duration", 0) or 0)

            return {
                "total_crawls": total,
                "status_counts": status_counts,
                "total_articles_captured": total_articles,
                "avg_duration_ms": avg_duration,
            }
        except Exception as e:
            return {
                "total_crawls": 0,
                "status_counts": {},
                "total_articles_captured": 0,
                "avg_duration_ms": 0,
            }

    def _crawl_log_to_dict(self, row):
        """将抓取日志行转换为字典"""

        def get_value(field, default=""):
            if isinstance(row, dict):
                return row.get(field, default)
            else:
                return getattr(row, field, default)

        return {
            "id": get_value("id", 0),
            "source_name": get_value("source_name", ""),
            "source_type": get_value("source_type", ""),
            "articles_count": get_value("articles_count", 0),
            "duration_ms": get_value("duration_ms", 0),
            "status": get_value("status", ""),
            "error_message": get_value("error_message"),
            "crawled_at": get_value("crawled_at", ""),
        }
