"""MCP 工具处理模块"""

import json


class MCPTools:
    """MCP 工具注册和执行"""
    
    def __init__(self, storage):
        self.storage = storage
        self.tools = self._register_tools()
    
    def _register_tools(self):
        """注册所有 MCP 工具"""
        return {
            "get_articles_by_date": self.get_articles_by_date,
            "update_article_summary_and_category": self.update_article_summary_and_category,
            "classify_article": self.classify_article,
            "list_categories": self.list_categories,
            "get_categories": self.get_categories,
            "create_category": self.create_category,
            "update_category": self.update_category,
            "delete_category": self.delete_category,
            "get_tags": self.get_tags,
            "create_tag": self.create_tag,
            "update_tag": self.update_tag,
            "delete_tag": self.delete_tag,
            "get_articles_with_empty_summary": self.get_articles_with_empty_summary,
            "init_default_categories": self.init_default_categories,
        }
    
    def get_tool_names(self):
        """获取所有工具名称"""
        return list(self.tools.keys())
    
    async def execute(self, tool_name, arguments):
        """执行工具"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}
        return await tool(arguments)
    
    async def get_articles_by_date(self, arguments):
        """获取指定日期的文章"""
        date_str = arguments.get("date")
        limit = arguments.get("limit", 20)
        
        if not date_str:
            return {"success": False, "error": "需要指定日期"}
        
        from datetime import datetime, timezone
        target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        filters = {
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat()
        }
        rows = await self.storage.fetch_articles(filters=filters, limit=limit)
        
        articles = []
        for row in rows:
            articles.append({
                "id": row["id"],
                "title": row["title"],
                "url": row["url"],
                "source": row["source"],
                "content": row.get("content", ""),
                "raw_markdown": row.get("raw_markdown", ""),
                "summary": row.get("summary", ""),
                "categories": row.get("categories", []),
                "tags": row.get("tags", []),
                "ingested_at": row["ingested_at"],
                "is_ai_related": bool(row.get("is_ai_related", 0)),
            })
        
        return {"success": True, "date": date_str, "count": len(articles), "articles": articles}
    
    async def update_article_summary_and_category(self, arguments):
        """更新文章摘要和分类"""
        article_id = arguments.get("article_id")
        summary = arguments.get("summary")
        manual_category = arguments.get("category")
        manual_tags = arguments.get("tags")
        auto_classify = arguments.get("auto_classify", True)
        is_ai_related = arguments.get("is_ai_related")
        
        if not article_id or (not summary and is_ai_related is None):
            return {"error": "Missing article_id or summary"}
        
        article = await self.storage.fetch_article_by_id(article_id)
        if not article:
            return {"error": "Article not found"}
        
        article["summary"] = summary
        
        if is_ai_related is not None:
            article["is_ai_related"] = is_ai_related
        
        if manual_category:
            article["categories"] = [manual_category]
        
        if manual_tags:
            article["tags"] = manual_tags
        
        # TODO: 实现实际更新逻辑
        return {"success": True, "message": f"Updated article {article_id}"}
    
    async def classify_article(self, arguments):
        """分类文章"""
        text = arguments.get("text", "")
        
        # 获取分类规则
        db_category_rules, db_tag_rules = await self._get_db_rules()
        
        if db_category_rules:
            result = classify_text(text, db_category_rules, db_tag_rules)
        else:
            result = classify_text(text, {}, {})
        
        return {"success": True, **result}
    
    async def list_categories(self, arguments):
        """列出所有分类"""
        categories = await self.storage.get_all_categories()
        return {"success": True, "categories": categories}
    
    async def get_categories(self, arguments):
        """获取分类（同 list_categories）"""
        return await self.list_categories(arguments)
    
    async def create_category(self, arguments):
        """创建分类"""
        name = arguments.get("name")
        keywords = arguments.get("keywords", [])
        
        if not name:
            return {"success": False, "error": "Missing name"}
        
        result = await self.storage.create_category(name, keywords)
        return {"success": True, "category": result}
    
    async def update_category(self, arguments):
        """更新分类"""
        category_id = arguments.get("category_id")
        name = arguments.get("name")
        keywords = arguments.get("keywords", [])
        
        result = await self.storage.update_category(category_id, name, keywords)
        return {"success": True}
    
    async def delete_category(self, arguments):
        """删除分类"""
        category_id = arguments.get("category_id")
        
        result = await self.storage.delete_category(category_id)
        return {"success": True, "message": f"Deleted category: {category_id}"}
    
    async def get_tags(self, arguments):
        """获取所有标签"""
        tags = await self.storage.get_all_tags()
        return {"success": True, "tags": tags}
    
    async def create_tag(self, arguments):
        """创建标签"""
        name = arguments.get("name")
        keywords = arguments.get("keywords", [])
        
        result = await self.storage.create_tag(name, keywords)
        return {"success": True, "tag": result}
    
    async def update_tag(self, arguments):
        """更新标签"""
        tag_id = arguments.get("tag_id")
        name = arguments.get("name")
        keywords = arguments.get("keywords", [])
        
        result = await self.storage.update_tag(tag_id, name, keywords)
        return {"success": True}
    
    async def delete_tag(self, arguments):
        """删除标签"""
        tag_id = arguments.get("tag_id")
        
        result = await self.storage.delete_tag(tag_id)
        return {"success": True, "message": f"Deleted tag: {tag_id}"}
    
    async def get_articles_with_empty_summary(self, arguments):
        """获取没有摘要的文章"""
        limit = arguments.get("limit", 150)
        
        sql = "SELECT * FROM articles WHERE summary IS NULL OR summary = '' LIMIT ?"
        result = await self.storage._execute_sql(sql, [limit])
        
        articles = []
        if result.get("success"):
            for row in result.get("results", []):
                articles.append(self.storage._row_to_dict(row))
        
        return {"success": True, "count": len(articles), "articles": articles}
    
    async def init_default_categories(self, arguments):
        """初始化默认分类"""
        # 默认分类
        default_categories = [
            {"name": "大厂", "keywords": ["阿里", "腾讯", "百度", "字节", "华为", "小米"]},
            {"name": "人物", "keywords": ["马斯克", "黄仁勋", " Sam Altman", "山姆·奥特曼"]},
            {"name": "产品", "keywords": ["发布", "新品", "产品", "上市"]},
            {"name": "技术", "keywords": ["芯片", "模型", "算法", "论文", "研究"]},
            {"name": "投资", "keywords": ["融资", "投资", "收购", "估值"]},
            {"name": "安全", "keywords": ["漏洞", "攻击", "隐私", "安全"]},
            {"name": "其他", "keywords": []},
        ]
        
        for cat in default_categories:
            await self.storage.create_category(cat["name"], cat.get("keywords", []))
        
        return {"success": True, "message": "Default categories initialized"}
    
    async def _get_db_rules(self):
        """获取数据库中的分类规则"""
        # TODO: 实现
        return {}, {}


def classify_text(text, category_rules=None, tag_rules=None):
    """简单的文本分类函数"""
    if category_rules is None:
        category_rules = {}
    if tag_rules is None:
        tag_rules = {}
    
    text_lower = text.lower()
    
    # 简单关键词匹配
    for cat_name, keywords in category_rules.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return {"category": cat_name, "tags": [], "scores": {cat_name: 1.0}}
    
    return {"category": "其他", "tags": [], "scores": {}}
