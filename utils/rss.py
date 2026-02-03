# AI Daily Collector - RSS 生成工具

"""
RSS/Atom Feed 生成工具

支持生成：
- RSS 2.0
- Atom 1.0
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class RSSGenerator:
    """RSS 2.0 生成器"""
    
    def __init__(
        self,
        title: str,
        link: str,
        description: str,
        language: str = "zh-CN",
        author: str = "AI Daily Collector",
        copyright: str = None,
    ):
        self.title = title
        self.link = link
        self.description = description
        self.language = language
        self.author = author
        self.copyright = copyright or f"© {datetime.now().year} {author}"
        self.items: List[Dict] = []
    
    def add_item(
        self,
        title: str,
        link: str,
        description: str = "",
        pub_date: str = None,
        guid: str = None,
        category: str = None,
        author: str = None,
    ):
        """添加 RSS 项"""
        self.items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date or datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "guid": guid or link,
            "category": category,
            "author": author or self.author,
        })
    
    def generate(self) -> str:
        """生成 RSS XML"""
        rss = Element('rss', version="2.0")
        rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
        rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        
        channel = SubElement(rss, 'channel')
        
        # Channel 信息
        self._add_element(channel, 'title', self.title)
        self._add_element(channel, 'link', self.link)
        self._add_element(channel, 'description', self.description)
        self._add_element(channel, 'language', self.language)
        self._add_element(channel, 'lastBuildDate', datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        
        # Atom link
        atom_link = SubElement(channel, 'atom:link')
        atom_link.set("href", self.link)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")
        
        # Items
        for item in self.items:
            item_elem = SubElement(channel, 'item')
            self._add_element(item_elem, 'title', item["title"])
            self._add_element(item_elem, 'link', item["link"])
            self._add_element(item_elem, 'description', item["description"])
            self._add_element(item_elem, 'pubDate', item["pub_date"])
            self._add_element(item_elem, 'guid', item["guid"], isPermaLink="false")
            
            if item.get("category"):
                self._add_element(item_elem, 'category', item["category"])
            
            if item.get("author"):
                dc_creator = SubElement(item_elem, 'dc:creator')
                dc_creator.text = item["author"]
        
        return self._to_string(rss)
    
    def _add_element(self, parent, tag: str, text: str = None, **attrs):
        """添加子元素"""
        if text is None:
            return
        elem = SubElement(parent, tag)
        elem.text = text[:2000] if len(str(text)) > 2000 else str(text)
        for key, value in attrs.items():
            elem.set(key, value)
    
    def _to_string(self, elem) -> str:
        """转换为格式化的 XML 字符串"""
        xml_str = tostring(elem, encoding='unicode')
        xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
        # 移除 XML 声明
        lines = xml_str.split('\n')
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
        return '\n'.join(lines).strip()


class AtomGenerator:
    """Atom 1.0 生成器"""
    
    def __init__(
        self,
        title: str,
        link: str,
        subtitle: str = "",
        author_name: str = "AI Daily Collector",
        author_email: str = None,
    ):
        self.title = title
        self.link = link
        self.subtitle = subtitle
        self.author_name = author_name
        self.author_email = author_email
        self.entries: List[Dict] = []
    
    def add_entry(
        self,
        title: str,
        link: str,
        content: str = "",
        summary: str = "",
        pub_date: str = None,
        id: str = None,
        author: str = None,
    ):
        """添加 Atom 条目"""
        self.entries.append({
            "title": title,
            "link": link,
            "content": content,
            "summary": summary,
            "pub_date": pub_date or datetime.now().isoformat() + "Z",
            "id": id or link,
            "author": author or self.author_name,
        })
    
    def generate(self) -> str:
        """生成 Atom XML"""
        feed = Element('feed', xmlns="http://www.w3.org/2005/Atom")
        
        # Feed 信息
        title_elem = SubElement(feed, 'title')
        title_elem.text = self.title
        
        if self.subtitle:
            subtitle_elem = SubElement(feed, 'subtitle')
            subtitle_elem.text = self.subtitle
        
        link_elem = SubElement(feed, 'link')
        link_elem.set("rel", "self")
        link_elem.set("href", self.link)
        link_elem.set("type", "application/atom+xml")
        
        updated = SubElement(feed, 'updated')
        updated.text = datetime.now().isoformat() + "Z"
        
        # Author
        author_elem = SubElement(feed, 'author')
        name_elem = SubElement(author_elem, 'name')
        name_elem.text = self.author_name
        if self.author_email:
            email_elem = SubElement(author_elem, 'email')
            email_elem.text = self.author_email
        
        id_elem = SubElement(feed, 'id')
        id_elem.text = f"tag:ai-daily-collector,{datetime.now().strftime('%Y-%m-%d')}:feed"
        
        # Entries
        for entry in self.entries:
            entry_elem = SubElement(feed, 'entry')
            
            title_elem = SubElement(entry_elem, 'title')
            title_elem.text = entry["title"]
            
            link_elem = SubElement(entry_elem, 'link')
            link_elem.set("rel", "alternate")
            link_elem.set("href", entry["link"])
            
            id_elem = SubElement(entry_elem, 'id')
            id_elem.text = entry["id"]
            
            updated_elem = SubElement(entry_elem, 'updated')
            updated_elem.text = entry["pub_date"]
            
            if entry.get("summary"):
                summary_elem = SubElement(entry_elem, 'summary')
                summary_elem.text = entry["summary"]
            
            if entry.get("content"):
                content_elem = SubElement(entry_elem, 'content')
                content_elem.set("type", "text/plain")
                content_elem.text = entry["content"]
        
        return self._to_string(feed)
    
    def _to_string(self, elem) -> str:
        """转换为格式化的 XML 字符串"""
        xml_str = tostring(elem, encoding='unicode')
        xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
        lines = xml_str.split('\n')
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
        return '\n'.join(lines).strip()


def generate_rss_from_articles(
    articles: List[Dict],
    title: str = "AI Daily",
    link: str = "https://github.com/xxl115/ai-daily-collector",
    description: str = "AI 热点资讯",
) -> str:
    """
    从文章列表生成 RSS Feed
    
    Args:
        articles: 文章列表，每篇文章包含 title, url, summary, source 等字段
        title: Feed 标题
        link: Feed 链接
        description: Feed 描述
    
    Returns:
        RSS 2.0 XML 字符串
    """
    generator = RSSGenerator(
        title=title,
        link=link,
        description=description,
    )
    
    for article in articles:
        generator.add_item(
            title=article.get("title", "无标题"),
            link=article.get("url", link),
            description=article.get("summary", "")[:500],
            pub_date=article.get("date", ""),
            guid=article.get("url", ""),
            category=article.get("source", ""),
        )
    
    return generator.generate()


def generate_atom_from_articles(
    articles: List[Dict],
    title: str = "AI Daily",
    link: str = "https://github.com/xxl115/ai-daily-collector",
    subtitle: str = "AI 热点资讯自动采集与分发",
) -> str:
    """
    从文章列表生成 Atom Feed
    
    Args:
        articles: 文章列表
        title: Feed 标题
        link: Feed 链接
        subtitle: Feed 子标题
    
    Returns:
        Atom 1.0 XML 字符串
    """
    generator = AtomGenerator(
        title=title,
        link=link,
        subtitle=subtitle,
    )
    
    for article in articles:
        generator.add_entry(
            title=article.get("title", "无标题"),
            link=article.get("url", link),
            content=article.get("summary", "")[:2000],
            summary=article.get("summary", "")[:500],
            pub_date=article.get("date", ""),
            id=article.get("url", ""),
        )
    
    return generator.generate()


if __name__ == "__main__":
    # 测试生成
    test_articles = [
        {
            "title": "AI News Test",
            "url": "https://example.com/article1",
            "summary": "这是一篇测试文章",
            "source": "Dev.to",
            "date": "2026-02-03",
        }
    ]
    
    print("=== RSS 2.0 ===")
    print(generate_rss_from_articles(test_articles))
    
    print("\n=== Atom 1.0 ===")
    print(generate_atom_from_articles(test_articles))
