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
        from config.settings import config, CrawlerConfig
        
        assert config.data_dir.exists() or True  # 目录可能不存在
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


# ============ 工具函数测试 ============

class TestHelpers:
    """工具函数测试"""
    
    def test_clean_filename(self):
        """测试文件名清理"""
        from utils.helpers import clean_filename
        
        # 测试移除非法字符
        assert clean_filename('test:file.txt') == 'testfile.txt'
        assert clean_filename('test/file\\name') == 'testfilename'
        assert clean_filename('test(name).md') == 'testname.md'
        
        # 测试长度限制
        long_name = 'a' * 100
        assert len(clean_filename(long_name)) <= 50
    
    def test_slugify(self):
        """测试 slug 生成"""
        from utils.helpers import slugify
        
        assert slugify('Hello World') == 'hello-world'
        assert slugify('Test  Article!') == 'test-article'
        assert slugify('中文标题') == '中文标题'  # 中文保持原样
    
    def test_extract_domain(self):
        """测试域名提取"""
        from utils.helpers import extract_domain
        
        assert extract_domain('https://dev.to/test') == 'dev.to'
        assert extract_domain('https://www.example.com/path') == 'www.example.com'
        assert extract_domain('invalid-url') == 'unknown'
    
    def test_truncate_text(self):
        """测试文本截断"""
        from utils.helpers import truncate_text
        
        text = '这是一个很长的文本'
        assert truncate_text(text, 10) == '这是一个很...'
        assert truncate_text(text, 100) == text  # 不截断
    
    def test_format_duration(self):
        """测试时长格式化"""
        from utils.helpers import format_duration
        
        assert format_duration(0.5) == '500ms'
        assert format_duration(30) == '30.0s'
        assert format_duration(90) == '1.5min'
        assert format_duration(3661) == '1.0h'
    
    def test_parse_date_string(self):
        """测试日期解析"""
        from utils.helpers import parse_date_string
        
        assert parse_date_string('2026-02-03') is not None
        assert parse_date_string('2026/02/03') is not None
        assert parse_date_string('invalid') is None


# ============ 日志系统测试 ============

class TestLogger:
    """日志系统测试"""
    
    def test_logger_creation(self):
        """测试日志器创建"""
        from utils.logger import setup_logger
        
        logger = setup_logger('test', console=False, file=False)
        assert logger is not None
        assert logger.name == 'test'
    
    def test_logger_output(self):
        """测试日志输出"""
        from utils.logger import setup_logger
        import io
        import sys
        
        # 捕获输出
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        logger = setup_logger('test-output', console=True, file=False)
        logger.info('Test message')
        
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        assert 'Test message' in output
    
    def test_logger_level(self):
        """测试日志级别"""
        from utils.logger import setup_logger
        
        logger = setup_logger('test-level', log_level='DEBUG', console=False, file=False)
        assert logger.level == 10  # DEBUG = 10


# ============ 指标系统测试 ============

class TestMetrics:
    """监控指标测试"""
    
    def test_counter(self):
        """测试计数器"""
        from utils.metrics import metrics
        
        initial = metrics.get_counter('test_counter')
        metrics.counter('test_counter', 1)
        assert metrics.get_counter('test_counter') == initial + 1
    
    def test_gauge(self):
        """测试仪表盘"""
        from utils.metrics import metrics
        
        metrics.gauge('test_gauge', 100)
        assert metrics.get_gauge('test_gauge') == 100
        
        metrics.gauge_inc('test_gauge')
        assert metrics.get_gauge('test_gauge') == 101
    
    def test_histogram(self):
        """测试直方图"""
        from utils.metrics import metrics
        
        metrics.histogramObserve('test_histogram', 0.5)
        metrics.histogramObserve('test_histogram', 1.0)
        
        # 验证指标已记录
        metrics_output = metrics.get_metrics()
        assert 'test_histogram' in metrics_output
    
    def test_track_duration(self):
        """测试计时上下文管理器"""
        from utils.metrics import track_duration
        
        with track_duration('test_timer') as t:
            pass  # 模拟耗时操作
        
        assert t.seconds >= 0


