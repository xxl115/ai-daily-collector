"""
Cloudflare Worker - Jina Reader API 代理
用于绕过 GitHub Actions 网络限制
"""

import os
import json
from js import fetch, Response


async def on_fetch(request):
    try:
        # 从 URL 获取要提取的 URL
        url_path = request.url.split("/extract?url=")[-1]
        if not url_path:
            return Response.new(
                json.dumps({"error": "Missing url parameter"}),
                headers={"content-type": "application/json"},
            )

        # URL 解码
        from urllib.parse import unquote

        target_url = unquote(url_path)

        # 获取 Jina API Key
        jina_key = os.environ.get("JINA_API_KEY", "")

        # 构建请求头
        headers = {
            "Accept": "application/json",
        }
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"

        # 转发到 r.jina.ai
        jina_url = f"https://r.jina.ai/{target_url}"
        resp = await fetch(jina_url, headers=headers)

        # 返回结果
        body = await resp.text()
        return Response.new(
            body,
            headers={
                "content-type": resp.headers.get("content-type", "text/plain"),
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception as e:
        return Response.new(
            json.dumps({"error": str(e)}), headers={"content-type": "application/json"}
        )
