"""
Cloudflare Workers Python 入口文件 - 重构版 v3
使用模块化结构
"""

from workers import WorkerEntrypoint
from js import Response
import json
from urllib.parse import urlparse, parse_qs

VERSION = "3.0.0"

# 导入模块
from api.storage import D1StorageAdapter
from api.handlers import APIHandlers
from api.classifier import classify as classify_text


class Default(WorkerEntrypoint):
    """Cloudflare Python Workers 入口类"""
    
    async def on_fetch(self, request, env, ctx):
        """处理所有 HTTP 请求"""
        # 获取数据库
        db = self._get_db()
        storage = D1StorageAdapter(db) if db else None
        handlers = APIHandlers(storage) if storage else None
        
        # 解析 URL
        url_str = str(request.url)
        parsed_url = urlparse(url_str)
        path = parsed_url.path
        method = request.method
        
        # 路由分发
        try:
            return await self._dispatch(path, method, parsed_url, request, handlers, storage)
        except Exception as e:
            return self._error(str(e))
    
    def _get_db(self):
        """获取 D1 数据库"""
        try:
            if hasattr(self.env, "DB"):
                return self.env.DB
        except:
            pass
        return None
    
    async def _dispatch(self, path, method, parsed_url, request, handlers, storage):
        """路由分发"""
        # 健康检查
        if path == "/" or path == "/health":
            return await self._health(handlers)
        
        # API v2 路由
        if path == "/api/v2/articles":
            return await handlers.handle_articles(parsed_url, method)
        
        if path.startswith("/api/v2/articles/"):
            return await handlers.handle_article_detail(path, method)
        
        if path == "/api/v2/stats":
            return await handlers.handle_stats(method)
        
        if path == "/api/v2/sources":
            return await handlers.handle_sources(method)
        
        # MCP 路由
        if path == "/mcp" or path == "/api/mcp":
            if method == "POST":
                return await self._mcp(request, handlers)
            elif method == "GET":
                return self._mcp_info(handlers)
        
        return self._not_found()
    
    async def _health(self, handlers):
        """健康检查"""
        if not handlers:
            return self._json({"status": "unhealthy", "version": VERSION})
        
        data = await handlers.handle_health()
        return self._json(data)
    
    def _mcp_info(self, handlers):
        """MCP 信息"""
        tools = ["get_articles_by_date", "update_article_summary_and_category", 
                 "classify_article", "list_categories", "get_tags"]
        return self._json({
            "name": "AI Daily Collector MCP",
            "version": VERSION,
            "tools": tools
        })
    
    async def _mcp(self, request, handlers):
        """MCP 请求"""
        if not handlers:
            return self._error("No storage")
        
        try:
            body = await request.json()
            tool_name = body.get("tool")
            arguments = body.get("arguments", {})
            
            # 使用简化逻辑
            if tool_name == "classify_article":
                text = arguments.get("text", "")
                result = classify_text(text)
                return self._json({"success": True, **result})
            
            return self._json({"error": f"Tool {tool_name} not implemented in v3"})
        except Exception as e:
            return self._error(str(e))
    
    def _json(self, data, status=200):
        """JSON 响应"""
        return Response(
            json.dumps(data, ensure_ascii=False),
            status=status,
            headers={"Content-Type": "application/json"}
        )
    
    def _not_found(self):
        """404"""
        return self._json({"error": "Not found"}, 404)
    
    def _error(self, message, status=500):
        """错误"""
        return self._json({"error": message}, status)


# 保留兼容性别名
WorkersD1StorageAdapter = D1StorageAdapter
