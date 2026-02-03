# -*- coding: utf-8 -*-
"""
推送服务模块

支持多种推送渠道:
- 飞书 (Feishu)
- 钉钉 (DingTalk)
- 企业微信 (WeChat Work)
- Telegram
"""

import json
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import requests
from pytz import timezone

from .logger import get_logger

logger = get_logger(__name__)


class PushPlatform(Enum):
    """推送平台枚举"""
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    WEWORK = "wework"
    TELEGRAM = "telegram"


class PushMessage:
    """推送消息"""
    
    def __init__(
        self,
        title: str,
        content: str,
        platform: PushPlatform = PushPlatform.FEISHU,
    ):
        self.title = title
        self.content = content
        self.platform = platform
        self.timestamp = datetime.now(timezone("Asia/Shanghai"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
        }


class BasePusher(ABC):
    """推送器基类"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    @abstractmethod
    def format_message(self, message: PushMessage) -> Dict[str, Any]:
        """格式化消息"""
        pass
    
    @abstractmethod
    def send(self, message: PushMessage) -> bool:
        """发送消息"""
        pass
    
    def _send_request(self, payload: Dict[str, Any]) -> bool:
        """发送 HTTP 请求"""
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"推送请求失败: {e}")
            return False


class FeishuPusher(BasePusher):
    """飞书推送器"""
    
    def __init__(self, webhook_url: str = None):
        # 从环境变量或配置获取
        webhook_url = webhook_url or os.environ.get(
            "FEISHU_WEBHOOK_URL", ""
        )
        super().__init__(webhook_url)
    
    def format_message(self, message: PushMessage) -> Dict[str, Any]:
        """飞书消息格式"""
        content = message.content
        
        # 飞书支持 Markdown
        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content,
                        },
                    }
                ],
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": message.title,
                    },
                },
            },
        }
    
    def send(self, message: PushMessage) -> bool:
        """发送飞书消息"""
        if not self.webhook_url:
            logger.warning("飞书 Webhook URL 未配置")
            return False
        
        payload = self.format_message(message)
        return self._send_request(payload)


class DingTalkPusher(BasePusher):
    """钉钉推送器"""
    
    def __init__(self, webhook_url: str = None):
        webhook_url = webhook_url or os.environ.get(
            "DINGTALK_WEBHOOK_URL", ""
        )
        super().__init__(webhook_url)
    
    def format_message(self, message: PushMessage) -> Dict[str, Any]:
        """钉钉消息格式"""
        content = message.content
        
        # 钉钉 Markdown 格式
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": message.title,
                "text": content,
            },
        }
    
    def send(self, message: PushMessage) -> bool:
        """发送钉钉消息"""
        if not self.webhook_url:
            logger.warning("钉钉 Webhook URL 未配置")
            return False
        
        payload = self.format_message(message)
        return self._send_request(payload)


class WeWorkPusher(BasePusher):
    """企业微信推送器"""
    
    def __init__(self, webhook_url: str = None):
        webhook_url = webhook_url or os.environ.get(
            "WEWORK_WEBHOOK_URL", ""
        )
        super().__init__(webhook_url)
    
    def format_message(self, message: PushMessage) -> Dict[str, Any]:
        """企业微信消息格式"""
        content = message.content
        
        # 企业微信 Markdown 格式
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content,
            },
        }
    
    def send(self, message: PushMessage) -> bool:
        """发送企业微信消息"""
        if not self.webhook_url:
            logger.warning("企业微信 Webhook URL 未配置")
            return False
        
        payload = self.format_message(message)
        return self._send_request(payload)


class TelegramPusher(BasePusher):
    """Telegram 推送器"""
    
    def __init__(
        self,
        bot_token: str = None,
        chat_id: str = None,
    ):
        bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        
        self.bot_token = bot_token
        self.chat_id = chat_id
        super().__init__(f"https://api.telegram.org/bot{bot_token}/sendMessage")
    
    def format_message(self, message: PushMessage) -> Dict[str, Any]:
        """Telegram 消息格式"""
        content = message.content
        
        # Telegram 支持 HTML/Markdown
        return {
            "chat_id": self.chat_id,
            "text": f"*{message.title}*\n\n{content}",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
    
    def send(self, message: PushMessage) -> bool:
        """发送 Telegram 消息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram 配置不完整")
            return False
        
        payload = self.format_message(message)
        return self._send_request(payload)


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.pushers: Dict[PushPlatform, BasePusher] = {}
        self._init_pushers()
    
    def _init_pushers(self):
        """初始化推送器"""
        self.pushers[PushPlatform.FEISHU] = FeishuPusher()
        self.pushers[PushPlatform.DINGTALK] = DingTalkPusher()
        self.pushers[PushPlatform.WEWORK] = WeWorkPusher()
        self.pushers[PushPlatform.TELEGRAM] = TelegramPusher()
    
    def send_to_all(
        self,
        title: str,
        content: str,
        platforms: List[PushPlatform] = None,
    ) -> Dict[PushPlatform, bool]:
        """发送到所有配置的渠道"""
        if platforms is None:
            platforms = list(PushPlatform)
        
        message = PushMessage(title=title, content=content)
        results = {}
        
        for platform in platforms:
            pusher = self.pushers.get(platform)
            if pusher and pusher.webhook_url:
                success = pusher.send(message)
                results[platform] = success
                if success:
                    logger.info(f"成功推送到 {platform.value}")
                else:
                    logger.error(f"推送到 {platform.value} 失败")
                # 避免请求过快
                time.sleep(1)
            else:
                logger.debug(f"{platform.value} 未配置，跳过")
                results[platform] = False
        
        return results
    
    def send_to_feishu(self, title: str, content: str) -> bool:
        """发送飞书"""
        return self.pushers[PushPlatform.FEISHU].send(
            PushMessage(title, content, PushPlatform.FEISHU)
        )
    
    def send_to_dingtalk(self, title: str, content: str) -> bool:
        """发送钉钉"""
        return self.pushers[PushPlatform.DINGTALK].send(
            PushMessage(title, content, PushPlatform.DINGTALK)
        )
    
    def send_to_wework(self, title: str, content: str) -> bool:
        """发送企业微信"""
        return self.pushers[PushPlatform.WEWORK].send(
            PushMessage(title, content, PushPlatform.WEWORK)
        )
    
    def send_to_telegram(self, title: str, content: str) -> bool:
        """发送 Telegram"""
        return self.pushers[PushPlatform.TELEGRAM].send(
            PushMessage(title, content, PushPlatform.TELEGRAM)
        )
    
    def get_config_status(self) -> Dict[str, Dict[str, Any]]:
        """获取配置状态"""
        status = {}
        for platform, pusher in self.pushers.items():
            status[platform.value] = {
                "configured": bool(pusher.webhook_url),
                "webhook_url": pusher.webhook_url[:20] + "..." if pusher.webhook_url else None,
            }
        return status


# 全局通知管理器实例
notification_manager = NotificationManager()


def send_daily_report(
    title: str,
    articles: List[Dict],
    platform: str = "feishu",
) -> bool:
    """
    发送每日报告
    
    Args:
        title: 报告标题
        articles: 文章列表
        platform: 推送平台
    
    Returns:
        是否发送成功
    """
    # 构建内容
    content = f"## {title}\n\n"
    content += f"**时间**: {datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')}\n\n"
    content += "---\n\n"
    
    for i, article in enumerate(articles[:20], 1):
        title_text = article.get("title", "无标题")
        url = article.get("url", "")
        source = article.get("source", "")
        
        content += f"**{i}. {title_text}**\n"
        if source:
            content += f"   - 来源: {source}\n"
        if url:
            content += f"   - [链接]({url})\n"
        content += "\n"
    
    # 根据平台选择推送方式
    platform_map = {
        "feishu": notification_manager.send_to_feishu,
        "dingtalk": notification_manager.send_to_dingtalk,
        "wework": notification_manager.send_to_wework,
        "telegram": notification_manager.send_to_telegram,
    }
    
    sender = platform_map.get(platform)
    if sender:
        return sender(title, content)
    else:
        logger.error(f"不支持的推送平台: {platform}")
        return False
