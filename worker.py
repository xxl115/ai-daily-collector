"""
Cloudflare Workers Python 入口文件
适配 FastAPI 应用以在 Workers 上运行
"""
from __future__ import annotations

import json
from typing import Dict, Any, Optional

# 导入我们的 FastAPI 应用组件
from api.v2.routes_d1 import router as v2_router
from api.storage.dao import ArticleDAO
from config.config import load_config_from_env, DatabaseConfig
from ingestor.storage.d1_adapter import D1StorageAdapter


class WorkersD1StorageAdapter(D1StorageAdapter):
    """适配 Cloudflare Workers D1 绑定的存储适配器"""
    
    def __init__(self, d1_binding):
        """
        Args:
            d1_binding: Cloudflare Workers D1 数据库绑定对象
        """
        self.db = d1_binding
    
    def _execute_sql(self, sql: str, params: Optional[list] = None) -> Dict[str, Any]:
        """通过 Workers D1 绑定执行 SQL"""
        try:
            # Workers D1 API 使用 db.prepare().bind().all() 模式
            stmt = self.db.prepare(sql)
            if params:
                stmt = stmt.bind(*params)
            result = stmt.all()
            return {
                "success": True,
                "results": result.results if hasattr(result, 'results') else []
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": str(e)}]
            }


async def handle_request(request, env):
    """处理 HTTP 请求的主函数"""
    
    url = request.url
    path = url.pathname
    method = request.method
    
    # 获取 D1 数据库绑定
    db = env.DB if hasattr(env, 'DB') else None
    
    # 初始化存储适配器
    if db:
        storage = WorkersD1StorageAdapter(db)
        dao = ArticleDAO(storage_adapter=storage)
    else:
        dao = None
    
    # 路由处理
    if path == "/" or path == "/health":
        return json_response({
            "status": "healthy",
            "database": "connected" if db else "disconnected",
            "timestamp": get_timestamp()
        })
    
    elif path == "/api/v2/articles":
        if method != "GET":
            return method_not_allowed()
        
        if not dao:
            return json_response({"error": "Database not available"}, status=500)
        
        # 解析查询参数
        query = url.search_params
        source = query.get("source")
        page = int(query.get("page", 1))
        page_size = min(int(query.get("page_size", 20)), 100)
        
        try:
            filters = {}
            if source:
                filters["source"] = source
            
            offset = (page - 1) * page_size
            articles = dao.fetch_articles(filters=filters, limit=page_size, offset=offset)
            stats = dao.get_stats()
            
            return json_response({
                "total": stats.get("total", len(articles)),
                "articles": [article_to_dict(a) for a in articles],
                "page": page,
                "page_size": page_size
            })
        except Exception as e:
            return json_response({"error": str(e)}, status=500)
    
    elif path.startswith("/api/v2/articles/"):
        if method != "GET":
            return method_not_allowed()
        
        if not dao:
            return json_response({"error": "Database not available"}, status=500)
        
        article_id = path.split("/")[-1]
        
        try:
            article = dao.fetch_article_by_id(article_id)
            if not article:
                return json_response({"error": "Article not found"}, status=404)
            
            return json_response(article_to_dict(article))
        except Exception as e:
            return json_response({"error": str(e)}, status=500)
    
    elif path == "/api/v2/stats":
        if method != "GET":
            return method_not_allowed()
        
        if not dao:
            return json_response({"error": "Database not available"}, status=500)
        
        try:
            stats = dao.get_stats()
            return json_response({
                "total_articles": stats.get("total", 0),
                "sources": [
                    {"source": k, "count": v}
                    for k, v in stats.get("sources", {}).items()
                ],
                "last_updated": get_timestamp()
            })
        except Exception as e:
            return json_response({"error": str(e)}, status=500)
    
    elif path == "/api/v2/sources":
        if method != "GET":
            return method_not_allowed()
        
        if not dao:
            return json_response({"error": "Database not available"}, status=500)
        
        try:
            stats = dao.get_stats()
            return json_response(list(stats.get("sources", {}).keys()))
        except Exception as e:
            return json_response({"error": str(e)}, status=500)
    
    else:
        return json_response({"error": "Not found"}, status=404)


def article_to_dict(article) -> Dict[str, Any]:
    """将 ArticleModel 转换为字典"""
    if isinstance(article, dict):
        return {
            "id": article.get("id", ""),
            "title": article.get("title", ""),
            "content": article.get("content", ""),
            "url": article.get("url", ""),
            "published_at": article.get("published_at"),
            "source": article.get("source", ""),
            "categories": article.get("categories", []),
            "tags": article.get("tags", []),
            "summary": article.get("summary"),
            "ingested_at": article.get("ingested_at", "")
        }
    else:
        return {
            "id": getattr(article, "id", ""),
            "title": getattr(article, "title", ""),
            "content": getattr(article, "content", ""),
            "url": getattr(article, "url", ""),
            "published_at": getattr(article, "published_at", None),
            "source": getattr(article, "source", ""),
            "categories": getattr(article, "categories", []),
            "tags": getattr(article, "tags", []),
            "summary": getattr(article, "summary", None),
            "ingested_at": getattr(article, "ingested_at", "")
        }


def json_response(data: Dict[str, Any], status: int = 200):
    """创建 JSON 响应"""
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        headers={"Content-Type": "application/json"}
    )


def method_not_allowed():
    """405 Method Not Allowed"""
    return json_response({"error": "Method not allowed"}, status=405)


def get_timestamp() -> str:
    """获取当前时间戳"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


class Response:
    """简单的响应类"""
    def __init__(self, body: str, status: int = 200, headers: Optional[Dict[str, str]] = None):
        self.body = body
        self.status = status
        self.headers = headers or {}


# Cloudflare Workers 入口点
async def on_fetch(request, env):
    """
    Workers fetch 事件处理器
    
    Args:
        request: HTTP 请求对象
        env: 环境变量和绑定（包含 D1 数据库）
    
    Returns:
        Response 对象
    """
    response = await handle_request(request, env)
    
    # 适配 Workers Response 格式
    if isinstance(response, Response):
        from js import Response as JSResponse
        return JSResponse.new(
            response.body,
            {
                "status": response.status,
                "headers": response.headers
            }
        )
    
    return response
