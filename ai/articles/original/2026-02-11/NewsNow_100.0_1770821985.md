---
title: "Vibe Code 了一个记录汽车能耗，保养，配件等的工具"
url: "https://www.v2ex.com/t/1192331"
source: "NewsNow 中文热点"
date: 2026-02-11
score: 100.0
---

# Vibe Code 了一个记录汽车能耗，保养，配件等的工具

**来源**: [NewsNow 中文热点](https://www.v2ex.com/t/1192331) | **热度**: 100.0

## 原文内容

Title: Vibe Code 了一个记录汽车能耗，保养，配件等的工具 - V2EX

URL Source: http://www.v2ex.com/t/1192331

Published Time: 2026-02-11T14:20:07Z

Markdown Content:
我之前用的是腾讯的小程序，但是进去要点好多次，还要等。现在又 AI 了，直接就用 Antigravity 做了一个工具。

![Image 1](https://i.v2ex.co/16m3ojIBl.png)

*   项目页面： [https://boxks.com/carnote](https://boxks.com/carnote)
*   Github： [https://github.com/Kaiyuan/CarNote/](https://github.com/Kaiyuan/CarNote/)
*   我搭建好的： [https://carnote.boxks.com/](https://carnote.boxks.com/)

现在好了，点开就能记了。

我建好的加了会员功能，默认能管理 2 台车，进阶会员可以管理 5 台车，￥ 30/年，专业会员无限制车辆，可以多台车数据对比，可以修改时间范围，￥ 200/年。

自建的没有限制。

### 快速部署

```
# CarNote Docker Compose 配置
# 包含后端 API 服务和可选的 PostgreSQL 数据库

version: '3.8'

services:
  # 主应用服务 (包含前后端)
  app:
    image: kaiyuan/carnote:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: carnote
    ports:
      - "53300:53300"
    environment:
      - NODE_ENV=production
      - PORT=53300
      - DB_TYPE=sqlite
      - SQLITE_PATH=/app/data/carnote.db
      # - DB_TYPE=postgresql
      # - PG_HOST=172.20.0.1
      # - PG_PORT=5432
      # - PG_DATABASE=carnote
      # - PG_USER=carnote
      # - PG_PASSWORD=postgresqlPassword
      - UPLOAD_PATH=/app/uploads
      # JWT 密钥
      - JWT_SECRET=${JWT_SECRET}
      # 跨域资源共享
      - CORS_ORIGIN=http://localhost
      # SMTP 配置 (可选)
      # - SMTP_HOST=smtp.example.com
      # - SMTP_PORT=465
      # - SMTP_USER=user@example.com
      # - SMTP_PASS=password
      # - SMTP_SECURE=true
      # - SMTP_FROM=CarNote 

    volumes:
      # SQList 数据库目录及数据库备份目录
      - ${carnote_data}:/app/data
      # 上传文件目录
      - ${carnote_uploads}:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: [ "CMD", "node", "-e", "require('http').get('http://localhost:53300/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" ]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    networks:
      - carnote-network
  # 数据卷
volumes:
  carnote_data:
    driver: local
  carnote_uploads:
    driver: local
  # postgres_data:
  #   driver: local

  # 网络
networks:
  carnote-network:
    driver: bridge
```

---
*自动采集于 2026-02-11 22:59:49 (北京时间)*
