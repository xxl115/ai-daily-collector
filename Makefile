# AI Daily Collector - Makefile
# 简化常用命令

.PHONY: help install test run lint format clean docker deploy

# 默认目标
help:
	@echo "🤖 AI Daily Collector - 可用命令:"
	@echo ""
	@echo "  📦 安装与配置:"
	@echo "    make install      - 安装依赖"
	@echo "    make install-dev  - 安装开发依赖"
	@echo ""
	@echo "  🚀 运行:"
	@echo "    make run          - 运行完整工作流"
	@echo "    make crawl        - 仅采集文章"
	@echo "    make summarize    - 仅生成总结"
	@echo "    make report       - 仅生成日报"
	@echo "    make api          - 启动 API 服务"
	@echo ""
	@echo "  🧪 测试:"
	@echo "    make test         - 运行所有测试"
	@echo "    make test-cov     - 运行测试并检查覆盖率"
	@echo ""
	@echo "  🔧 代码质量:"
	@echo "    make lint         - 检查代码风格"
	@echo "    make format       - 自动格式化代码"
	@echo "    make check        - 运行所有检查"
	@echo ""
	@echo "  🐳 Docker:"
	@echo "    make docker-build - 构建 Docker 镜像"
	@echo "    make docker-run   - 运行 Docker 容器"
	@echo "    make docker-compose-up  - 启动 Docker Compose"
	@echo "    make docker-compose-down - 停止 Docker Compose"
	@echo ""
	@echo "  📤 部署:"
	@echo "    make deploy       - 部署到生产环境"
	@echo ""

# 安装
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black mypy pre-commit

# 运行完整工作流
run:
	python scripts/daily-ai-workflow.py

# 分步骤运行
crawl:
	python scripts/ai-hotspot-crawler-simple.py

summarize:
	python scripts/summarize-articles.py

report:
	python scripts/generate-daily-report.py

# API 服务
api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 测试
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=./ --cov-report=html --cov-report=term

# 代码质量
lint:
	flake8 . --count --show-source --statistics

format:
	black . --diff

check: lint test
	@echo "✅ 所有检查通过!"

# Docker
docker-build:
	docker build -t ai-daily-collector:latest .

docker-run:
	docker run -d --name ai-collector \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/.env:/app/.env:ro \
		-e TZ=Asia/Shanghai \
		ai-daily-collector:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# 清理
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "🧹 清理完成!"

# 部署
deploy:
	@echo "🚀 部署到生产环境..."
	@echo "请确保已配置好环境变量和 Docker"
	@make docker-build
	@make docker-compose-down
	@make docker-compose-up
	@echo "✅ 部署完成!"
