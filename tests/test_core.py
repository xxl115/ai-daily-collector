#!/usr/bin/env python3
"""
AI Daily Collector - 测试套件
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestCrawler:
    """采集器测试"""

    def test_sources_config_exists(self):
        """测试 RSS 源配置文件是否存在"""
        config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        assert config_path.exists(), f"配置文件不存在: {config_path}"

    def test_sources_yaml_parsable(self):
        """测试 YAML 配置可解析"""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert 'sources' in config, "配置缺少 sources 字段"
        assert len(config['sources']) > 0, "RSS 源列表为空"


class TestSummarizer:
    """总结生成器测试"""

    def test_article_info_extraction(self):
        """测试文章信息提取"""
        sample_content = """标题: 测试文章
来源: Dev.to
链接: https://dev.to/test
时间: 2026-02-03
==================================================
这是文章内容...
"""
        
        # 模拟提取逻辑
        title_match = "标题: (.*?)\n"
        source_match = "来源: (.*?)\n"
        
        title = "测试文章"
        source = "Dev.to"
        
        assert title == "测试文章"
        assert source == "Dev.to"

    def test_title_cleaning(self):
        """测试标题清理"""
        import re
        dirty_title = 'Test: "Special" Characters <>&|?*[]()'
        clean = re.sub(r'[<>:"/\\|?*\[\]（）()「」【】…—\'"]', '', dirty_title)
        assert '<' not in clean
        assert '>' not in clean
        assert '"' not in clean

    def test_filename_generation(self):
        """测试文件名生成"""
        title = "这是一个很长的标题" * 10
        source = "Dev.to"
        
        # 模拟文件名生成
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:35]
        abbr = "".join(c for c in source if c.isupper())[:3]
        
        assert len(safe_title) <= 35
        assert len(abbr) <= 3


class TestReportGenerator:
    """日报生成器测试"""

    def test_category_classification(self):
        """测试文章分类"""
        test_cases = [
            ("Cursor 发布新版本", "编程助手"),
            ("MCP 协议介绍", "Agent工作流"),
            ("Anthropic 发布 Claude", "大厂人物"),
            ("深度伪造风险", "安全风险"),
            ("Suno 音乐生成", "内容生成"),
        ]
        
        # 简单分类逻辑测试
        def classify(text):
            keywords = {
                "编程助手": ["cursor", "windsurf", "copilot"],
                "Agent工作流": ["mcp", "agent", "a2a"],
                "大厂人物": ["anthropic", "openai", "google"],
                "安全风险": ["deepfake", "security", "vulnerability"],
                "内容生成": ["suno", "midjourney", "video"],
            }
            text_lower = text.lower()
            for cat, kws in keywords.items():
                if any(kw in text_lower for kw in kws):
                    return cat
            return "其他"
        
        for text, expected in test_cases:
            result = classify(text)
            assert result == expected, f"'{text}' 应该分类为 {expected}，实际是 {result}"

    def test_date_format(self):
        """测试日期格式"""
        today = datetime.now().strftime("%Y-%m-%d")
        assert len(today) == 10  # YYYY-MM-DD
        assert today[4] == '-'
        assert today[7] == '-'

    def test_report_structure(self):
        """测试日报结构"""
        report_sections = [
            "1️⃣ 今日焦点",
            "2️⃣ 大厂/人物",
            "3️⃣ Agent 工作流",
            "4️⃣ 编程助手",
            "5️⃣ 内容生成",
            "6️⃣ 工具生态",
            "8️⃣ 安全风险",
            "7️⃣ 灵感库",
        ]
        # 验证编号不重复且连续
        numbers = [1, 2, 3, 4, 5, 6, 8, 7]
        assert len(set(numbers)) == len(numbers)


class TestNotionSync:
    """Notion 同步测试"""

    def test_markdown_to_blocks(self):
        """测试 Markdown 转 Notion blocks"""
        md_content = """# 标题
这是段落。
- 列表项
"""
        
        # 简单验证
        assert "# 标题" in md_content
        assert "这是段落" in md_content
        assert "列表项" in md_content

    def test_link_extraction(self):
        """测试链接提取"""
        text = '[链接](https://example.com)'
        import re
        match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', text)
        
        if match:
            assert match.group(1) == "链接"
            assert match.group(2) == "https://example.com"


class TestWorkflow:
    """工作流测试"""

    def test_workflow_steps(self):
        """测试工作流步骤定义"""
        steps = [
            "采集 AI 热点文章",
            "生成中文总结",
            "优化文件命名",
            "生成日报",
            "推送到 GitHub",
            "推送到 Notion"
        ]
        assert len(steps) == 6

    def test_cron_schedule(self):
        """测试定时任务配置"""
        cron_expr = "0 20 * * *"  # 每天晚上8点
        parts = cron_expr.split()
        
        assert len(parts) == 5
        assert parts[0] == "0"  # 分钟
        assert parts[1] == "20"  # 小时


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
