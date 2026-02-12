"""ArXiv API scraper for AI/ML papers."""
from __future__ import annotations

from typing import List, Dict, Any
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


def fetch_arxiv(search_query: str = "cat:cs.AI", max_articles: int = 15) -> List[Dict[str, Any]]:
    """Fetch papers from ArXiv API.
    
    Uses the ArXiv API (http://export.arxiv.org/api/query).
    
    Args:
        search_query: ArXiv search query (e.g., "cat:cs.AI" for AI papers,
                     "cat:cs.LG" for Machine Learning,
                     "cat:cs.CL" for Computation and Language)
        max_articles: Maximum articles to fetch
        
    Returns:
        List of article dictionaries
    """
    items: List[Dict[str, Any]] = []
    
    try:
        # Calculate date 48 hours ago
        start_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Build ArXiv API query
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_articles,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"http://export.arxiv.org/api/query?{query_string}"
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Collector/1.0)"
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(data)
        
        # Define namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        # Find all entry elements
        for entry in root.findall('.//atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text if title_elem is not None else ""
            title = title.replace('\n', ' ').strip() if title else ""
            
            if not title:
                continue
            
            # Get ID and URL
            id_elem = entry.find('atom:id', ns)
            arxiv_id = id_elem.text if id_elem is not None else ""
            
            # Get abstract
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text if summary_elem is not None else ""
            abstract = abstract.replace('\n', ' ').strip() if abstract else ""
            
            # Get published date
            published_elem = entry.find('atom:published', ns)
            published = published_elem.text if published_elem is not None else ""
            
            # Get authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)
            
            # Get categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term', '')
                if term:
                    categories.append(term)
            
            # Get PDF link
            pdf_url = ""
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href', '')
                    break
            
            # Primary category
            primary_category_elem = entry.find('arxiv:primary_category', ns)
            primary_category = primary_category_elem.get('term', '') if primary_category_elem is not None else ""
            
            items.append({
                "id": arxiv_id,
                "title": title,
                "url": arxiv_id,  # arxiv_id is already the URL
                "description": abstract[:1000],
                "pub_date": published,
                "source": "ArXiv",
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "pdf_url": pdf_url,
            })
            
    except Exception:
        return []
    
    return items
