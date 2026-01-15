.PHONY: help install dev test clean backend frontend services

# 默认目标 - 显示帮助
.DEFAULT_GOAL := help

help: ## 显示此帮助信息
	@echo "华立教育作业管理系统 - 开发命令"
	@echo ""
	@echo "使用方法: make [目标]"
	@echo ""
	@echo "主要命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "容器服务:"
	@echo "  make services-up       启动 MySQL 和 Redis 容器"
	@echo "  make services-down     停止容器"
	@echo "  make services-logs     查看容器日志"
	@echo "  make services-status   查看容器状态"
	@echo ""
	@echo "后端命令 (在 backend/ 目录):"
	@echo "  make backend-help      查看所有后端命令"
	@echo "  make backend-install   安装后端依赖"
	@echo "  make backend-dev       启动后端开发服务器"
	@echo "  make backend-test      运行后端测试"
	@echo "  make backend-format    格式化后端代码"
	@echo ""
	@echo "前端命令 (在 frontend/ 目录):"
	@echo "  make frontend-install  安装前端依赖"
	@echo "  make frontend-dev      启动前端开发服务器"
	@echo "  make frontend-build    构建前端生产版本"

install: ## 安装所有依赖（前端 + 后端）
	@echo "安装后端依赖..."
	@cd backend && uv sync --all-extras
	@echo "安装前端依赖..."
	@cd frontend && npm install
	@echo "✓ 所有依赖安装完成"

dev: ## 显示如何启动完整开发环境
	@echo "启动完整开发环境需要 3 个步骤:"
	@echo ""
	@echo "1. 启动容器服务 (MySQL + Redis):"
	@echo "   make services-up"
	@echo ""
	@echo "2. 启动后端 (新终端):"
	@echo "   make backend-dev"
	@echo ""
	@echo "3. 启动前端 (新终端):"
	@echo "   make frontend-dev"

# 检查容器是否运行
.PHONY: check-services ensure-services

check-services: ## 检查容器服务状态
	@powershell -ExecutionPolicy Bypass -File scripts/check-services.ps1

ensure-services: ## 确保容器服务运行（自动启动）
	@powershell -ExecutionPolicy Bypass -File scripts/check-services.ps1 -EnsureRunning

# 容器服务管理
services-up: ## 启动 MySQL 和 Redis 容器
	@$(MAKE) ensure-services

services-down: ## 停止容器服务
	@powershell -ExecutionPolicy Bypass -File scripts/manage-services.ps1 -Action stop

services-restart: ## 重启容器服务
	@powershell -ExecutionPolicy Bypass -File scripts/manage-services.ps1 -Action restart

services-logs: ## 查看容器日志
	@powershell -ExecutionPolicy Bypass -File scripts/manage-services.ps1 -Action logs

services-status: ## 查看容器状态
	@powershell -ExecutionPolicy Bypass -File scripts/manage-services.ps1 -Action status

services-clean: ## 清理容器和数据卷（危险操作！）
	@powershell -ExecutionPolicy Bypass -File scripts/manage-services.ps1 -Action clean

test: ## 运行所有测试
	@echo "运行后端测试..."
	@cd backend && uv run python manage.py test --verbosity=2
	@echo "运行前端测试..."
	@cd frontend && npm test

clean: ## 清理所有临时文件
	@echo "清理后端临时文件..."
	@cd backend && $(MAKE) clean
	@echo "清理前端临时文件..."
	@cd frontend && rm -rf node_modules/.cache dist
	@echo "✓ 清理完成"

# 后端命令
backend-help: ## 显示后端帮助
	@cd backend && $(MAKE) help

backend-install: ## 安装后端依赖
	@cd backend && $(MAKE) install

backend-dev: ensure-services ## 启动后端开发服务器（自动启动容器）
	@cd backend && $(MAKE) runserver

backend-test: ## 运行后端测试
	@cd backend && $(MAKE) test

backend-migrate: ## 应用数据库迁移
	@cd backend && $(MAKE) migrate

backend-format: ## 格式化后端代码
	@cd backend && $(MAKE) format

backend-lint: ## 检查后端代码
	@cd backend && $(MAKE) lint

# 前端命令
frontend-install: ## 安装前端依赖
	@cd frontend && npm install

frontend-dev: ## 启动前端开发服务器
	@cd frontend && npm run dev

frontend-build: ## 构建前端生产版本
	@cd frontend && npm run build

frontend-preview: ## 预览前端构建
	@cd frontend && npm run preview

# 快捷方式（向后兼容）
backend: ## 转发到后端 Makefile
	@cd backend && $(MAKE) $(filter-out $@,$(MAKECMDGOALS))

frontend: ## 转发到前端目录
	@cd frontend && npm $(filter-out $@,$(MAKECMDGOALS))

%:
	@:

