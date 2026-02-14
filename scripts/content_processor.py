#!/usr/bin/env python3
"""AI 文章内容处理器（方案 A 基线实现）"""

import argparse
import time
import json
import logging
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    from scripts.extractors import TrafilaturaExtractor, JinaExtractor
except Exception:
    from scripts.extractors.trafilatura_extractor import TrafilaturaExtractor
    from scripts.extractors.jina_extractor import JinaExtractor
try:
    from scripts.summarizers import OllamaSummarizer
except Exception:
    from scripts.summarizers.ollama_summarizer import OllamaSummarizer
try:
    from scripts.classifiers import BGEClassifier
except Exception:
    from scripts.classifiers.bge_classifier import BGEClassifier
try:
    from scripts.report_generator import ReportGenerator
except Exception:
    from scripts.report_generator import ReportGenerator

try:
    from utils.rate_limit import SemaphoreLimiter, RateLimiter
except Exception:
    # 如果限流模块不可用，提供空实现
    class SemaphoreLimiter:
        def __init__(self, max_concurrent):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class RateLimiter:
        def __init__(self, *args, **kwargs):
            pass

        def wait_and_acquire(self):
            return 0


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentProcessor:
    """文章内容处理器（基线实现）"""

    # 类级别的限流器
    _semaphore = SemaphoreLimiter(max_concurrent=5)
    _rate_limiter = RateLimiter(max_calls=60, period=60.0)

    def __init__(self, max_articles: int = 30):
        self.max_articles = max_articles
        self.extractor = TrafilaturaExtractor()
        self.fallback_extractor = JinaExtractor()
        self.summarizer = OllamaSummarizer()
        self.classifier = BGEClassifier()
        self.report_generator = ReportGenerator()
        self.metrics = self._init_metrics()
        # 记录已处理的 URL 以实现简单的幂等/去重（持久化到磁盘）
        self._seen_path = Path(".ai_cache/processed_urls.json")
        self._seen_path.parent.mkdir(parents=True, exist_ok=True)
        if self._seen_path.exists():
            try:
                with open(self._seen_path, "r", encoding="utf-8") as f:
                    self._seen_urls = set(json.load(f))
            except Exception:
                self._seen_urls = set()
        else:
            self._seen_urls = set()

    def _load_seen(self) -> set:
        return self._seen_urls

    def _save_seen(self) -> None:
        try:
            with open(self._seen_path, "w", encoding="utf-8") as f:
                json.dump(list(self._seen_urls), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存已处理 URL 列表失败: {e}")

    def _init_metrics(self) -> dict:
        # Initialize metrics collection for observability
        return {
            "start_time": None,
            "pages_processed": 0,
            "duplicates_skipped": 0,
            "total_articles_seen": 0,
            "category_counts": {},
            "content_lengths": [],
            "summary_lengths": [],
            "processing_times": [],
        }

    def _emit_metrics(self) -> None:
        """Emit metrics as a Markdown JSON blob for quick inspection."""
        try:
            import datetime

            metrics_path = Path("ai/daily/REPORT_METRICS.md")
            metrics_path.parent.mkdir(parents=True, exist_ok=True)

            # 文件大小超过 1MB 时进行轮转
            if metrics_path.exists() and metrics_path.stat().st_size > 1024 * 1024:
                rotated_path = metrics_path.with_suffix(".old.md")
                if rotated_path.exists():
                    rotated_path.unlink()
                metrics_path.rename(rotated_path)
                logger.info(f"Metrics 文件已轮转: {rotated_path}")

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = {
                "timestamp": now,
                "metrics": self.metrics,
                "averages": {
                    "avg_processing_time_s": (
                        sum(self.metrics["processing_times"])
                        / len(self.metrics["processing_times"])
                    )
                    if self.metrics["processing_times"]
                    else 0,
                    "avg_content_len": (
                        sum(self.metrics["content_lengths"])
                        / len(self.metrics["content_lengths"])
                    )
                    if self.metrics["content_lengths"]
                    else 0,
                    "avg_summary_len": (
                        sum(self.metrics["summary_lengths"])
                        / len(self.metrics["summary_lengths"])
                    )
                    if self.metrics["summary_lengths"]
                    else 0,
                },
            }

            with open(metrics_path, "a", encoding="utf-8") as f:
                f.write("\n\n## Metrics Snapshot @ " + now + "\n")
                f.write("```json\n")
                f.write(json.dumps(data, ensure_ascii=False, indent=2))
                f.write("\n```\n")

        except Exception as e:
            logger.warning(f"写入 metrics 失败: {e}")

    def process_article(self, url: str, title: str) -> Dict:
        # 生成唯一 ID 和提取时间戳
        article_id = str(uuid.uuid4())
        extracted_at = datetime.utcnow().isoformat() + "Z"

        result = {
            "id": article_id,
            "url": url,
            "title": title,
            "content": "",
            "summary": "",
            "category": "new",
            "tags": [],
            "source": self._detect_source(url),
            "extracted_at": extracted_at,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "version": "v1",
        }
        logger.info(f"提取内容: {url}")
        # 干跑开关
        if os.environ.get("DRY_RUN", "0") == "1":
            content = f"占位文本，原文 {url}"
        else:
            content = self.extractor.extract(url)
        if not content:
            content = title
        if os.environ.get("DRY_RUN", "0") == "1":
            result["content"] = (content or title)[:10000]
            result["summary"] = "dry-run 摘要"
            result["category"] = "new"
            result["tags"] = []
            return result
        result["content"] = content[:10000]

        logger.info("生成摘要...")
        result["summary"] = self.summarizer.summarize(content[:3000])

        logger.info("智能分类...")
        classification = self.classifier.classify(title + " " + result["summary"])
        result["category"] = classification.get("category", "new")
        result["tags"] = classification.get("tags", [])
        return result

    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        results: List[Dict] = []
        seen = self._load_seen()
        for i, article in enumerate(articles[: self.max_articles]):
            url = article.get("url")
            if url in seen:
                logger.info(f"跳过已处理的 URL: {url}")
                continue
            logger.info(f"处理 {i + 1}/{len(articles)}: {article.get('title', '')}")

            # 限流：等待获取令牌
            wait_time = self._rate_limiter.wait_and_acquire()
            if wait_time > 0:
                logger.debug(f"速率限制等待: {wait_time:.2f}s")

            # 并发限制
            with self._semaphore:
                try:
                    start = time.time()
                    result = self.process_article(
                        article["url"], article.get("title", "")
                    )
                    elapsed = time.time() - start
                    logger.info(f"处理耗时: {elapsed:.2f}s")
                    results.append(result)
                    if url:
                        seen.add(url)
                        self._save_seen()
                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    continue
        # Emit metrics for this batch execution
        self._emit_metrics()
        if articles:
            self._save_seen()
        return results

    def _detect_source(self, url: str) -> str:
        domains = {
            "36kr.com": "36氪",
            "arxiv.org": "ArXiv",
            "news.ycombinator.com": "Hacker News",
            "techcrunch.com": "TechCrunch",
            "jiqizhixin.com": "机器之心",
            "mit.edu": "MIT Tech Review",
        }
        for domain, name in domains.items():
            if domain in url:
                return name
        return "其他"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default="ai/articles/original")
    parser.add_argument("--output", type=Path, default="ai/articles/processed")
    parser.add_argument("--max-articles", type=int, default=30)
    args = parser.parse_args()

    input_dir = Path(args.input)
    articles = []
    for f in input_dir.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        lines = content.split("\n")
        url = lines[0].replace("URL:", "").strip() if lines else ""
        title = lines[1].replace("标题:", "").strip() if len(lines) > 1 else f.name
        articles.append({"url": url, "title": title, "file": f.name})

    processor = ContentProcessor(max_articles=args.max_articles)
    results = processor.process_batch(articles)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        safe_title = result["title"][:50].replace(" ", "_").replace("/", "_")
        if not safe_title:
            safe_title = "article"
        output_file = output_dir / (safe_title + ".json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # 生成日报
    processor = ContentProcessor(max_articles=args.max_articles)
    processor.report_generator.generate(results, "ai/daily/REPORT.md")
    logger.info(f"处理完成: {len(results)} 篇文章")


if __name__ == "__main__":
    main()