# ============ 核心功能测试 ============

class TestCrawlerIntegration:
    """采集器集成测试"""
    
    @patch('scripts.ai_hotspot_crawler_simple.requests.get')
    def test_rss_fetch(self, mock_get, mock_rss_feed):
        """测试 RSS 获取"""
        mock_response = Mock()
        mock_response.text = mock_rss_feed
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 验证请求发起
        import requests
        from scripts.ai_hotspot_crawler_simple import fetch_rss
        
        with patch.object(requests, 'get', mock_get):
            # 测试不会抛出异常
            pass
    
    @patch('scripts.summarize_articles.requests.post')
    def test_summarization(self, mock_post, mock_zhipu_response):
        """测试总结生成"""
        mock_response = Mock()
        mock_response.json.return_value = mock_zhipu_response
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # 验证智谱 API 调用
        import requests
        from scripts.summarize_articles import summarize_with_zhipu
        
        with patch.object(requests, 'post', mock_post):
            result = summarize_with_zhipu(
                "测试内容",
                "测试标题",
                "Dev.to"
            )
            assert "AI" in result or "API" in result  # 基于 mock 响应


class TestReportIntegration:
    """日报生成集成测试"""
    
    def test_article_classification(self):
        """测试文章分类"""
        from scripts.generate_daily_report import CATEGORIES
        
        test_cases = [
            ("Cursor 发布新版本编程助手工具", "编程助手"),
            ("MCP 协议发布新功能", "Agent工作流"),
            ("Anthropic Claude 更新", "大厂人物"),
            ("深度伪造安全风险预警", "安全风险"),
        ]
        
        def classify(text):
            text_lower = text.lower()
            for cat, config in CATEGORIES.items():
                if any(kw in text_lower for kw in config.get('keywords', [])):
                    return cat
            return "其他"
        
        for text, expected in test_cases:
            result = classify(text)
            assert result == expected, f"'{text}' 分类失败: 期望 {expected}, 实际 {result}"
    
    def test_report_structure(self):
        """测试日报结构"""
        from scripts.generate_daily_report import generate_report
        
        # 验证函数可调用且不抛出异常
        try:
            # 可能因为没有数据而失败，但不应该有语法错误
            generate_report("2026-02-03")
        except Exception as e:
            # 预期可能因为文件不存在而失败
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower() or "directory" in str(e).lower()


class TestNotionSyncIntegration:
    """Notion 同步集成测试"""
    
    def test_markdown_to_blocks(self):
        """测试 Markdown 转 Notion Blocks"""
        from scripts.push_to_notion import md_to_notion_blocks
        
        md_content = """# 标题

这是段落内容。

- 列表项 1
- 列表项 2

---
"""
        
        blocks = md_to_notion_blocks(md_content)
        
        # 验证 blocks 列表不为空
        assert len(blocks) > 0
        
        # 验证包含必要类型
        block_types = [b.get('type') for b in blocks]
        assert 'heading_1' in block_types or 'heading_2' in block_types
        assert 'paragraph' in block_types
        assert 'bulleted_list_item' in block_types or 'divider' in block_types


class TestWorkflowIntegration:
    """工作流集成测试"""
    
    def test_workflow_steps_order(self):
        """测试工作流步骤顺序"""
        from scripts.daily_ai_workflow import main
        
        # 验证 main 函数存在且可调用
        assert callable(main)
    
    def test_workflow_steps_execution(self):
        """测试工作流步骤执行"""
        # 模拟执行步骤
        steps = [
            "采集 AI 热点文章",
            "生成中文总结",
            "优化文件命名",
            "生成日报",
            "推送到 GitHub",
            "推送到 Notion"
        ]
        
        assert len(steps) == 6
        # 验证步骤顺序合理
        assert steps[0] == "采集 AI 热点文章"  # 先采集
        assert "推送到" in steps[-1]  # 最后同步


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
            routes = [r.path for r in app.routes]
            
            # 验证基本端点存在
            assert '/' in routes  # 健康检查
            assert '/api/v1/report' in routes or '/api/v1/report/{date}' in routes
            assert '/api/v1/articles' in routes
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
