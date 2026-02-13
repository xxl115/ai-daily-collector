import json
import os
from scripts.content_processor import ContentProcessor


def main():
    os.environ['DRY_RUN'] = '1'
    processor = ContentProcessor(max_articles=2)
    articles = [
        {'url': 'http://example.com/a', 'title': '测试文章 A'},
        {'url': 'http://example.com/b', 'title': '测试文章 B'},
    ]
    results = processor.process_batch(articles)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
