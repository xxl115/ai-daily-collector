"""API 端点处理模块"""

from urllib.parse import urlparse, parse_qs


class APIHandlers:
    """API 端点处理器"""
    
    def __init__(self, storage):
        self.storage = storage
    
    async def handle_health(self, db_error=None, env_info=None):
        """健康检查端点"""
        from datetime import datetime
        data = {
            "status": "healthy" if self.storage else "unhealthy",
            "version": "2.2.1",
            "database": {
                "connected": self.storage is not None,
                "article_count": await self._get_article_count() if self.storage else 0,
                "error": db_error
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if env_info:
            data["database_details"] = env_info
        return data
    
    async def _get_article_count(self):
        """获取文章数量"""
        try:
            result = await self.storage._execute_sql("SELECT COUNT(*) as count FROM articles")
            if result.get("success") and result.get("results"):
                return result["results"][0].get("count", 0)
        except:
            pass
        return 0
    
    async def handle_articles(self, parsed_url, method="GET"):
        """文章列表端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        query_params = parse_qs(parsed_url.query)
        source = query_params.get("source", [None])[0]
        page = int(query_params.get("page", ["1"])[0])
        page_size = min(int(query_params.get("page_size", ["20"])[0]), 100)
        
        filters = {}
        if source:
            filters["source"] = source
        
        offset = (page - 1) * page_size
        articles = await self.storage.fetch_articles(
            filters=filters, limit=page_size, offset=offset
        )
        stats = await self.storage.get_stats()
        
        return {
            "total": stats.get("total", len(articles)),
            "articles": articles,
            "page": page,
            "page_size": page_size
        }, 200
    
    async def handle_article_detail(self, path, method="GET"):
        """文章详情端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        # 提取 ID
        article_id = path.rstrip("/").split("/")[-1]
        article = await self.storage.fetch_article_by_id(article_id)
        
        if article:
            return {"article": article}, 200
        else:
            return {"error": "Article not found"}, 404
    
    async def handle_stats(self, method="GET"):
        """统计端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        stats = await self.storage.get_stats()
        return stats, 200
    
    async def handle_sources(self, method="GET"):
        """来源列表端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        stats = await self.storage.get_stats()
        return {"sources": stats.get("sources", [])}, 200
    
    async def handle_crawl_logs(self, parsed_url, method="GET"):
        """抓取日志端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        query_params = parse_qs(parsed_url.query)
        limit = min(int(query_params.get("limit", ["50"])[0]), 100)
        
        logs = await self.storage.get_crawl_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}, 200
    
    async def handle_crawl_stats(self, method="GET"):
        """抓取统计端点"""
        if method != "GET":
            return {"error": "Method not allowed"}, 405
        
        return {"message": "Not implemented"}, 501
