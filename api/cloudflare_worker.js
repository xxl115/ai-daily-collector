/**
 * AI Daily Collector - Cloudflare Worker
 * 
 * 提供 API 网关功能:
 * - 健康检查
 * - 热点数据 API
 * - RSS 订阅
 */

// 配置
const CF_WORKER_NAME = "ai-daily-collector";

const CACHE_TTL = {
  hotspots: 3600,    // 1小时
  rss: 1800,         // 30分钟
  stats: 300,        // 5分钟
};

// 热点数据 (静态示例，实际可从 KV 读取)
const SAMPLE_HOTSPOTS = [
  {
    title: "DeepSeek R1 发布",
    url: "https://github.com/deepseek-ai/DeepSeek-R1",
    source: "GitHub Trending",
    hot_score: 95,
    timestamp: new Date().toISOString(),
  },
  {
    title: "Claude Code 编程助手",
    url: "https://github.com/anthropics/claude-code",
    source: "GitHub",
    hot_score: 92,
    timestamp: new Date().toISOString(),
  },
  {
    title: "MCP 协议发布",
    url: "https://modelcontextprotocol.io",
    source: "Hacker News",
    hot_score: 88,
    timestamp: new Date().toISOString(),
  },
];

/**
 * 路由分发
 */
async function routeRequest(path, method, url, request, env, ctx) {
  // 根路径 - 返回使用说明
  if (path === '/' || path === '') {
    return new Response(JSON.stringify({
      name: "AI Daily Collector",
      version: "1.0.0",
      status: "ok",
      endpoints: {
        health: "/health",
        hotspots: "/api/hotspots",
        rss: "/rss/latest.xml",
      },
      timestamp: new Date().toISOString(),
    }, null, 2), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // 健康检查
  if (path === '/health') {
    return new Response(JSON.stringify({
      status: "ok",
      worker: CF_WORKER_NAME,
      timestamp: new Date().toISOString(),
      uptime: Date.now(),
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // 热点 API
  if (path === '/api/hotspots' || path === '/api/hotspots/') {
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const data = SAMPLE_HOTSPOTS.slice(0, limit);
    
    return new Response(JSON.stringify({
      success: true,
      count: data.length,
      data: data,
      timestamp: new Date().toISOString(),
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // RSS 订阅
  if (path.startsWith('/rss')) {
    const rss = generateRSS(SAMPLE_HOTSPOTS);
    return new Response(rss, {
      headers: {
        'Content-Type': 'application/rss+xml',
        'Cache-Control': 'public, max-age=1800',
      }
    });
  }

  // 404
  return new Response(JSON.stringify({
    error: "Not Found",
    path: path,
  }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 生成 RSS
 */
function generateRSS(items) {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI Daily Hotspots</title>
    <link>https://${CF_WORKER_NAME}.workers.dev</link>
    <description>Daily AI News Hotspots</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="https://${CF_WORKER_NAME}.workers.dev/rss/latest.xml" rel="self" type="application/rss+xml"/>
    ${items.map(item => `
    <item>
      <title><![CDATA[${item.title}]]></title>
      <link>${item.url}</link>
      <description><![CDATA[${item.source} - Hot Score: ${item.hot_score}]]></description>
      <pubDate>${new Date(item.timestamp).toUTCString()}</pubDate>
      <guid>${item.url}</guid>
    </item>`).join('')}
  </channel>
</rss>`;
  return xml;
}

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
      console.error('Request error:', error);
      
      return new Response(JSON.stringify({
        error: "Internal Server Error",
        message: error.message,
      }), {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
  },
};
