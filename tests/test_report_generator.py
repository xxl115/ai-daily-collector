import os
from scripts.report_generator import ReportGenerator


def test_report_generator_writes_file(tmp_path):
    articles = [
        {
            'title': '测试文章一',
            'url': 'https://example.com/1',
            'source': '测试源',
            'tags': ['测试'],
            'summary': '这是摘要',
            'category': 'breaking',
        },
        {
            'title': '测试文章二',
            'url': 'https://example.com/2',
            'source': '测试源',
            'tags': ['测试'],
            'summary': '这是摘要2',
            'category': 'hot',
        }
    ]
    output_file = tmp_path / 'REPORT.md'
    rg = ReportGenerator()
    rg.generate(articles, str(output_file))
    assert output_file.exists(), "日报文件未创建"
    content = output_file.read_text(encoding='utf-8')
    assert 'AI Daily Report' in content
    assert '测试文章一' in content
