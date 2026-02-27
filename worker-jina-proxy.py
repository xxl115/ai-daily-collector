"""
Cloudflare Worker - Jina Reader API 代理
用于绕过 GitHub Actions 网络限制

用法:
  /extract?url=https://example.com
"""

import json
import os
from urllib.parse import unquote
from js import fetch
from workers import Response


async def on_fetch(request, env):
    try:
        url_str = str(request.url)

        # 健康检查端点
        if "/health" in url_str or url_str.endswith("/"):
            return Response(
                '{"status": "ok", "service": "jina-proxy"}',
                headers=[
                    ("content-type", "application/json"),
                    ("Access-Control-Allow-Origin", "*"),
                ],
            )

        if "/extract?url=" in url_str:
            parts = url_str.split("/extract?url=")
            if len(parts) < 2 or not parts[1]:
                return Response(
                    json.dumps({"error": "Missing url parameter"}),
                    headers=[
                        ("content-type", "application/json"),
                        ("Access-Control-Allow-Origin", "*"),
                    ],
                )

            target_url = unquote(parts[1])

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
