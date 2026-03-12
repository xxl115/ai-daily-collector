"""D1 Storage 适配器模块"""

import json
from datetime import datetime


class D1StorageAdapter:
    """D1 存储适配器 - 简化版"""
    
    def __init__(self, d1_binding):
        self.db = d1_binding
    
    async def _execute_sql(self, sql, params=None):
        """执行 SQL"""
        try:
            stmt = self.db.prepare(sql)
            if params:
                stmt = stmt.bind(*params)
            result = await stmt.all()
            
            results = []
            if hasattr(result, "results"):
                results = list(result.results)
            elif isinstance(result, list):
                results = result
            
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_articles(self, filters=None, limit=50, offset=0):
        """获取文章列表"""
        sql = "SELECT * FROM articles LIMIT ? OFFSET ?"
        result = await self._execute_sql(sql, [limit, offset])
        
        articles = []
        if result.get("success"):
            for row in result.get("results", []):
                articles.append(self._row_to_dict(row))
        return articles
    
    async def fetch_article_by_id(self, article_id):
        """获取单篇文章"""
        sql = "SELECT * FROM articles WHERE id = ?"
        result = await self._execute_sql(sql, [article_id])
        
        if result.get("success") and result.get("results"):
            return self._row_to_dict(result["results"][0])
        return None
    
    async def get_all_categories(self):
        """获取所有分类"""
        sql = "SELECT * FROM categories ORDER BY id"
        result = await self._execute_sql(sql)
        
        categories = []
        if result.get("success"):
            for row in result.get("results", []):
                categories.append({
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "keywords": json.loads(row.get("keywords", "[]")) if row.get("keywords") else []
                })
        return categories
    
    async def create_category(self, name, keywords):
        """创建分类"""
        sql = "INSERT INTO categories (name, keywords) VALUES (?, ?)"
        result = await self._execute_sql(sql, [name, json.dumps(keywords)])
        return result.get("success")
    
    async def update_category(self, category_id, name, keywords):
        """更新分类"""
        sql = "UPDATE categories SET name = ?, keywords = ? WHERE id = ?"
        result = await self._execute_sql(sql, [name, json.dumps(keywords), category_id])
        return result.get("success")
    
    async def delete_category(self, category_id):
        """删除分类"""
        sql = "DELETE FROM categories WHERE id = ?"
        result = await self._execute_sql(sql, [category_id])
        return result.get("success")
    
    async def get_all_tags(self):
        """获取所有标签"""
        sql = "SELECT * FROM tags ORDER BY id"
        result = await self._execute_sql(sql)
        
        tags = []
        if result.get("success"):
            for row in result.get("results", []):
                tags.append({
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "keywords": json.loads(row.get("keywords", "[]")) if row.get("keywords") else []
                })
        return tags
    
    async def create_tag(self, name, keywords):
        """创建标签"""
        sql = "INSERT INTO tags (name, keywords) VALUES (?, ?)"
        result = await self._execute_sql(sql, [name, json.dumps(keywords)])
        return result.get("success")
    
    async def update_tag(self, tag_id, name, keywords):
        """更新标签"""
        sql = "UPDATE tags SET name = ?, keywords = ? WHERE id = ?"
        result = await self._execute_sql(sql, [name, json.dumps(keywords), tag_id])
        return result.get("success")
    
    async def delete_tag(self, tag_id):
        """删除标签"""
        sql = "DELETE FROM tags WHERE id = ?"
        result = await self._execute_sql(sql, [tag_id])
        return result.get("success")
    
    async def get_stats(self):
        """获取统计"""
        # 文章数
        result = await self._execute_sql("SELECT COUNT(*) as count FROM articles")
        total = result.get("results", [{}])[0].get("count", 0) if result.get("success") else 0
        
        # 来源统计
        result = await self._execute_sql("SELECT source, COUNT(*) as count FROM articles GROUP BY source")
        sources = {}
        if result.get("success"):
            for row in result.get("results", []):
                sources[row.get("source", "unknown")] = row.get("count", 0)
        
        return {"total": total, "sources": sources}
    
    def _row_to_dict(self, row):
        """转换行为字典"""
        if not row:
            return {}
        
        categories = []
        tags = []
        
        # 处理 categories
        cat_value = row.get("categories")
        if cat_value:
            try:
                categories = json.loads(cat_value) if isinstance(cat_value, str) else cat_value
            except:
                categories = []
        
        # 处理 tags
        tag_value = row.get("tags")
        if tag_value:
            try:
                tags = json.loads(tag_value) if isinstance(tag_value, str) else tag_value
            except:
                tags = []
        
        return {
            "id": str(row.get("id", "")),
            "title": str(row.get("title", "")),
            "content": str(row.get("content", "")),
            "url": str(row.get("url", "")),
            "published_at": row.get("published_at"),
            "source": str(row.get("source", "")),
            "categories": categories,
            "tags": tags,
            "summary": str(row.get("summary", "")),
            "ingested_at": str(row.get("ingested_at", "")),
            "is_ai_related": bool(row.get("is_ai_related", 0)),
        }
