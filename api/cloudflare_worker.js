/**
 * AI Daily Collector - Cloudflare Worker
 * 
 * 提供 API 网关功能:
 * - 健康检查
 * - 热点数据 API (从 GitHub 读取)
 * - RSS 订阅
 */

// 配置
const CF_WORKER_NAME = "ai-daily-collector";
const DATA_URL = "https://raw.githubusercontent.com/xxl115/ai-daily-collector/master/data/daily.json";

const CACHE_TTL = {
  data: 3600,     // 1小时
  hotspots: 3600,
  rss: 1800,      // 30分钟
};

/**
 * 缓存辅助函数
 */
const cache = new Map();

async function getCached(key) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.time < CACHE_TTL[key] * 1000) {
    return cached.data;
  }
  return null;
}

function setCache(key, data) {
  cache.set(key, { data, time: Date.now() });
}

/**
 * 获取热点数据
 */
async function fetchHotspots() {
  // 检查缓存
  const cached = getCached('hotspots');
  if (cached) return cached;
  
  try {
    const response = await fetch(DATA_URL, {
      headers: { 'Cache-Control': 'no-cache' }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    setCache('hotspots', data);
    return data;
  } catch (error) {
    console.error('Fetch hotspots error:', error);
    return null;
  }
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
    <description>Daily AI News Hotspots - Auto Generated</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="https://${CF_WORKER_NAME}.workers.dev/rss/latest.xml" rel="self" type="application/rss+xml"/>
    ${items.slice(0, 20).map(item => `
    <item>
      <title><![CDATA[${item.title || 'Untitled'}]]></title>
      <link>${item.url || '#'}</link>
      <description><![CDATA[${item.source || 'Unknown'} - Hot Score: ${item.hot_score || 0}]]></description>
      <pubDate>${new Date(item.timestamp || Date.now()).toUTCString()}</pubDate>
      <guid>${item.url || Date.now()}</guid>
    </item>`).join('')}
  </channel>
</rss>`;
  return xml;
}

/**
 * 路由分发
 */
async function routeRequest(path, method, url, request) {
  // 根路径 - 返回使用说明
  if (path === '/' || path === '') {
    return new Response(JSON.stringify({
      name: "AI Daily Collector",
      version: "1.0.0",
      status: "ok",
      data_source: DATA_URL,
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
    const limit = parseInt(url.searchParams.get('limit') || '30');
    const rawData = await fetchHotspots();
    
    if (!rawData) {
      return new Response(JSON.stringify({
        success: false,
        error: "Failed to fetch data",
        fallback: true,
        hotspots: [
          {
            title: "AI Daily Collector - 数据采集中",
            url: "https://github.com/xxl115/ai-daily-collector",
            source: "GitHub",
            hot_score: 100,
            timestamp: new Date().toISOString(),
          }
        ]
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    const items = rawData.hotspots || [];
    
    return new Response(JSON.stringify({
      success: true,
      total: items.length,
      limit: limit,
      data: items.slice(0, limit),
      generated_at: rawData.generated_at,
      timestamp: new Date().toISOString(),
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // RSS 订阅
  if (path.startsWith('/rss')) {
    const rawData = await fetchHotspots();
    const items = rawData?.hotspots || [];
    const rss = generateRSS(items);
    
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
 * 处理请求
 */
export default {
  async fetch(request) {
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
      const response = await routeRequest(path, method, url, request);
      
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
