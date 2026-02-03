# -*- coding: utf-8 -*-
"""
Notion 同步模块

功能:
- 将 AI Daily 报告同步到 Notion
- 支持页面创建和内容更新
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import requests
from pytz import timezone

from .logger import get_logger

logger = get_logger(__name__)


class NotionSyncStatus(Enum):
    """同步状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class NotionClient:
    """Notion API 客户端"""

    def __init__(
        self,
        api_key: str = None,
        version: str = "2022-06-28",
    ):
        """
        初始化

        Args:
            api_key: Notion API Key
            version: API 版本
        """
        self.api_key = api_key or os.environ.get("NOTION_API_KEY", "")
        self.version = version
        self.base_url = "https://api.notion.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
            "User-Agent": "AI-Daily-Collector/1.0",
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
    ) -> Dict:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, timeout=30)
            else:
                raise ValueError(f"不支持的方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Notion API 请求失败: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"响应: {e.response.text[:500]}")
            return {"error": str(e)}

    def create_page(
        self,
        parent_id: str,
        title: str,
        content: str,
        date: str = None,
    ) -> Dict:
        """
        创建页面

        Args:
            parent_id: 父页面 ID
            title: 页面标题
            content: 页面内容（支持 Markdown）
            date: 日期字符串

        Returns:
            API 响应
        """
        # 解析内容中的链接
        blocks = self._content_to_blocks(content)

        data = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": blocks,
        }

        if date:
            # 如果有日期属性，添加
            data["properties"]["Date"] = {
                "date": {"start": date}
            }

        return self._request("POST", "/pages", data)

    def _content_to_blocks(self, content: str) -> List[Dict]:
        """
        将 Markdown 内容转换为 Notion blocks

        支持:
        - 无序列表 (• 或 -)
        - 有序列表 (1. 2. 3.)
        - 链接 [title](url)
        - 粗体 **text**
        - 换行
        """
        blocks = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测列表项
            if re.match(r"^[-•]\s+", line):
                # 无序列表
                text = re.sub(r"^[-•]\s+", "", line)
                block = self._text_to_block(text, "bulleted_list_item")
                blocks.append(block)

            elif re.match(r"^\d+[.）]\s+", line):
                # 有序列表
                text = re.sub(r"^\d+[.）]\s+", "", line)
                block = self._text_to_block(text, "numbered_list_item")
                blocks.append(block)

            elif re.match(r"^\d+[.）]\s+\[.+\]\(.+\)", line):
                # 带链接的列表项
                text = re.sub(r"^\d+[.）]\s+", "", line)
                block = self._text_to_block(text, "numbered_list_item")
                blocks.append(block)

            elif "•" in line:
                # 检测 Markdown 链接
                matches = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", line)
                if matches:
                    for title, url in matches:
                        text = f"[{title}]({url})"
                        block = self._text_to_block(text, "bulleted_list_item")
                        blocks.append(block)
                else:
                    # 普通段落
                    block = self._text_to_block(line, "paragraph")
                    blocks.append(block)

            else:
                # 普通段落
                block = self._text_to_block(line, "paragraph")
                blocks.append(block)

        return blocks[:100]  # Notion 限制

    def _text_to_block(self, text: str, block_type: str) -> Dict:
        """将文本转换为 block"""
        # 解析 Markdown 格式
        rich_text = []

        # 处理链接 [title](url)
        parts = re.split(r'(\[[^\]]+\]\([^)]+\))', text)
        for part in parts:
            if part.startswith("[") and "(" in part:
                match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', part)
                if match:
                    rich_text.append({
                        "type": "text",
                        "text": {
                            "content": match.group(1),
                            "link": {"url": match.group(2)}
                        }
                    })
            elif part:
                # 处理粗体
                part_clean = part
                if "**" in part_clean:
                    part_clean = re.sub(r"\*\*(.+?)\*\*", r"\1", part_clean)

                if part_clean:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": part_clean}
                    })

        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": rich_text}
        }

    def append_blocks(
        self,
        page_id: str,
        blocks: List[Dict],
    ) -> Dict:
        """追加 blocks 到页面"""
        data = {"children": blocks}
        return self._request("PATCH", f"/blocks/{page_id}/children", data)

    def query_database(
        self,
        database_id: str,
        filter_params: Dict = None,
    ) -> Dict:
        """查询数据库"""
        data = {}
        if filter_params:
            data["filter"] = filter_params

        return self._request("POST", f"/databases/{database_id}/query", data)

    def create_database_page(
        self,
        database_id: str,
        title: str,
        properties: Dict,
        content: str = "",
    ) -> Dict:
        """在数据库中创建页面"""
        props = {
            "Name": {
                "title": [{"text": {"content": title}}]
            }
        }
        props.update(properties)

        blocks = self._content_to_blocks(content) if content else []

        data = {
            "parent": {"database_id": database_id},
            "properties": props,
            "children": blocks,
        }

        return self._request("POST", "/pages", data)


class NotionSyncManager:
    """Notion 同步管理器"""

    def __init__(self, config: Dict = None):
        """
        初始化

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.client = NotionClient(
            api_key=self.config.get("api_key") or os.environ.get("NOTION_API_KEY"),
            version=self.config.get("version", "2022-06-28"),
        )
        self.parent_page_id = self.config.get("parent_page_id") or os.environ.get(
            "NOTION_PARENT_PAGE_ID", ""
        )

    def sync_daily_report(
        self,
        date: str,
        title: str,
        content: str,
        links: List[Dict] = None,
    ) -> Dict:
        """
        同步日报到 Notion

        Args:
            date: 日期
            title: 标题
            content: 内容
            links: 链接列表 [{"title": "", "url": ""}]

        Returns:
            同步结果
        """
        if not self.client.api_key:
            logger.warning("Notion API Key 未配置")
            return {"status": "failed", "error": "API Key 未配置"}

        if not self.parent_page_id:
            logger.warning("Notion Parent Page ID 未配置")
            return {"status": "failed", "error": "Parent Page ID 未配置"}

        # 构建内容
        sync_content = f"**🤖 AI Daily - {date}**\n\n"
        sync_content += f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"

        if links:
            for link in links[:20]:
                sync_content += f"• [{link.get('title', '')}]({link.get('url', '')})\n"

        sync_content += f"\n_自动生成_"

        # 创建页面
        page_title = f"AI Daily - {date}"
        result = self.client.create_page(
            parent_id=self.parent_page_id,
            title=page_title,
            content=sync_content,
            date=date,
        )

        if "error" in result:
            return {
                "status": "failed",
                "error": result["error"],
                "response": result,
            }

        logger.info(f"Notion 同步成功: {result.get('id', 'unknown')}")
        return {
            "status": "success",
            "page_id": result.get("id"),
            "url": f"https://notion.so/{result.get('id', '').replace('-', '')}",
        }

    def get_config_status(self) -> Dict:
        """获取配置状态"""
        return {
            "api_key_configured": bool(self.client.api_key),
            "parent_page_id_configured": bool(self.parent_page_id),
        }


# 全局实例
notion_sync_manager = NotionSyncManager()


def sync_to_notion(
    date: str,
    title: str,
    content: str,
    links: List[Dict] = None,
) -> Dict:
    """同步到 Notion"""
    return notion_sync_manager.sync_daily_report(date, title, content, links)


def get_notion_status() -> Dict:
    """获取 Notion 配置状态"""
    return notion_sync_manager.get_config_status()
