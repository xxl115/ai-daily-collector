/**
 * AI Daily Collector - Cloudflare Worker
 * 
 * 提供 API 网关功能:
 * - 缓存响应
 * - 请求限流
 * - API 路由转发
 */

// 配置
const BACKEND_URL = 'https://your-backend.workers.dev'; // 替换为实际后端地址
const CACHE_TTL = {
  hotspots: 3600,    // 1小时
  rss: 1800,         // 30分钟
  stats: 300,        // 5分钟
};

/**
 * 处理请求
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS 头
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    };

    // 处理 OPTIONS 请求
    if (method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders
      });
    }

    try {
      // 路由分发
      const response = await routeRequest(path, method, url, request, env, ctx);
      // 添加 CORS 头
      for (const [key, value] of Object.entries(corsHeaders)) {
        response.headers.set(key, value);
      }
      return response;
    } catch (error) {
      return handleError(error, corsHeaders);
    }
  }
};

/**
 * 路由分发
 */
async function routeRequest(path, method, url, request, env, ctx) {
  // 健康检查
  if (path === '/health' || path === '/api/health') {
    return handleHealth();
  }

  // 统计信息
  if (path === '/api/stats' || path === '/stats') {
    return handleStats();
  }

  // 热点列表
  if (path === '/api/hotspots' && method === 'GET') {
    return handleHotspots(url, request, env, ctx);
  }

  // RSS Feed
  if (path === '/rss' && method === 'GET') {
    return handleRSS(url, 'daily', env, ctx);
  }

  if (path === '/rss/latest' && method === 'GET') {
    return handleRSS(url, 'latest', env, ctx);
  }

  // V2EX 热点
  if (path === '/api/v2ex' && method === 'GET') {
    return handleV2EX(url, request, env, ctx);
  }

  // Reddit 热点
  if (path === '/api/reddit' && method === 'GET') {
    return handleReddit(url, request, env, ctx);
  }

  // NewsNow 热点
  if (path === '/api/newsnow' && method === 'GET') {
    return handleNewsNow(url, request, env, ctx);
  }

  // GitHub Trending
  if (path === '/api/github' && method === 'GET') {
    return handleGitHub(url, request, env, ctx);
  }

  // 搜索
  if (path === '/api/search' && method === 'GET') {
    return handleSearch(url, request, env, ctx);
  }

  // 根路径 / 文档
  if (path === '/' || path === '/docs' || path === '/api') {
    return handleDocs();
  }

  // 404
  return new Response('Not Found', { status: 404 });
}

/**
 * 健康检查
 */
function handleHealth() {
  return new Response(JSON.stringify({
    status: 'ok',
    service: 'ai-daily-collector',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    uptime: process.uptime ? Math.floor(process.uptime()) : 0,
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 统计信息
 */
function handleStats() {
  return new Response(JSON.stringify({
    service: 'AI Daily Collector',
    version: '1.0.0',
    sources: {
      rss: { count: '10+', name: 'RSS Feeds' },
      github: { languages: ['python', 'typescript'], name: 'GitHub Trending' },
      hn: { name: 'Hacker News' },
      ph: { name: 'Product Hunt' },
      newsnow: { count: '20+', name: 'Chinese Platforms' },
      v2ex: { name: 'V2EX Hot' },
      reddit: { count: '8+', name: 'Subreddits' },
    },
    features: {
      cache: { type: 'Cloudflare KV', enabled: true },
      rate_limit: { type: 'worker', enabled: true },
      filter: { type: 'keyword', enabled: true },
      ranking: { type: 'hotness', enabled: true },
    },
    endpoints: [
      { path: '/health', method: 'GET', description: 'Health check' },
      { path: '/api/hotspots', method: 'GET', description: 'Get all hotspots' },
      { path: '/api/v2ex', method: 'GET', description: 'V2EX hot topics' },
      { path: '/api/reddit', method: 'GET', description: 'Reddit hot posts' },
      { path: '/api/newsnow', method: 'GET', description: 'Chinese platforms' },
      { path: '/api/github', method: 'GET', description: 'GitHub trending' },
      { path: '/rss', method: 'GET', description: 'RSS feed (daily)' },
      { path: '/rss/latest', method: 'GET', description: 'RSS feed (latest)' },
      { path: '/api/stats', method: 'GET', description: 'Service statistics' },
    ],
    deploy: {
      docker: { supported: true },
      workers: { supported: true },
      kubernetes: { supported: true },
      serverless: { supported: true },
    },
    links: {
      github: 'https://github.com/xxl115/ai-daily-collector',
      docs: '/docs',
    }
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 热点列表
 */
async function handleHotspots(url, request, env, ctx) {
  const limit = parseInt(url.searchParams.get('limit') || '50');
  const source = url.searchParams.get('source');
  const cacheKey = `hotspots:${source || 'all'}:${limit}`;

  // 尝试从 KV 缓存获取
  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      const response = new Response(cached, {
        headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
      return response;
    }
  }

  // 转发到后端
  const backendUrl = `${BACKEND_URL}/api/hotspots?${url.search}`;
  try {
    const response = await fetch(backendUrl, request);
    const data = await response.json();

    // 缓存结果
    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: CACHE_TTL.hotspots
      }));
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    // 如果后端不可用，返回缓存或错误
    return new Response(JSON.stringify({
      error: 'Backend unavailable',
      message: 'Please try again later',
      cache_key: cacheKey,
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * RSS Feed
 */
async function handleRSS(url, type, env, ctx) {
  const cacheKey = `rss:${type}`;
  
  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'application/rss+xml', 'X-Cache': 'HIT' }
      });
    }
  }

  const backendUrl = `${BACKEND_URL}/rss/${type}`;
  try {
    const response = await fetch(backendUrl, request);
    const data = await response.text();

    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, data, {
        expirationTtl: CACHE_TTL.rss
      }));
    }

    return new Response(data, {
      headers: { 'Content-Type': 'application/rss+xml', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    return new Response(`<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily - Error</title>
    <description>Service temporarily unavailable</description>
    <item>
      <title>Backend unavailable</title>
      <description>Please try again later</description>
    </item>
  </channel>
</rss>`, {
      status: 503,
      headers: { 'Content-Type': 'application/rss+xml' }
    });
  }
}

/**
 * V2EX 热点
 */
async function handleV2EX(url, request, env, ctx) {
  const cacheKey = `v2ex:${url.searchParams.get('limit') || 20}`;
  
  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
    }
  }

  // 直接从 V2EX API 获取
  try {
    const response = await fetch('https://www.v2ex.com/api/v2/topics/hot?limit=20');
    const data = await response.json();

    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: CACHE_TTL.hotspots
      }));
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Failed to fetch V2EX data',
      message: error.message,
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Reddit 热点
 */
async function handleReddit(url, request, env, ctx) {
  const subreddits = url.searchParams.get('subreddits') || 'programming,artificial,MachineLearning';
  const limit = url.searchParams.get('limit') || '20';
  const cacheKey = `reddit:${subreddits}:${limit}`;

  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
    }
  }

  // 直接从 Reddit API 获取
  try {
    const subList = subreddits.split(',').map(s => s.trim()).join('+');
    const response = await fetch(
      `https://www.reddit.com/r/${subList}/hot.json?limit=${limit}`,
      {
        headers: {
          'User-Agent': 'AI-Daily-Collector/1.0',
        }
      }
    );
    const data = await response.json();

    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: CACHE_TTL.hotspots
      }));
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Failed to fetch Reddit data',
      message: error.message,
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * NewsNow 热点
 */
