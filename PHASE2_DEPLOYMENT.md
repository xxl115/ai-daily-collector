# Phase 2 Implementation - Production Deployment Guide

## Overview
Phase 2 adds Cloudflare D1 integration, structured logging, and production-ready configuration management.

## What's New

### 1. Cloudflare D1 Storage Adapter (`ingestor/storage/d1_adapter.py`)
**Features:**
- Full CRUD operations via Cloudflare D1 REST API
- Automatic schema creation (articles table + indexes)
- JSON serialization for categories/tags arrays
- Connection pooling and error handling
- Statistics and cleanup methods

**Database Schema:**
```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT NOT NULL,
    published_at TEXT,
    source TEXT NOT NULL,
    categories TEXT,        -- JSON array
    tags TEXT,              -- JSON array
    summary TEXT,
    raw_markdown TEXT,
    ingested_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_ingested_at ON articles(ingested_at);
```

### 2. Configuration Management (`config/config.py`)
**Environment Variables:**
- `ENVIRONMENT` - development/staging/production
- `DATABASE_PROVIDER` - local or d1
- `CF_ACCOUNT_ID` - Cloudflare account ID
- `CF_D1_DATABASE_ID` - D1 database ID
- `CF_API_TOKEN` - Cloudflare API token
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `LOG_FORMAT` - json or text

**Usage:**
```python
from config.config import load_config_from_env, get_storage_adapter

config = load_config_from_env()
storage = get_storage_adapter(config)
```

### 3. Structured Logging (`utils/logging_config.py`)
**Features:**
- JSON formatted logs for production
- Text formatted logs for development
- Structured log fields (source, articles_count, duration_ms)
- File and console output support

**Log Events:**
- Ingestion start/complete/error
- Storage operations
- Performance metrics

**Example Log Output:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Completed ingestion from MIT Tech Review: 10 articles in 1500.50ms",
  "logger": "ai_daily_collector",
  "source": "MIT Tech Review",
  "articles_count": 10,
  "duration_ms": 1500.50
}
```

### 4. Enhanced Main Entry Point
**Features:**
- Environment-based configuration
- Structured logging throughout
- Performance metrics tracking
- Error handling per source
- Source type filtering
- Dry-run mode
- Detailed statistics reporting

### 5. API Routes with D1 (`api/v2/routes_d1.py`)
**Endpoints:**
- `GET /api/v2/articles` - List articles with pagination
- `GET /api/v2/articles/{id}` - Get single article
- `GET /api/v2/stats` - Database statistics
- `GET /api/v2/sources` - List all sources
- `GET /api/v2/health` - Health check

## Deployment Steps

### 1. Setup Cloudflare D1

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create D1 database
wrangler d1 create ai-daily-collector

# Note the database ID from output
```

### 2. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your values
ENVIRONMENT=production
DATABASE_PROVIDER=d1
CF_ACCOUNT_ID=your_account_id
CF_D1_DATABASE_ID=your_database_id
CF_API_TOKEN=your_api_token
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3. Setup GitHub Actions Secrets

Go to GitHub Repository → Settings → Secrets and add:
- `CF_ACCOUNT_ID`
- `CF_API_TOKEN`
- `CF_D1_DATABASE_ID`

### 4. Initialize Database Schema

```bash
# Run a test ingestion to create tables
python ingestor/main.py --config config/sources.yaml --dry-run

# Or manually create schema using Wrangler
wrangler d1 execute ai-daily-collector --local --file=./schema.sql
```

### 5. Test Locally

```bash
# Test with local database
DATABASE_PROVIDER=local python ingestor/main.py --dry-run

# Test with D1 (requires credentials)
DATABASE_PROVIDER=d1 python ingestor/main.py --dry-run

# Run tests
pytest tests/ -v
```

### 6. Deploy API

```bash
# Using Cloudflare Workers (recommended)
wrangler deploy

# Or using Docker
docker build -t ai-daily-collector .
docker run -e DATABASE_PROVIDER=d1 -e CF_ACCOUNT_ID=xxx ... ai-daily-collector
```

## File Structure

```
ai-daily-collector/
├── ingestor/
│   ├── main.py                    # Production-ready entry point
│   ├── storage/
│   │   ├── d1_adapter.py         # Cloudflare D1 adapter
│   │   ├── db.py                  # Local adapter (fallback)
│   │   └── d1_client.py          # D1 REST client
│   └── scrapers/                  # All scrapers (from Phase 1)
├── api/
│   ├── storage/
│   │   └── dao.py                 # Data access object
│   └── v2/
│       ├── routes_d1.py          # D1-integrated routes
│       └── routes.py              # Original routes (backup)
├── config/
│   ├── config.py                  # Configuration management
│   └── sources.yaml               # Source definitions
├── utils/
│   └── logging_config.py          # Structured logging
├── .env.example                   # Environment template
└── .github/workflows/
    └── ingest_schedule.yml        # CI/CD pipeline
```

## Environment Switching

### Development (Local)
```bash
ENVIRONMENT=development
DATABASE_PROVIDER=local
LOG_FORMAT=text
```

### Staging (D1)
```bash
ENVIRONMENT=staging
DATABASE_PROVIDER=d1
LOG_FORMAT=json
```

### Production (D1)
```bash
ENVIRONMENT=production
DATABASE_PROVIDER=d1
LOG_FORMAT=json
LOG_LEVEL=WARNING
```

## Monitoring & Debugging

### View Logs
```bash
# Local text logs
python ingestor/main.py 2>&1 | tee ingestion.log

# Production JSON logs (use jq for parsing)
python ingestor/main.py 2>&1 | jq '.'
```

### Check Database Stats
```bash
# Using API curl http://localhost:8000/api/v2/stats
```

### Health Check
```bash
curl http://localhost:8000/api/v2/health
```

## Troubleshooting

### D1 Connection Issues
1. Verify `CF_ACCOUNT_ID` is correct
2. Check `CF_API_TOKEN` has D1 read/write permissions
3. Confirm `CF_D1_DATABASE_ID` exists

### Rate Limiting
- D1 API has rate limits
- Use caching in scrapers
- Add delays between requests

### Data Migration
```python
# Migrate from local to D1
from ingestor.storage.db import LocalDBAdapter
from ingestor.storage.d1_adapter import D1StorageAdapter

local = LocalDBAdapter()
d1 = D1StorageAdapter(account_id, database_id, api_token)

articles = local.fetch_articles({})
for article in articles:
    d1.upsert_article(article)
```

## Next Steps (Phase 3)

1. **Authentication** - Add API key authentication
2. **Rate Limiting** - Implement request throttling
3. **Caching** - Add Redis caching layer
4. **Monitoring** - Add metrics and alerting
5. **Backup** - Automated database backups

## Summary

Phase 2 provides:
- ✅ Production-ready D1 storage adapter
- ✅ Environment-based configuration
- ✅ Structured JSON logging
- ✅ Enhanced error handling
- ✅ API routes with D1 integration
- ✅ Comprehensive deployment documentation

The system is now ready for production deployment with Cloudflare D1!
