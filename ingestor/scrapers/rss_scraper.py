#!/usr/bin/env python3
"""
RSS Scraper skeleton.
"""
from typing import List, Dict

def fetch_rss(url: str) -> List[Dict]:
    """Fetch and parse a simple RSS/Atom feed from the given URL.

    Returns a list of dict items with at least: id, title, url, summary,
    published_at, source.
    """
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

    channel = root.find('channel')
    if channel is not None:
        channel_title = channel.findtext('title') or ''
        for item in channel.findall('item'):
            title = item.findtext('title') or ''
            link = item.findtext('link') or ''
            description = item.findtext('description') or ''
            pubdate = item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or ''
            items.append({
                'id': link or pubdate or title,
                'title': title,
                'url': link,
                'description': description,
                'pubDate': pubdate,
                'pub_date': pubdate,
                'source': channel_title,
            })
        if not items:
            return []
        return items

    # Atom
    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        title = entry.findtext('{http://www.w3.org/2005/Atom}title') or ''
        link_el = entry.find('{http://www.w3.org/2005/Atom}link')
        link = link_el.get('href') if link_el is not None else ''
        pub = entry.findtext('{http://www.w3.org/2005/Atom}updated') or entry.findtext('{http://www.w3.org/2005/Atom}published') or ''
        summary = entry.findtext('{http://www.w3.org/2005/Atom}summary') or ''
        items.append({
            'id': link or title,
            'title': title,
            'url': link,
            'description': summary,
            'pubDate': pub,
            'pub_date': pub,
            'source': root.findtext('{http://www.w3.org/2005/Atom}author') or ''
        })
    return items
