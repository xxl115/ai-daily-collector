"""Scrapers package for fetching articles from various sources."""
from ingestor.scrapers.rss_scraper import fetch_rss
from ingestor.scrapers.newsnow_scraper import fetch_newsnow
from ingestor.scrapers.hackernews_scraper import fetch_hackernews
from ingestor.scrapers.devto_scraper import fetch_devto
from ingestor.scrapers.v2ex_scraper import fetch_v2ex
from ingestor.scrapers.reddit_scraper import fetch_reddit
from ingestor.scrapers.arxiv_scraper import fetch_arxiv

__all__ = [
    "fetch_rss",
    "fetch_newsnow",
    "fetch_hackernews",
    "fetch_devto",
    "fetch_v2ex",
    "fetch_reddit",
    "fetch_arxiv",
]
