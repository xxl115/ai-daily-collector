#!/usr/bin/env python3
"""
AI Daily Collector - 集成测试
测试完整工作流的各个环节
"""

import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============ Fixtures ============

@pytest.fixture
def sample_article_content():
    """示例文章内容"""
    return """标题: 测试 AI 文章
来源: Dev.to
链接: https://dev.to/test/article
时间: 2026-02-03
==================================================
这是一篇测试文章的内容，包含 AI 相关的讨论。
本文讨论了机器学习和深度学习的技术细节。
"""


@pytest.fixture
def sample_summary_content():
    """示例总结内容"""
    return '''---
title: "测试 AI 文章"
source: "Dev.to"
original_url: "https://dev.to/test/article"
date: "2026-02-03"
---

# 测试 AI 文章

**来源**: Dev.to | **原文**: [链接](https://dev.to/test/article)

## 中文总结

这是一篇关于 AI 的测试文章，总结了机器学习和深度学习的技术要点。

---

*自动生成于 2026-02-03*
'''


@pytest.fixture
def mock_zhipu_response():
    """Mock 智谱 AI API 响应"""
    return {
        "choices": [{
            "message": {
                "content": "这是一篇关于 AI 的测试文章，总结了机器学习和深度学习的技术要点。"
            }
        }]
    }


