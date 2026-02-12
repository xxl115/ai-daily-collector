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

            # 获取 D1 数据库绑定
            db = None
            db_error = None
            env_info = {}
            
            if env is None:
                db_error = "env is None - D1 binding not available"
                env_info = {"env_type": "None"}
            else:
                env_info = {
                    "env_type": type(env).__name__,
                    "env_attrs": [attr for attr in dir(env) if not attr.startswith('_')][:10]
                }
                try:
                    # Try to access DB binding
                    db = getattr(env, 'DB', None)
                    if db is None:
                        db_error = "env.DB is None - D1 binding may not be configured"
                except Exception as e:
                    db_error = f"Error accessing env.DB: {str(e)}"

            # 初始化存储适配器
            storage = WorkersD1StorageAdapter(db) if db else None

            # 健康检查端点 - 显示数据库连接状态
            if path == "/" or path == "/health":
                return self._health_response(storage, db_error, env_info)

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

            else:
                return self._json_response({"error": "Not found"}, status=404)

        except Exception as e:
            return self._json_response({
                "error": "Internal server error",
                "message": str(e)
            }, status=500)

    def _health_response(self, storage, db_error=None, env_info=None):
        """健康检查响应 - 显示数据库连接状态"""
        db_connected = storage is not None
        db_count = 0
        db_details = {}
        
        if storage:
            try:
                stats = storage.get_stats()
                db_count = stats.get("total", 0)
                db_details = {
                    "sources": stats.get("sources", {}),
                    "tables": storage._list_tables()
                }
            except Exception as e:
                db_count = f"ERROR: {str(e)}"
        
        response = {
            "status": "healthy",
            "version": VERSION,
            "database": {
                "connected": db_connected,
                "article_count": db_count,
                "error": db_error
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if db_details:
            response["database_details"] = db_details
        
        if env_info:
            response["env_info"] = env_info
            
        return self._json_response(response)

    async def _articles_response(self, parsed_url, storage):
        """文章列表响应 - 返回空列表当没有数据"""
        if not storage:
            return self._json_response({
                "total": 0,
                "articles": [],
                "page": 1,
                "page_size": 20,
                "message": "Database configured but no data yet"
            })

        try:
            query_params = parse_qs(parsed_url.query)
            source = query_params.get("source", [None])[0]
            page = int(query_params.get("page", ["1"])[0])
            page_size = min(int(query_params.get("page_size", ["20"])[0]), 100)

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
            return self._json_response({
                "error": str(e),
                "total": 0,
                "articles": []
            }, status=500)

    async def _article_detail_response(self, path, storage):
        """单篇文章详情响应"""
        if not storage:
            return self._json_response({"error": "Database not configured"}, status=500)

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
            return self._json_response({
                "total_articles": 0,
                "sources": [],
                "message": "No data yet"
            })

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
            return self._json_response([])

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
                "results": list(result.results) if hasattr(result, 'results') else []
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": str(e)}],
                "sql": sql
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
        # Get total count
        count_result = self._execute_sql("SELECT COUNT(*) as total FROM articles")
        total = 0
        if count_result.get("success") and count_result.get("results"):
            row = count_result["results"][0]
            # Handle both dict and numeric access
            if isinstance(row, dict):
                total = row.get("total", 0)
            else:
                total = row[0] if hasattr(row, '__getitem__') else 0

        # Get sources breakdown
        sources_result = self._execute_sql(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source"
        )
        sources = {}
        if sources_result.get("success"):
            for row in sources_result.get("results", []):
                if isinstance(row, dict):
                    sources[row.get("source", "unknown")] = row.get("count", 0)

        return {
            "total": total,
            "sources": sources
        }

    def _list_tables(self):
        """List all tables in the database"""
        result = self._execute_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        if result.get("success"):
            return [row.get("name") for row in result.get("results", [])]
        return []

    def _row_to_dict(self, row):
        """Convert database row to dict"""
        if not isinstance(row, dict):
            return {"raw_data": str(row)}
        
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
            "id": str(row.get("id", "")),
            "title": str(row.get("title", "")),
            "content": str(row.get("content", "")),
            "url": str(row.get("url", "")),
            "published_at": str(row.get("published_at")),
            "source": str(row.get("source", "")),
            "categories": categories,
            "tags": tags,
            "summary": str(row.get("summary", "")),
            "ingested_at": str(row.get("ingested_at", ""))
        }
