"""
Cloudflare Worker - Jina Reader API 代理
用于绕过 GitHub Actions 网络限制

用法:
  /extract?url=https://example.com
"""

import json
import os
from urllib.parse import unquote, urlparse
from js import fetch
from workers import Response


async def on_fetch(request, env):
    try:
        # 获取完整 URL 字符串
        url_str = str(request.url)

        # 解析 URL
        parsed = urlparse(url_str)
        path = parsed.path
        query = parsed.query

        # 健康检查端点
        if path == "/health" or path == "/" or path == "":
            return Response(
                '{"status": "ok", "service": "jina-proxy"}',
                headers=[
                    ("content-type", "application/json"),
                    ("Access-Control-Allow-Origin", "*"),
                ],
            )

        # 提取端点: /extract?url=xxx
        if path == "/extract" and query:
            # 解析 url 参数
            from urllib.parse import parse_qs
            params = parse_qs(query)
            if 'url' not in params or not params['url']:
                return Response(
                    json.dumps({"error": "Missing url parameter"}),
                    headers=[
                        ("content-type", "application/json"),
                        ("Access-Control-Allow-Origin", "*"),
                    ],
                )

            target_url = params['url'][0]
            target_url = unquote(target_url)

            # 通过 env 获取 secret（Cloudflare Workers 正确方式）
            jina_key = ""
            if env:
                try:
                    jina_key = getattr(env, "JINA_API_KEY", "") or ""
                except Exception:
                    pass

            headers_list = [("Accept", "application/json")]
            if jina_key:
                headers_list.append(("Authorization", f"Bearer {jina_key}"))

            jina_url = f"https://r.jina.ai/{target_url}"
            resp = await fetch(jina_url, headers=headers_list)

            body = await resp.text()
            content_type = resp.headers.get("content-type", "text/plain")
            return Response(
                body,
                headers=[
                    ("content-type", content_type),
                    ("Access-Control-Allow-Origin", "*"),
                ],
            )

        return Response(
            '{"error": "Not found"}',
            status=404,
            headers=[
                ("content-type", "application/json"),
                ("Access-Control-Allow-Origin", "*"),
            ],
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers=[
                ("content-type", "application/json"),
                ("Access-Control-Allow-Origin", "*"),
            ],
        )
