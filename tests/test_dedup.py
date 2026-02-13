import os
from scripts.content_processor import ContentProcessor


def test_dedup_across_runs(tmp_path):
    # Ensure DRY_RUN mode to avoid real network I/O
    os.environ['DRY_RUN'] = '1'

    articles = [
        {'url': 'https://example.com/article1', 'title': '示例文章1'},
        {'url': 'https://example.com/article2', 'title': '示例文章2'},
    ]

    # First run: should process both
    p1 = ContentProcessor(max_articles=2)
    res1 = p1.process_batch(articles)
    assert len(res1) == 2

    # Second run with a new processor should skip duplicates
    p2 = ContentProcessor(max_articles=2)
    res2 = p2.process_batch(articles)
    # Since URLs were seen in previous run, nothing should be processed
    assert len(res2) == 0
