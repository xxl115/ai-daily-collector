/**
 * AI Daily Collector - Cloudflare Worker (最小化测试版)
 */

const DATA_URL = "https://raw.githubusercontent.com/xxl115/ai-daily-collector/master/data/daily.json";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Content-Type': 'application/json',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    try {
      // 根路径
      if (path === '/' || path === '') {
        return new Response(JSON.stringify({
          name: "AI Daily Collector",
          status: "ok",
          endpoints: ["/health", "/api/hotspots", "/rss"],
        }), { headers: corsHeaders });
      }

      // 健康检查
      if (path === '/health') {
        return new Response(JSON.stringify({
          status: "ok",
          timestamp: new Date().toISOString(),
        }), { headers: corsHeaders });
      }

      // 热点 API
      if (path.startsWith('/api/hotspots')) {
        const limit = parseInt(url.searchParams.get('limit') || '30');
        const response = await fetch(DATA_URL);
        if (!response.ok) {
          return new Response(JSON.stringify({
            success: false,
            error: "Failed to fetch data",
            data: [],
          }), { headers: corsHeaders });
        }
        const data = await response.json();
        return new Response(JSON.stringify({
          success: true,
          total: data.hotspots?.length || 0,
          data: data.hotspots?.slice(0, limit) || [],
          timestamp: new Date().toISOString(),
        }), { headers: corsHeaders });
      }

      // RSS
      if (path.startsWith('/rss')) {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
          return new Response('RSS unavailable', { status: 503 });
        }
        const data = await response.json();
        const items = data.hotspots || [];
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily</title>
    <link>https://ai-daily-collector.workers.dev</link>
    <description>AI News Hotspots</description>
    ${items.slice(0, 20).map(item => `
    <item>
      <title>${item.title || 'Untitled'}</title>
      <link>${item.url || '#'}</link>
      <description>${item.source || ''}</description>
    </item>`).join('')}
  </channel>
</rss>`;
        return new Response(xml, {
          headers: { 'Content-Type': 'application/rss+xml' }
        });
      }

      // 404
      return new Response(JSON.stringify({ error: "Not Found", path }), {
        status: 404,
        headers: corsHeaders
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: corsHeaders
      });
    }
  },
};
