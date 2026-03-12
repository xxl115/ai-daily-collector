"""Debug 版本"""
from workers import WorkerEntrypoint
from js import Response
import json
from urllib.parse import urlparse

VERSION = "3.0.0"

class Default(WorkerEntrypoint):
    async def on_fetch(self, request, env, ctx):
        try:
            # 测试 self.env 是否可用
            has_env = hasattr(self, 'env')
            return Response(json.dumps({
                "has_self_env": has_env,
                "version": VERSION
            }))
        except Exception as e:
            return Response(json.dumps({"error": str(e)}))
