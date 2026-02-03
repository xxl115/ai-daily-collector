# AI Daily Collector - Docker 配置

# 使用 Python 3.12 slim 镜像（更小更快）
FROM python:3.12-slim-bookworm

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/articles /app/data/daily

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data

# 默认命令
CMD ["python", "scripts/daily-ai-workflow.py"]

# 健康检查
HEALTHCHECK --interval=300s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/daily/ai-hotspot-$(date +%Y-%m-%d).md') else 1)"

# 多阶段构建（可选：生产镜像）
# FROM builder AS production
# RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
# FROM python:3.12-slim-bookworm
# COPY --from=install /install /usr/local
# COPY --from=builder /app /app
