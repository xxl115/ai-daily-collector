# AI Daily Collector - Makefile
# 简化常用命令

.PHONY: help install install-dev install-poetry run crawl summarize report api test test-cov test-coverage lint lint-flake8 lint-black lint-mypy format format-black format-isort quality check clean docker-build docker-push docker-run docker-compose-up docker-compose-down deploy release precommit precommit-run

# 默认目标
help:
	@echo "🤖 AI Daily Collector - 可用命令:"
	@echo ""
	@echo "📦 安装与配置:"
	@echo "    make install              - 安装依赖"
	@echo "    make install-dev          - 安装开发依赖"
	@echo "    make install-poetry       - 使用 Poetry 安装"
	@echo ""
	@echo "🚀 运行:"
	@echo "    make run                  - 运行完整工作流"
	@echo "    make crawl                - 仅采集文章"
	@echo "    make summarize            - 仅生成总结"
	@echo "    make report               - 仅生成日报"
	@echo "    make api                  - 启动 API 服务"
	@echo "    make dev                  - 开发模式（热重载）"
	@echo ""
	@echo "🧪 测试:"
	@echo "    make test                 - 运行所有测试"
	@echo "    make test-cov             - 运行测试并检查覆盖率"
	@echo "    make test-coverage        - 生成覆盖率报告"
	@echo ""
	@echo "🔧 代码质量:"
	@echo "    make lint                 - 检查所有代码风格"
	@echo "    make lint-flake8          - Flake8 检查"
	@echo "    make lint-black           - Black 检查"
	@echo "    make lint-mypy            - MyPy 类型检查"
	@echo "    make format               - 格式化所有代码"
	@echo "    make format-black         - Black 格式化"
	@echo "    make format-isort         - Import 排序"
	@echo "    make quality              - 运行所有检查"
	@echo "    make check                - 完整质量检查 (lint + test)"
	@echo ""
	@echo "🐳 Docker:"
	@echo "    make docker-build         - 构建 Docker 镜像"
	@echo "    make docker-push          - 推送镜像到仓库"
	@echo "    make docker-run           - 运行 Docker 容器"
	@echo "    make docker-compose-up    - 启动 Docker Compose"
	@echo "    make docker-compose-down  - 停止 Docker Compose"
	@echo ""
	@echo "📤 部署:"
	@echo "    make deploy               - 部署到生产环境"
	@echo "    make release              - 发布新版本"
	@echo ""
	@echo "🔧 工具:"
	@echo "    make precommit            - 安装预提交钩子"
	@echo "    make precommit-run        - 运行预提交检查"
	@echo "    make clean                - 清理缓存文件"
	@echo ""

# 安装
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black mypy pre-commit httpx
	pip install -r requirements-dev.txt 2>/dev/null || true

install-poetry:
	@if ! command -v poetry &> /dev/null; then \
		curl -sSL https://install.python-poetry.org | python3 -; \
	fi
	poetry install --with dev

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
	uvicorn api.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 测试
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=./ --cov-report=term-missing --cov-report=html

test-coverage:
	pytest tests/ --cov=./ --cov-report=xml --cov-report=html
	@echo "📊 覆盖率报告已生成: htmlcov/index.html"

# 代码质量 - 检查
lint: lint-flake8 lint-black lint-mypy

lint-flake8:
	@echo "🔍 Running Flake8..."
	flake8 . --count --show-source --statistics --max-line-length=100

lint-black:
	@echo "🔍 Running Black check..."
	black --check --diff .

lint-mypy:
	@echo "🔍 Running MyPy type check..."
	mypy . --ignore-missing-imports --show-error-codes

# 代码质量 - 格式化
format: format-black format-isort

format-black:
	@echo "🎨 Running Black format..."
	black .

format-isort:
	@echo "🎨 Running isort..."
	isort .

# 完整质量检查
quality: lint test
	@echo ""
	@echo "✅ 所有代码质量检查通过!"

# 完整检查
check: quality
	@echo ""
	@echo "✅ 项目检查全部通过!"

# 清理
clean:
	@echo "🧹 清理缓存文件..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .eggs -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf *.egg-info 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf *.whl 2>/dev/null || true
	@echo "✨ 清理完成!"

# Docker
docker-build:
	@echo "🐳 构建 Docker 镜像..."
	docker build -t ai-daily-collector:latest .

docker-push:
	@echo "📤 推送 Docker 镜像..."
	@read -p "请输入镜像标签版本 (如 0.2.0): " VERSION; \
	echo "VERSION=$$VERSION"; \
	docker tag ai-daily-collector:latest ai-daily-collector:$$VERSION; \
	docker push ai-daily-collector:$$VERSION; \
	docker push ai-daily-collector:latest

docker-run:
	@echo "🚀 启动 Docker 容器..."
	docker run -d --name ai-collector \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/.env:/app/.env:ro \
		-e TZ=Asia/Shanghai \
		-e ZAI_API_KEY=$${ZAI_API_KEY:-} \
		ai-daily-collector:latest

docker-compose-up:
	@echo "🐳 启动 Docker Compose..."
	docker-compose up -d

docker-compose-down:
	@echo "🛑 停止 Docker Compose..."
	docker-compose down

# 部署
deploy:
	@echo "🚀 部署到生产环境..."
	@echo "请确保已配置好以下环境变量:"
	@echo "  - ZAI_API_KEY"
	@echo "  - NOTION_API_KEY (可选)"
	@make docker-build
	@make docker-compose-down
	@make docker-compose-up
	@echo "✅ 部署完成!"

# 发布
release: check
	@echo "🚀 发布新版本..."
	@read -p "请输入版本号 (如 0.2.0): " VERSION; \
	read -p "请输入更新说明: " MESSAGE; \
	echo "VERSION=$$VERSION"; \
	echo "MESSAGE=$$MESSAGE"; \
	git add -A; \
	git commit -m "Release v$$VERSION - $$MESSAGE"; \
	git tag -a v$$VERSION -m "Version $$VERSION"; \
	git push origin master; \
	git push origin v$$VERSION; \
	@echo "✅ 版本 v$$VERSION 已发布!"

# 预提交
precommit:
	@echo "🔧 安装预提交钩子..."
	pre-commit install

precommit-run:
	@echo "🔍 运行预提交检查..."
	pre-commit run --all-files

# 默认目标
all: install test quality
