# Dagster Pipeline for AI Content Pipeline (Phase B MVP)
#
# This is a minimal working DAG that can be extended.
# To run: dagster dev -m dagster.ai_content_pipeline
# Or: dagster job execute -m dagster.ai_content_pipeline

from dagster import (
    pipeline,
    solid,
    OpExecutionContext,
    Dict,
    String,
    List,
)
from typing import Any, Dict, List, Optional


# ==================== Solids ====================


@solid(
    name="extract_article",
    description="Extract content from URL using Trafilatura",
)
def extract_article(context: OpExecutionContext, url: str) -> Dict[str, Any]:
    """Extract article content from URL."""
    try:
        from scripts.extractors import TrafilaturaExtractor

        extractor = TrafilaturaExtractor()
        content = extractor.extract(url)
    except Exception as e:
        context.log.warning(f"Extraction failed for {url}: {e}")
        return {"url": url, "content": None, "success": False}

    if not content:
        context.log.warning(f"No content extracted from {url}")
        return {"url": url, "content": None, "success": False}

    return {
        "url": url,
        "content": content[:10000],
        "success": True,
    }


@solid(
    name="generate_summary",
    description="Generate summary using Ollama",
)
def generate_summary(
    context: OpExecutionContext, article: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate article summary using LLM."""
    if not article.get("success"):
        return article

    try:
        from scripts.summarizers import OllamaSummarizer

        summarizer = OllamaSummarizer()
        content = article.get("content", "")
        summary = summarizer.summarize(content[:3000])
    except Exception as e:
        context.log.error(f"Summary generation failed: {e}")
        summary = article.get("content", "")[:200]

    return {
        **article,
        "summary": summary,
    }


@solid(
    name="classify_article",
    description="Classify article using BGE",
)
def classify_article(
    context: OpExecutionContext, article: Dict[str, Any]
) -> Dict[str, Any]:
    """Classify article into categories."""
    if not article.get("success"):
        return article

    try:
        from scripts.classifiers import BGEClassifier

        classifier = BGEClassifier()
        title = article.get("title", "")
        summary = article.get("summary", "")
        result = classifier.classify(title + " " + summary)
    except Exception as e:
        context.log.error(f"Classification failed: {e}")
        result = {"category": "new", "tags": []}

    return {
        **article,
        "category": result.get("category", "new"),
        "tags": result.get("tags", []),
    }


@solid(
    name="persist_article",
    description="Save processed article to storage",
)
def persist_article(
    context: OpExecutionContext, article: Dict[str, Any]
) -> Dict[str, Any]:
    """Persist processed article to JSON file."""
    if not article.get("success"):
        return article

    import json
    from pathlib import Path
    from datetime import datetime
    import uuid

    output_dir = Path("ai/articles/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add metadata
    article["id"] = str(uuid.uuid4())
    article["processed_at"] = datetime.utcnow().isoformat() + "Z"
    article["version"] = "v1"

    try:
        safe_title = (
            article.get("title", "article")[:50].replace(" ", "_").replace("/", "_")
        )
        output_file = output_dir / f"{safe_title}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        context.log.info(f"Persisted article: {output_file}")
    except Exception as e:
        context.log.error(f"Failed to persist article: {e}")

    return article


@solid(
    name="generate_report",
    description="Generate daily report",
)
def generate_report(
    context: OpExecutionContext, articles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate daily report from processed articles."""
    from scripts.report_generator import ReportGenerator

    processed = [a for a in articles if a.get("success")]

    try:
        reporter = ReportGenerator()
        report_path = reporter.generate(processed, "ai/daily/REPORT.md")
        context.log.info(f"Generated report: {report_path}")
        return {"success": True, "article_count": len(processed)}
    except Exception as e:
        context.log.error(f"Failed to generate report: {e}")
        return {"success": False, "article_count": 0}


# ==================== Pipeline ====================


@pipeline(
    name="ai_content_pipeline",
    description="AI Content Processing Pipeline - Extract, Summarize, Classify",
)
def ai_content_pipeline():
    """Main pipeline for processing AI news articles.

    This pipeline can be invoked with a list of URLs:

    from dagster import build_op_context
    from dagster.ai_content_pipeline import ai_content_pipeline

    result = ai_content_pipeline.execute_in_process(
        run_config={
            "ops": {
                "extract_article": {"inputs": {"url": "https://example.com/article"}}
            }
        }
    )
    """
    pass


# ==================== Alternative: Asset-based Approach ====================
#
# For production use, consider using Dagster Assets for better observability:
#
# from dagster import asset, Definitions
# from dagster._core.definitions.definitions_class import Definitions
#
# @asset
# def urls() -> List[str]:
#     """List of URLs to process."""
#     return [...]
#
# @asset
# def extracted(urls: List[str]) -> List[Dict]:
#     """Extract content from URLs."""
#     ...
#
# @asset
# def processed(extracted: List[Dict]) -> List[Dict]:
#     """Summarize and classify."""
#     ...
#
# @asset
# def report(processed: List[Dict]) -> str:
#     """Generate daily report."""
#     ...
#
# defs = Definitions(assets=[urls, extracted, processed, report])
