"""
Cloudflare Workers Python 入口文件
使用官方推荐的 WorkerEntrypoint 模式
"""
from workers import WorkerEntrypoint
from js import Response
import json
from datetime import datetime


class Default(WorkerEntrypoint):
    """Cloudflare Python Workers 默认入口类"""

    async def fetch(self, request):
        """处理所有 HTTP 请求的主入口"""
        try:
            url = request.url
            path = url.pathname
            method = request.method

            # 获取 D1 数据库绑定
            db = None
            try:
                db = self.env.DB
            except:
                pass

            # 初始化存储适配器
            storage = WorkersD1StorageAdapter(db) if db else None

            # 路由处理
            if path == "/" or path == "/health":
                return self._health_response(db)

            elif path == "/api/v2/articles":
                if method != "GET":
                    return self._method_not_allowed()
                return await self._articles_response(request, storage)

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

            else:
                return self._json_response({"error": "Not found"}, status=404)

        except Exception as e:
            # 全局错误处理
            return self._json_response({
                "error": "Internal server error",
                "message": str(e)
            }, status=500)

    def _health_response(self, db):
        """健康检查响应"""
        return self._json_response({
            "status": "healthy",
            "database": "connected" if db else "disconnected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    async def _articles_response(self, request, storage):
        """文章列表响应"""
        if not storage:
            return self._json_response({"error": "Database not available"}, status=500)

        try:
            # 解析查询参数
            url = request.url
            query = url.search_params
            source = query.get("source")
            page = int(query.get("page", 1))
            page_size = min(int(query.get("page_size", 20)), 100)

            filters = {}
            if source:
                filters["source"] = source

            offset = (page - 1) * page_size
            articles = storage.fetch_articles(filters=filters, limit=page_size, offset=offset)
            stats = storage.get_stats()

            return self._json_response({
                "total": stats.get("total", len(articles)),
                "articles": articles,
                "page": page,
                "page_size": page_size
            })
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _article_detail_response(self, path, storage):
        """单篇文章详情响应"""
        if not storage:
            return self._json_response({"error": "Database not available"}, status=500)

        try:
            article_id = path.split("/")[-1]
            article = storage.fetch_article_by_id(article_id)

            if not article:
                return self._json_response({"error": "Article not found"}, status=404)

            return self._json_response(article)
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _stats_response(self, storage):
        """统计信息响应"""
        if not storage:
            return self._json_response({"error": "Database not available"}, status=500)

        try:
            stats = storage.get_stats()
            return self._json_response({
                "total_articles": stats.get("total", 0),
                "sources": [
                    {"source": k, "count": v}
                    for k, v in stats.get("sources", {}).items()
                ],
                "last_updated": datetime.utcnow().isoformat() + "Z"
            })
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _sources_response(self, storage):
        """数据源列表响应"""
        if not storage:
            return self._json_response({"error": "Database not available"}, status=500)

        try:
            stats = storage.get_stats()
            return self._json_response(list(stats.get("sources", {}).keys()))
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    def _json_response(self, data, status=200):
        """创建 JSON 响应"""
        return Response.new(
            json.dumps(data, ensure_ascii=False, default=str),
            {
                "status": status,
                "headers": {"Content-Type": "application/json"}
            }
        )

    def _method_not_allowed(self):
        """405 Method Not Allowed"""
        return self._json_response({"error": "Method not allowed"}, status=405)


class WorkersD1StorageAdapter:
    """适配 Cloudflare Workers D1 绑定的存储适配器"""

    def __init__(self, d1_binding):
        self.db = d1_binding

    def _execute_sql(self, sql, params=None):
        """通过 Workers D1 绑定执行 SQL"""
        try:
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

    def fetch_articles(self, filters=None, limit=50, offset=0):
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

        result = self._execute_sql(sql, params)

        articles = []
        if result.get("success"):
            for row in result.get("results", []):
                if isinstance(row, dict):
                    articles.append(self._row_to_dict(row))

        return articles

    def fetch_article_by_id(self, article_id):
        """Get a single article by ID"""
        sql = "SELECT * FROM articles WHERE id = ? LIMIT 1"
        result = self._execute_sql(sql, [article_id])

        if result.get("success") and result.get("results"):
            return self._row_to_dict(result["results"][0])

        return None

    def get_stats(self):
        """Get database statistics"""
        # Total count
        count_result = self._execute_sql("SELECT COUNT(*) as total FROM articles")
        total = 0
        if count_result.get("success") and count_result.get("results"):
            total = count_result["results"][0].get("total", 0)

        # Source breakdown
        sources_result = self._execute_sql(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source"
        )
        sources = {}
        if sources_result.get("success"):
            for row in sources_result.get("results", []):
                sources[row["source"]] = row["count"]

        return {
            "total": total,
            "sources": sources
        }

    def _row_to_dict(self, row):
        """Convert database row to dict"""
        categories = []
        tags = []

        if row.get("categories"):
            try:
                categories = json.loads(row["categories"])
            except:
                categories = []

        if row.get("tags"):
            try:
                tags = json.loads(row["tags"])
            except:
                tags = []

        return {
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "content": row.get("content", ""),
            "url": row.get("url", ""),
            "published_at": row.get("published_at"),
            "source": row.get("source", ""),
            "categories": categories,
            "tags": tags,
            "summary": row.get("summary"),
            "ingested_at": row.get("ingested_at", "")
        }
