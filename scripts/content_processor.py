#!/usr/bin/env python3
"""AI 文章内容处理器（方案 A 基线实现）"""

import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import time
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict

try:
    from scripts.extractors import (
        TrafilaturaExtractor,
        JinaExtractor,
        Crawl4AIExtractor,
    )
except Exception:
    from scripts.extractors.trafilatura_extractor import TrafilaturaExtractor
    from scripts.extractors.jina_extractor import JinaExtractor
    from scripts.extractors.crawl4ai_extractor import Crawl4AIExtractor
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

    def __init__(self, max_articles: int = 30, mode: str = "full", d1_adapter=None):
        self.max_articles = max_articles
        self.mode = mode
        self.d1_adapter = d1_adapter
        self.extractor = TrafilaturaExtractor()
        self.fallback_extractor = JinaExtractor()
        self.fallback_extractor_2 = Crawl4AIExtractor()
        self.summarizer = OllamaSummarizer()
        self.classifier = BGEClassifier()
        self.report_generator = ReportGenerator()
        self.metrics = self._init_metrics()

        # 抓取状态记录
        self.extraction_stats = {
            "trafilatura_success": 0,
            "jina_success": 0,
            "crawl4ai_success": 0,
            "all_failed": 0,
            "failed_urls": [],  # 记录失败 URL 和原因
        }
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

    def process_article(self, url: str, title: str, original_id: str = None) -> Dict:
        # 使用原始 ID（如果是 D1）或生成新 UUID
        article_id = original_id if original_id else str(uuid.uuid4())
        extracted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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
            "processed_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "version": "v1",
        }
        logger.info(f"提取内容: {url}")

        # 三层降级提取策略
        extraction_method = None
        extraction_error = None

        if os.environ.get("DRY_RUN", "0") == "1":
            content = f"占位文本，原文 {url}"
        else:
            # 第一层：Trafilatura
            content = self.extractor.extract(url)
            if content:
                extraction_method = "trafilatura"
                self.extraction_stats["trafilatura_success"] += 1
                logger.info(f"Trafilatura 提取成功: {url}")
            else:
                # 第二层：Jina Reader
                content = self.fallback_extractor.extract(url)
                if content:
                    extraction_method = "jina"
                    self.extraction_stats["jina_success"] += 1
                    logger.info(f"Jina Reader 提取成功: {url}")
                else:
                    # 第三层：Crawl4AI
                    try:
                        content = self.fallback_extractor_2.extract(url)
                        if content:
                            extraction_method = "crawl4ai"
                            self.extraction_stats["crawl4ai_success"] += 1
                            logger.info(f"Crawl4AI 提取成功: {url}")
                        else:
                            extraction_method = "failed"
                            extraction_error = "All extractors returned empty"
                            self.extraction_stats["all_failed"] += 1
                            self.extraction_stats["failed_urls"].append(
                                {"url": url, "error": extraction_error}
                            )
                            logger.warning(f"所有提取器失败: {url}")
                    except Exception as e:
                        extraction_method = "failed"
                        extraction_error = str(e)
                        self.extraction_stats["all_failed"] += 1
                        self.extraction_stats["failed_urls"].append(
                            {"url": url, "error": extraction_error}
                        )
                        logger.error(f"Crawl4AI 提取异常: {url}, {e}")

        if not content:
            content = title
        if os.environ.get("DRY_RUN", "0") == "1":
            result["content"] = (content or title)[:10000]
            result["extraction_method"] = "dry-run"
            result["summary"] = "dry-run 摘要"
            result["category"] = "new"
            result["tags"] = []
            return result
        result["content"] = content[:10000]
        result["extraction_method"] = extraction_method or "unknown"
        result["extraction_error"] = extraction_error

        # 根据 mode 决定是否执行后续步骤
        if self.mode in ("full", "summarize-only"):
            logger.info("生成摘要...")
            result["summary"] = self.summarizer.summarize(content[:3000])
        else:
            result["summary"] = None

        if self.mode in ("full", "classify-only"):
            logger.info("智能分类...")
            classification = self.classifier.classify(
                title + " " + (result["summary"] or "")
            )
            result["category"] = classification.get("category", "new")
            result["tags"] = classification.get("tags", [])
        else:
            result["category"] = None
            result["tags"] = []
        return result

    def process_batch(self, articles: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        results: List[Dict] = []
        errors: List[Dict] = []
        seen = self._load_seen()
        for i, article in enumerate(articles[: self.max_articles]):
            url = article.get("url")
            if not url:
                logger.warning(f"跳过空 URL 文章: {article.get('title', 'unknown')}")
                continue
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
                        article["url"], article.get("title", ""), article.get("id")
                    )
                    elapsed = time.time() - start
                    logger.info(f"处理耗时: {elapsed:.2f}s")
                    results.append(result)

                    # 立即更新 D1（如果提供了 d1_adapter）
                    if self.d1_adapter and result.get("id") and result.get("content"):
                        self.d1_adapter.update_article_content(
                            result["id"],
                            result["content"],
                            result.get("extraction_method", "unknown"),
                        )
                        logger.info(f"已更新 D1 文章 content: {result['id']}")

                    if url:
                        seen.add(url)
                        self._save_seen()
                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    errors.append(
                        {"url": url, "error": str(e), "title": article.get("title", "")}
                    )
                    continue
        # Emit metrics for this batch execution
        self._emit_metrics()
        if articles:
            self._save_seen()
        return results, errors

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
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "extract-only", "summarize-only", "classify-only"],
        default="full",
        help="Processing mode: full (extract+summarize+classify) or single stage",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["local", "d1"],
        default="local",
        help="Data source: local files or D1 database",
    )
    parser.add_argument(
        "--d1-account-id", type=str, default=os.environ.get("CF_ACCOUNT_ID", "")
    )
    parser.add_argument(
        "--d1-database-id", type=str, default=os.environ.get("CF_D1_DATABASE_ID", "")
    )
    parser.add_argument(
        "--d1-api-token", type=str, default=os.environ.get("CF_API_TOKEN", "")
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    articles = []

    if args.source == "d1":
        # 从 D1 读取未提取的文章
        if not args.d1_account_id or not args.d1_database_id or not args.d1_api_token:
            logger.error(
                "D1 模式需要提供 --d1-account-id, --d1-database-id, --d1-api-token"
            )
            return

        from ingestor.storage.d1_adapter import D1StorageAdapter

        d1 = D1StorageAdapter(
            account_id=args.d1_account_id,
            database_id=args.d1_database_id,
            api_token=args.d1_api_token,
        )
        # 查询 content 为空（未提取）且有有效 URL 的文章
        sql = """
            SELECT id, url, title, source, ingested_at 
            FROM articles 
            WHERE (content IS NULL OR content = '') 
            AND url IS NOT NULL AND TRIM(url) != ''
            ORDER BY ingested_at DESC 
            LIMIT ?
        """
        logger.info(f"D1 SQL: {sql}")
        logger.info(f"D1 params: [{args.max_articles}]")
        result = d1._execute_sql(sql, [args.max_articles])
        logger.info(f"D1 result keys: {result.keys()}")

        # D1 API returns: {"result": [{"results": [...], "success": true, "meta": {...}}], "success": true}
        raw_result = result.get("result", [])
        if raw_result and isinstance(raw_result, list) and len(raw_result) > 0:
            rows = raw_result[0].get("results", [])
        else:
            rows = []

        logger.info(f"D1 rows count: {len(rows)}")
        if rows:
            logger.info(f"D1 first row keys: {rows[0].keys()}")
            logger.info(f"D1 first row: {rows[0]}")
        for row in rows:
            articles.append(
                {
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                    "id": row.get("id", ""),
                    "source": row.get("source", ""),
                }
            )
        logger.info(f"从 D1 加载了 {len(articles)} 篇未提取的文章")
    else:
        # 从本地目录读取
        for f in input_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            lines = content.split("\n")
            url = lines[0].replace("URL:", "").strip() if lines else ""
            title = lines[1].replace("标题:", "").strip() if len(lines) > 1 else f.name
            articles.append({"url": url, "title": title, "file": f.name})

    # 创建 D1 adapter（如果使用 D1 模式）
    d1_adapter = None
    if args.source == "d1" and args.mode in ("extract-only", "full"):
        from ingestor.storage.d1_adapter import D1StorageAdapter

        d1_adapter = D1StorageAdapter(
            account_id=args.d1_account_id,
            database_id=args.d1_database_id,
            api_token=args.d1_api_token,
        )

    processor = ContentProcessor(
        max_articles=args.max_articles, mode=args.mode, d1_adapter=d1_adapter
    )
    results, errors = processor.process_batch(articles)

    # 仅在非 D1 模式时保存到本地文件
    write_errors = []
    if args.source != "d1":
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            safe_title = result["title"][:50].replace(" ", "_").replace("/", "_")
            if not safe_title:
                safe_title = "article"
            output_file = output_dir / (safe_title + ".json")
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                write_errors.append({"file": str(output_file), "error": str(e)})
                logger.error(f"文件写入失败 {output_file}: {e}")

    # 生成日报 (仅在全量模式或非提取模式时)
    if args.mode == "full" and results:
        try:
            processor = ContentProcessor(max_articles=args.max_articles, mode=args.mode)
            processor.report_generator.generate(results, "ai/daily/REPORT.md")
        except Exception as e:
            logger.error(f"日报生成失败: {e}")
            write_errors.append({"file": "ai/daily/REPORT.md", "error": str(e)})

    # 输出处理统计
    logger.info(
        f"处理完成: {len(results)} 篇文章, {len(errors)} 个处理错误, {len(write_errors)} 个写入错误"
    )

    # 输出抓取状态统计
    if hasattr(processor, "extraction_stats"):
        stats = processor.extraction_stats
        logger.info(
            f"抓取状态: Trafilatura成功={stats['trafilatura_success']}, "
            f"Jina成功={stats['jina_success']}, "
            f"Crawl4AI成功={stats['crawl4ai_success']}, "
            f"全部失败={stats['all_failed']}"
        )

        if stats["failed_urls"]:
            logger.warning("抓取失败的URL:")
            for fail in stats["failed_urls"][:5]:
                logger.warning(f"  - {fail['url']}: {fail['error']}")

    if errors:
        logger.warning("处理错误详情:")
        for err in errors[:5]:
            logger.warning(
                f"  - {err.get('url', 'unknown')}: {err.get('error', 'unknown')}"
            )


if __name__ == "__main__":
    main()
