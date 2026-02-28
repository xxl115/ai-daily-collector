#!/usr/bin/env python3
"""
RSS Scraper skeleton.
"""

import hashlib
from typing import List, Dict


def generate_article_id(source: str, url: str) -> str:
    """Generate unique article ID from source and URL hash."""
    if not url:
        from datetime import datetime

        return (
            f"{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"
        )
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    clean_source = "".join(c for c in source if c.isalnum())[:20]
    return f"{clean_source}-{url_hash}"


def fetch_rss(url: str) -> List[Dict]:
    """Fetch and parse a simple RSS/Atom feed from the given URL."""
    import urllib.request
    import xml.etree.ElementTree as ET

    items: List[Dict] = []
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read()
    except Exception:
        return []

    try:
        root = ET.fromstring(data)
    except Exception:
        return []

    channel = root.find("channel")
    if channel is not None:
        channel_title = channel.findtext("title") or ""
        for item in channel.findall("item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            description = item.findtext("description") or ""
            pubdate = (
                item.findtext("pubDate")
                or item.findtext("{http://purl.org/dc/elements/1.1/}date")
                or ""
            )
            article_id = generate_article_id(channel_title, link or "")
            items.append(
                {
                    "id": article_id,
                    "title": title,
                    "url": link,
                    "description": description,
                    "pubDate": pubdate,
                    "pub_date": pubdate,
                    "source": channel_title,
                }
            )
        if not items:
            return []
        return items

    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = entry.findtext("{http://www.w3.org/2005/Atom}title") or ""
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = link_el.get("href") if link_el is not None else ""
        pub = (
            entry.findtext("{http://www.w3.org/2005/Atom}updated")
            or entry.findtext("{http://www.w3.org/2005/Atom}published")
            or ""
        )
        summary = entry.findtext("{http://www.w3.org/2005/Atom}summary") or ""
        article_id = generate_article_id(root.findtext("title") or "atom", link or "")
        items.append(
            {
                "id": article_id,
                "title": title,
                "url": link,
                "description": summary,
                "pubDate": pub,
                "pub_date": pub,
                "source": root.findtext("{http://www.w3.org/2005/Atom}author") or "",
            }
        )
    return items

    # Atom
    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = entry.findtext("{http://www.w3.org/2005/Atom}title") or ""
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = link_el.get("href") if link_el is not None else ""
        pub = (
            entry.findtext("{http://www.w3.org/2005/Atom}updated")
            or entry.findtext("{http://www.w3.org/2005/Atom}published")
            or ""
        )
        summary = entry.findtext("{http://www.w3.org/2005/Atom}summary") or ""
        article_id = generate_article_id(root.findtext("title") or "atom", link or "")
        items.append(
            {
                "id": article_id,
                "title": title,
                "url": link,
                "description": summary,
                "pubDate": pub,
                "pub_date": pub,
                "source": root.findtext("{http://www.w3.org/2005/Atom}author") or "",
            }
        )
    return items
