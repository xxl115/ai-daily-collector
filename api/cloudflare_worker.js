/**
 * AI Daily Collector - Cloudflare Worker (完整版)
 * 支持: /api/hotspots, /api/stats, /api/sources, /rss
 */

// Primary data source for hotspots (legacy master branch)
const DATA_URL = "https://raw.githubusercontent.com/xxl115/ai-daily-collector/master/data/daily.json";
// Fallback data sources (try alternative branches in case of rename)
const FALLBACK_DATA_URLS = [
  DATA_URL,
  "https://raw.githubusercontent.com/xxl115/ai-daily-collector/main/data/daily.json",
];

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
          version: "1.1.0",
          endpoints: ["/", "/health", "/api/hotspots", "/api/stats", "/api/sources", "/rss"],
          documentation: "https://github.com/xxl115/ai-daily-collector"
        }), { headers: corsHeaders });
      }

      // Health check
      if (path === '/health') {
        return new Response(JSON.stringify({
          status: "ok",
          timestamp: new Date().toISOString(),
          version: "1.1.0"
        }), { headers: corsHeaders });
      }

      // Hotspots API - 获取热点文章
      if (path.startsWith('/api/hotspots')) {
        const limit = parseInt(url.searchParams.get('limit') || '50');
        const source = url.searchParams.get('source');  // 筛选来源
        const keyword = url.searchParams.get('keyword'); // 关键词搜索
        
      // Try multiple data sources to improve reliability
      let data = null;
      for (const url of FALLBACK_DATA_URLS) {
        try {
          const dataResp = await fetch(url);
          if (dataResp && dataResp.ok) {
            data = await dataResp.json();
            break;
          }
        } catch (e) {
          // ignore and try next source
        }
      }
      if (!data) {
        // As a last resort, provide an empty payload to avoid breaking the API.
        data = { hotspots: [], generated_at: new Date().toISOString(), total_collected: 0 };
      }
        let items = data.hotspots || [];
        
        // 来源筛选
        if (source && source !== 'all') {
          items = items.filter(item => item.source === source);
        }
        
        // 关键词搜索
        if (keyword) {
          const kw = keyword.toLowerCase();
          items = items.filter(item => 
            (item.title && item.title.toLowerCase().includes(kw)) ||
            (item.source && item.source.toLowerCase().includes(kw))
          );
        }
        
        // 限制数量并按热度排序
        items = items
          .sort((a, b) => (b.hot_score || 0) - (a.hot_score || 0))
          .slice(0, limit);
        
        // 统计来源
        const sourceCounts = {};
        (data.hotspots || []).forEach(item => {
          const s = item.source || 'Unknown';
          sourceCounts[s] = (sourceCounts[s] || 0) + 1;
        });
        
        return new Response(JSON.stringify({
          success: true,
          total: items.length,
          filtered: items.length,
          filters: {
            source: source || 'all',
            keyword: keyword || ''
          },
          sources: Object.entries(sourceCounts).map(([name, count]) => ({ name, count })),
          generated_at: data.generated_at || new Date().toISOString(),
          data: items
        }), { headers: corsHeaders });
      }

      // Stats API - 获取统计信息
      if (path === '/api/stats') {
        const dataResp = await fetch(DATA_URL);
        
        if (!dataResp.ok) {
          return new Response(JSON.stringify({
            success: false,
            error: "Failed to fetch data"
          }), { headers: corsHeaders });
        }
        
        const data = await dataResp.json();
        const items = data.hotspots || [];
        
        // 计算统计
        const total = items.length;
        const sources = new Set(items.map(i => i.source));
        const avgScore = total > 0 
          ? (items.reduce((sum, i) => sum + (i.hot_score || 0), 0) / total).toFixed(1)
          : 0;
        
        return new Response(JSON.stringify({
          success: true,
          today: {
            date: new Date().toISOString().split('T')[0],
            articles: total,
            hot_score_avg: parseFloat(avgScore)
          },
          total: {
            articles: total,
            sources: sources.size
          },
          generated_at: new Date().toISOString()
        }), { headers: corsHeaders });
      }

      // Sources API - 获取来源列表
      if (path === '/api/sources') {
        const dataResp = await fetch(DATA_URL);
        
        if (!dataResp.ok) {
          return new Response(JSON.stringify({
            success: false,
            error: "Failed to fetch data"
          }), { headers: corsHeaders });
        }
        
        const data = await dataResp.json();
        const items = data.hotspots || [];
        
        // 统计来源
        const sourceCounts = {};
        items.forEach(item => {
          const s = item.source || 'Unknown';
          sourceCounts[s] = (sourceCounts[s] || 0) + 1;
        });
        
        const sources = Object.entries(sourceCounts)
          .map(([name, count]) => ({ name, count }))
          .sort((a, b) => b.count - a.count);
        
        return new Response(JSON.stringify({
          success: true,
          total: sources.length,
          sources: sources
        }), { headers: corsHeaders });
      }

      // RSS feed
      if (path.startsWith('/rss')) {
        const limit = parseInt(url.searchParams.get('limit') || '20');
        const dataResp = await fetch(DATA_URL);
        
        if (!dataResp.ok) {
          return new Response('RSS unavailable', { status: 503 });
        }
        
        const data = await dataResp.json();
        const items = (data.hotspots || []).slice(0, limit);
        
        const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily - ${new Date().toLocaleDateString('zh-CN')}</title>
    <link>https://ai-daily-collector.workers.dev</link>
    <description>AI 热点资讯自动采集</description>
    <language>zh-CN</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items.map(item => `
    <item>
      <title><![CDATA[${item.title || 'Untitled'}]]></title>
      <link>${item.url || '#'}</link>
      <description><![CDATA[来源: ${item.source || ''} | 热度: ${item.hot_score || 0}]]></description>
      <category>${item.source || 'AI'}</category>
      <pubDate>${item.published_at ? new Date(item.published_at).toUTCString() : new Date().toUTCString()}</pubDate>
    </item>`).join('')}
  </channel>
</rss>`;
        
        return new Response(xml, {
          headers: { 'Content-Type': 'application/rss+xml', ...corsHeaders }
        });
      }

      // 404 Not Found
      return new Response(JSON.stringify({ 
        error: "Not Found", 
        path: path,
        availableRoutes: ["/", "/health", "/api/hotspots", "/api/stats", "/api/sources", "/rss"]
      }), {
        status: 404,
        headers: corsHeaders
      });

    } catch (err) {
      return new Response(JSON.stringify({ 
        error: err.message,
        stack: process.env.DEBUG ? err.stack : undefined
      }), {
        status: 500,
        headers: corsHeaders
      });
    }
  },
};