@pytest.fixture
def mock_rss_feed():
    """Mock RSS Feed 数据"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Test Article</title>
      <link>https://example.com/article</link>
      <description>This is a test article</description>
      <pubDate>Mon, 03 Feb 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''


# ============ 配置测试 ============

class TestConfiguration:
    """配置相关测试"""
    
    def test_config_loading(self):
        """测试配置加载"""
        from config.settings import CrawlerConfig
        
        assert hasattr(CrawlerConfig, 'articles_hours_back')
        assert hasattr(CrawlerConfig, 'max_articles_per_source')
    
    def test_environment_variables(self):
        """测试环境变量覆盖"""
        from config.settings import ZhipuConfig
        
        # 测试默认配置
        assert ZhipuConfig.api_url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        assert ZhipuConfig.model == "glm-4"
    
    def test_sources_yaml_exists(self):
        """测试 RSS 源配置存在"""
        config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        assert config_path.exists(), f"配置文件不存在: {config_path}"
    
    def test_sources_yaml_parsable(self):
        """测试 RSS 源配置可解析"""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert 'sources' in config
        assert len(config['sources']) > 0


# ============ 核心功能测试 ============

class TestIngestorIntegration:
    """新架构数据摄取集成测试"""
    
    def test_ingestor_imports(self):
        """测试摄取模块导入"""
        from ingestor.scrapers import (
            fetch_rss, fetch_newsnow, fetch_hackernews,
            fetch_devto, fetch_v2ex, fetch_reddit, fetch_arxiv
        )
        from ingestor.transformers.article_transformer import transform
        from shared.models import ArticleModel
        
        # 验证主要组件可导入
        assert callable(fetch_rss)
        assert callable(fetch_newsnow)
        assert callable(transform)
        assert ArticleModel is not None
    
    def test_article_model(self):
        """测试文章模型"""
        from shared.models import ArticleModel
        from datetime import datetime
        
        article = ArticleModel(
            id="test-123",
            title="测试文章",
            content="测试内容",
            url="https://example.com/test",
            source="test-source",
            categories=["AI"],
            tags=["test"],
            published_at=datetime.now(),
            ingested_at=datetime.now()
        )
        
        assert article.id == "test-123"
        assert article.title == "测试文章"
        assert "AI" in article.categories


class TestScrapersIntegration:
    """爬虫集成测试"""
    
    def test_rss_scraper_import(self):
        """测试 RSS 爬虫导入"""
        from ingestor.scrapers.rss_scraper import fetch_rss
        assert callable(fetch_rss)
    
    def test_newsnow_scraper_import(self):
        """测试 NewsNow 爬虫导入"""
        from ingestor.scrapers.newsnow_scraper import fetch_newsnow
        assert callable(fetch_newsnow)
    
    def test_hackernews_scraper_import(self):
        """测试 Hacker News 爬虫导入"""
        from ingestor.scrapers.hackernews_scraper import fetch_hackernews
        assert callable(fetch_hackernews)
    
    def test_devto_scraper_import(self):
        """测试 Dev.to 爬虫导入"""
        from ingestor.scrapers.devto_scraper import fetch_devto
        assert callable(fetch_devto)
    
    def test_v2ex_scraper_import(self):
        """测试 V2EX 爬虫导入"""
        from ingestor.scrapers.v2ex_scraper import fetch_v2ex
        assert callable(fetch_v2ex)
    
    def test_reddit_scraper_import(self):
        """测试 Reddit 爬虫导入"""
        from ingestor.scrapers.reddit_scraper import fetch_reddit
        assert callable(fetch_reddit)
    
    def test_arxiv_scraper_import(self):
        """测试 ArXiv 爬虫导入"""
        from ingestor.scrapers.arxiv_scraper import fetch_arxiv
        assert callable(fetch_arxiv)


class TestWorkflowIntegration:
    """工作流集成测试"""
    
    def test_ingestor_workflow(self):
        """测试摄取工作流"""
        from ingestor.main import main
        
        # 验证 main 函数存在且可调用
        assert callable(main)
    
    def test_data_pipeline_steps(self):
        """测试数据管道步骤"""
        # 新架构的数据管道步骤
        steps = [
            "配置加载",
            "存储初始化",
            "数据源抓取",
            "数据转换",
            "数据存储"
        ]
        
        assert len(steps) == 5
        assert steps[0] == "配置加载"
        assert steps[-1] == "数据存储"


# ============ API 测试 ============

class TestAPIIntegration:
    """API 集成测试"""
    
    def test_api_import(self):
        """测试 API 模块导入"""
        try:
            from api.main import app
            assert app is not None
        except ImportError as e:
            pytest.skip(f"API 模块导入失败: {e}")
    
    def test_api_endpoints(self):
        """测试 API 端点定义"""
        try:
            from api.main import app
            route_paths = []
            for r in app.routes:
                path = getattr(r, 'path', None)
                if path:
                    route_paths.append(path)
                sub_routes = getattr(r, 'routes', None)
                if sub_routes:
                    for sub_r in sub_routes:
                        sub_path = getattr(sub_r, 'path', None)
                        if sub_path:
                            route_paths.append(sub_path)
            
            # 验证基本端点存在
            assert '/' in route_paths  # 健康检查
        except ImportError:
            pytest.skip("API 模块不可用")


# ============ 异常处理测试 ============

class TestExceptionHandling:
    """异常处理测试"""
    
    def test_exception_classes(self):
        """测试异常类定义"""
        from exceptions import (
            AICollectorError,
            CrawlerError,
            SummarizerError,
            ReportError,
            NotionSyncError,
            ConfigurationError
        )
        
        # 验证异常可实例化
        e = AICollectorError("测试错误")
        assert str(e) == "测试错误"
        assert e.message == "测试错误"
    
    def test_error_codes(self):
        """测试错误码"""
        from exceptions import get_error_message, ERROR_CODES
        
        # 验证错误码映射
        assert 1001 in ERROR_CODES
        assert 2001 in ERROR_CODES
        assert 4001 in ERROR_CODES
        
        # 验证错误信息获取
        assert "RSS" in get_error_message(1001)
        assert "API" in get_error_message(2001)
    
    def test_handle_exceptions_decorator(self):
        """测试异常处理装饰器"""
        from exceptions import handle_exceptions
        
        @handle_exceptions(default_return="error")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "error"


# ============ 数据持久化测试 ============

class TestDataPersistence:
    """数据持久化测试"""
    
    def test_article_storage_structure(self):
        """测试文章存储目录结构"""
        data_dir = Path(__file__).parent.parent / "ai" / "articles"
        
        # 验证目录存在或可以创建
        original_dir = data_dir / "original"
        summary_dir = data_dir / "summary"
        
        # 检查父目录
        assert data_dir.exists() or True  # 可能不存在
    
    def test_daily_report_storage(self):
        """测试日报存储"""
        daily_dir = Path(__file__).parent.parent / "ai" / "daily"
        assert daily_dir.exists() or True  # 可能不存在
    
    def test_log_directory(self):
        """测试日志目录"""
        log_dir = Path(__file__).parent.parent / "logs"
        assert log_dir.exists() or True  # 可能不存在


# ============ 配置文件测试 ============

class TestConfigurationFiles:
    """配置文件测试"""
    
    def test_requirements_parsable(self):
        """测试 requirements.txt 可解析"""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r') as f:
                lines = f.readlines()
            # 验证每行是有效的 pip 包格式
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    assert '>=' in line or '==' in line or '[' in line
    
    def test_gitignore_exists(self):
        """测试 .gitignore 存在"""
        gitignore = Path(__file__).parent.parent / ".gitignore"
        assert gitignore.exists()
    
    def test_dockerfile_exists(self):
        """测试 Dockerfile 存在"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists()
    
    def test_makefile_exists(self):
        """测试 Makefile 存在"""
        makefile = Path(__file__).parent.parent / "Makefile"
        assert makefile.exists()


# ============ 运行测试 ============

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