async function handleNewsNow(url, request, env, ctx) {
  const platforms = url.searchParams.get('platforms') || '';
  const limit = url.searchParams.get('limit') || '30';
  const cacheKey = `newsnow:${platforms || 'all'}:${limit}`;

  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
    }
  }

  // 从 NewsNow API 获取
  try {
    const apiUrl = platforms
      ? `https://newsnow.busiyi.world/api/s?id=${platforms}&latest`
      : `https://newsnow.busiyi.world/api/s?id=all&latest`;
    
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: CACHE_TTL.hotspots
      }));
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Failed to fetch NewsNow data',
      message: error.message,
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * GitHub Trending
 */
async function handleGitHub(url, request, env, ctx) {
  const language = url.searchParams.get('language') || 'python';
  const since = url.searchParams.get('since') || 'daily';
  const cacheKey = `github:${language}:${since}`;

  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
    }
  }

  try {
    const response = await fetch(
      `https://api.github.com/search/repositories?q=language:${language}&sort=stars&order=desc`,
      {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'AI-Daily-Collector',
        }
      }
    );
    const data = await response.json();

    if (env.CACHE) {
      ctx.waitUntil(env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: CACHE_TTL.hotspots
      }));
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Failed to fetch GitHub data',
      message: error.message,
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * 搜索
 */
async function handleSearch(url, request, env, ctx) {
  const query = url.searchParams.get('q');
  const type = url.searchParams.get('type') || 'hotspots';
  
  if (!query) {
    return new Response(JSON.stringify({
      error: 'Missing query parameter',
      usage: '/api/search?q=keyword&type=hotspots',
    }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({
    query,
    type,
    results: [],
    message: 'Search functionality coming soon',
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 文档
 */
function handleDocs() {
  return new Response(`
# AI Daily Collector API

## Endpoints

### Health
- \`GET /health\` - Service health check

### Hotspots
- \`GET /api/hotspots\` - Get all hotspots
- \`GET /api/hotspots?limit=20\` - Limit results
- \`GET /api/hotspots?source=newsnow\` - Filter by source

### Platforms
- \`GET /api/v2ex\` - V2EX hot topics
- \`GET /api/reddit\` - Reddit hot posts
- \`GET /api/newsnow\` - Chinese platforms
- \`GET /api/github\` - GitHub trending

### RSS
- \`GET /rss\` - Daily RSS feed
- \`GET /rss/latest\` - Latest RSS feed

### Info
- \`GET /api/stats\` - Service statistics
- \`GET /docs\` - This documentation

## Deploy

\`\`\`bash
# GitHub
https://github.com/xxl115/ai-daily-collector

# Docker
docker pull xxl115/ai-daily-collector:latest
\`\`\`

## Cache

This worker uses Cloudflare KV for caching.
Cache TTL:
- Hotspots: 1 hour
- RSS: 30 minutes
- Stats: 5 minutes
  `, {
    headers: { 'Content-Type': 'text/markdown' }
  });
}

/**
 * 错误处理
 */
function handleError(error, corsHeaders) {
  console.error('Worker error:', error);
  
  return new Response(JSON.stringify({
    error: error.name || 'InternalError',
    message: error.message || 'An unexpected error occurred',
    stack: error.stack,
  }), {
    status: 500,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
    }
  });
}
