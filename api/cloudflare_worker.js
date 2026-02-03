/**
 * AI Daily Collector - Cloudflare Worker (修复版)
 */

const DATA_URL = "https://raw.githubusercontent.com/xxl115/ai-daily-collector/master/data/daily.json";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Content-Type': 'application/json',
    };

    // Handle OPTIONS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    try {
      // Root path - return info
      if (path === '/' || path === '') {
        return new Response(JSON.stringify({
          name: "AI Daily Collector",
          status: "ok",
          version: "1.0.1",
          endpoints: ["/health", "/api/hotspots", "/rss"],
        }), { headers: corsHeaders });
      }

      // Health check
      if (path === '/health') {
        return new Response(JSON.stringify({
          status: "ok",
          timestamp: new Date().toISOString(),
        }), { headers: corsHeaders });
      }

      // Hotspots API
      if (path.startsWith('/api/hotspots')) {
        const limit = parseInt(url.searchParams.get('limit') || '30');
        
        // 使用不同的变量名避免冲突
        const dataResp = await fetch(DATA_URL);
        
        if (!dataResp.ok) {
          return new Response(JSON.stringify({
            success: false,
            error: "Failed to fetch data",
            data: [],
          }), { headers: corsHeaders });
        }
        
        const data = await dataResp.json();
        return new Response(JSON.stringify({
          success: true,
          total: data.hotspots?.length || 0,
          data: data.hotspots?.slice(0, limit) || [],
          timestamp: new Date().toISOString(),
        }), { headers: corsHeaders });
      }

      // RSS feed
      if (path.startsWith('/rss')) {
        const dataResp = await fetch(DATA_URL);
        
        if (!dataResp.ok) {
          return new Response('RSS unavailable', { status: 503 });
        }
        
        const data = await dataResp.json();
        const items = data.hotspots || [];
        
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily</title>
    <link>https://ai-daily-collector.workers.dev</link>
    <description>AI News Hotspots</description>
    ${items.slice(0, 20).map(item => `
    <item>
      <title><![CDATA[${item.title || 'Untitled'}]]></title>
      <link>${item.url || '#'}</link>
      <description><![CDATA[${item.source || ''}]]></description>
    </item>`).join('')}
  </channel>
</rss>`;
        
        return new Response(xml, {
          headers: { 'Content-Type': 'application/rss+xml' }
        });
      }

      // 404 Not Found
      return new Response(JSON.stringify({ 
        error: "Not Found", 
        path: path,
        availableRoutes: ["/", "/health", "/api/hotspots", "/rss"]
      }), {
        status: 404,
        headers: corsHeaders
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: corsHeaders
      });
    }
  },
};
