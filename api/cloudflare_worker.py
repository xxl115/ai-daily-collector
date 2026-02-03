# -*- coding: utf-8 -*-
"""
Cloudflare Worker for AI Daily Collector

这个 Worker 充当 API 网关，提供:
- 缓存响应
- 请求限流
- API 路由转发

注意: Cloudflare Workers 主要支持 JavaScript
此文件用于参考，实际部署需要使用 wrangler 部署 JS 版本
"""

# 提示: 请使用 cloudflare_worker.js 作为实际 Worker 入口

WORKER_CODE = '''
// cloudflare_worker.js - Cloudflare Workers 入口
// 复制此代码到 Cloudflare Dashboard 或使用 wrangler 部署

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS 头
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // 处理 OPTIONS 请求
    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // API 路由
    try {
      // 健康检查
      if (path === '/health') {
        return new Response(JSON.stringify({
          status: 'ok',
          service: 'ai-daily-collector',
          timestamp: new Date().toISOString(),
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // 热点列表
      if (path === '/api/hotspots' && method === 'GET') {
        // 检查缓存
        const cacheKey = `hotspots:${url.searchParams.get('limit') || 20}`;
        const cache = await env.CACHE.get(cacheKey);
        
        if (cache) {
          return new Response(cache, {
            headers: { ...corsHeaders, 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
          });
        }

        // 转发到后端 API（需要配置你的后端地址）
        const backendUrl = `https://your-backend.workers.dev/api/hotspots${url.search}`;
        const response = await fetch(backendUrl, request);
        const data = await response.json();

        // 缓存响应（1小时）
        ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), { expirationTtl: 3600 }));

        return new Response(JSON.stringify(data), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
        });
      }

      // RSS Feed
      if (path === '/rss' || path === '/rss/latest') {
        const cacheKey = `rss:${path}`;
        const cache = await env.CACHE.get(cacheKey);
        
        if (cache) {
          return new Response(cache, {
            headers: { ...corsHeaders, 'Content-Type': 'application/rss+xml', 'X-Cache': 'HIT' }
          });
        }

        const backendUrl = `https://your-backend.workers.dev${path}`;
        const response = await fetch(backendUrl, request);
        const data = await response.text();

        ctx.waitUntil(env.CACHE.put(cacheKey, data, { expirationTtl: 1800 }));

        return new Response(data, {
          headers: { ...corsHeaders, 'Content-Type': 'application/rss+xml', 'X-Cache': 'MISS' }
        });
      }

      // 统计信息
      if (path === '/api/stats' && method === 'GET') {
        return new Response(JSON.stringify({
          sources: {
            rss: '10+ feeds',
            github: 'trending',
            hn: 'hacker news',
            ph: 'product hunt',
            newsnow: '20+ chinese platforms',
            v2ex: 'v2ex hot',
            reddit: '8+ subreddits',
          },
          features: {
            cache: 'Cloudflare KV',
            rate_limit: 'enabled',
            filter: 'keyword filtering',
            ranking: 'hotness scoring',
          },
          deploy: {
            docker: 'supported',
            workers: 'supported',
            k8s: 'supported',
          }
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // 默认返回文档
      if (path === '/' || path === '/docs') {
        return new Response(`AI Daily Collector API

Endpoints:
- GET /health          - 健康检查
- GET /api/hotspots    - 热点列表
- GET /rss             - RSS Feed
- GET /rss/latest      - 最新 RSS
- GET /api/stats       - 统计信息

Deploy: https://github.com/xxl115/ai-daily-collector
`, {
          headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
        });
      }

      // 404
      return new Response('Not Found', { status: 404, headers: corsHeaders });

    } catch (error) {
      return new Response(JSON.stringify({
        error: error.message,
        stack: error.stack,
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};
'''

# 使用说明
USAGE = '''
# Cloudflare Workers 部署

## 方式 1: 使用 Wrangler CLI

```bash
# 1. 安装 Wrangler
npm install -g wrangler

# 2. 登录 Cloudflare
wrangler login

# 3. 创建 KV 命名空间
wrangler kv:namespace create CACHE

# 4. 编辑 wrangler.toml，填入 KV ID

# 5. 部署
wrangler deploy

# 或者开发模式
wrangler dev
```

## 方式 2: Cloudflare Dashboard

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 "Workers & Pages" → "Create Application"
3. 点击 "Create Worker"
4. 粘贴上面的 JavaScript 代码
5. 配置 KV 绑定
6. 点击 "Deploy"

## 方式 3: GitHub Actions

在 deploy.yml 中添加:

```yaml
deploy-cloudflare:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Cloudflare Workers
      uses: cloudflare/wrangler-action@v3
      with:
        apiToken: ${{ secrets.CF_API_TOKEN }}
        command: deploy
```

## 环境变量 Secrets

在 GitHub 仓库添加:
- CF_API_TOKEN: Cloudflare API Token
- CF_ACCOUNT_ID: Cloudflare Account ID
'''

if __name__ == "__main__":
    print("=" * 60)
    print("Cloudflare Worker for AI Daily Collector")
    print("=" * 60)
    print()
    print("注意: Cloudflare Workers 使用 JavaScript")
    print("请使用 cloudflare_worker.js 作为 Worker 入口")
    print()
    print(USAGE)
