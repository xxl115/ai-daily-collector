#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily Collector - 监控告警

功能:
- 采集失败时发送飞书通知
- 每日采集统计报告
- Worker 健康检查
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 飞书 Webhook
FEISHU_WEBHOOK_URL = ""  # 在 GitHub Secrets 中配置


def send_feishu_notification(title: str, content: str, webhook_url: str = None):
    """发送飞书通知"""
    if not webhook_url and not FEISHU_WEBHOOK_URL:
        print("⚠️ 飞书 Webhook 未配置，跳过通知")
        return False
    
    url = webhook_url or FEISHU_WEBHOOK_URL
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"## 🚨 {title}\n\n{content}"}
                },
                {
                    "tag": "div",
                    "fields": [
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**⏰ 时间**\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**🔧 状态**\n{'🔴 失败' if '失败' in title else '🟢 正常'}"}},
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "text": "📊 查看数据"},
                            "url": "https://github.com/xxl115/ai-daily-collector/actions",
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        import requests
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            print("✅ 飞书通知发送成功")
            return True
        else:
            print(f"❌ 飞书通知失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 飞书通知异常: {e}")
        return False


def send_daily_report(stats: dict, webhook_url: str = None):
    """发送每日采集报告"""
    title = "📊 AI Daily 采集报告"
    
    content = f"""
**采集统计:**
- 总计: {stats.get('total_collected', 0)} 条
- 热点: {stats.get('hotspots_count', 0)} 条
- 数据源: {stats.get('sources', 'N/A')}

**数据源详情:**
{chr(10).join([f"- {k}: {v} 条" for k, v in stats.get('sources_detail', {}).items()])}

**系统状态:**
- Worker: 🟢 正常
- 定时任务: 🟢 正常
    """
    
    return send_feishu_notification(title, content, webhook_url)


def send_error_alert(error_msg: str, webhook_url: str = None):
    """发送错误告警"""
    title = "⚠️ AI Daily 采集失败"
    
    content = f"""
**错误信息:**
```
{error_msg}
```

**建议:**
- 检查 GitHub Actions 日志
- 确认数据源可用性
- 查看是否需要更新依赖
    """
    
    return send_feishu_notification(title, content, webhook_url)


def send_health_alert(check_name: str, status: str, webhook_url: str = None):
    """发送健康检查告警"""
    title = f"🏥 {check_name} {'异常' if status == 'error' else '恢复正常'}"
    
    content = f"""
**检查项:** {check_name}
**状态:** {status}
**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return send_feishu_notification(title, content, webhook_url)


def check_worker_health(worker_url: str) -> dict:
    """检查 Worker 健康状态"""
    try:
        import requests
        resp = requests.get(worker_url + "/health", timeout=10)
        if resp.ok:
            data = resp.json()
            return {
                "status": "ok" if data.get("status") == "ok" else "error",
                "data": data,
                "message": "Worker 正常"
            }
        else:
            return {"status": "error", "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Daily 监控告警")
    parser.add_argument("--test", action="store_true", help="发送测试通知")
    parser.add_argument("--report", type=str, help="发送日报 (JSON 统计)")
    parser.add_argument("--error", type=str, help="发送错误告警")
    parser.add_argument("--health", action="store_true", help="健康检查")
    parser.add_argument("--webhook", type=str, help="飞书 Webhook URL")
    
    args = parser.parse_args()
    
    webhook = args.webhook or FEISHU_WEBHOOK_URL
    
    if args.test:
        send_feishu_notification("🧪 测试通知", "这是一条测试消息", webhook)
    elif args.report:
        stats = json.loads(args.report)
        send_daily_report(stats, webhook)
    elif args.error:
        send_error_alert(args.error, webhook)
    elif args.health:
        result = check_worker_health("https://ai-daily-collector.workers.dev")
        print(f"Worker 健康检查: {result}")
        if result["status"] == "error":
            send_health_alert("Worker API", "error", webhook)
    else:
        print("请指定参数: --test, --report, --error, --health")
        sys.exit(1)
