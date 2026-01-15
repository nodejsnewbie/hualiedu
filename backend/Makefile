.PHONY: help install sync test runserver migrate makemigrations shell createsuperuser lint format clean check-services ensure-services

# 默认目标 - 显示帮助
.DEFAULT_GOAL := help

help: ## 显示此帮助信息
	@echo "华立教育管理系统 - 后端开发命令"
	@echo ""
	@echo "所有命令都使用 uv 管理 Python 环境"
	@echo ""
	@echo "使用方法: make [目标]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $1, $2}'

# 检查容器服务
check-services: ## 检查 MySQL 和 Redis 容器状态
	@powershell -ExecutionPolicy Bypass -File ../scripts/check-services.ps1

ensure-services: ## 确保容器服务运行（自动启动）
	@powershell -ExecutionPolicy Bypass -File ../scripts/check-services.ps1 -EnsureRunning

# 环境管理
install: ## 安装所有依赖（包括开发依赖）
	@echo "安装项目依赖..."
	@uv sync --all-extras
	@echo "✓ 依赖安装完成"

sync: ## 同步依赖到最新版本
	@echo "同步依赖..."
	@uv sync --upgrade
	@echo "✓ 依赖同步完成"

# 测试相关
test: ## 运行所有测试
	@echo "运行所有测试..."
	@uv run python manage.py test --verbosity=2

test-app: ## 运行指定应用的测试 (使用: make test-app APP=grading)
	@echo "运行 $(APP) 应用的测试..."
	@uv run python manage.py test $(APP) --verbosity=2

test-file: ## 运行指定测试文件 (使用: make test-file FILE=grading.tests.test_models)
	@echo "运行测试文件: $(FILE)"
	@uv run python manage.py test $(FILE) --verbosity=2

test-coverage: ## 运行测试并生成覆盖率报告
	@echo "运行测试并生成覆盖率..."
	@uv run pytest --cov=grading --cov=toolbox --cov-report=html --cov-report=term
	@echo "✓ 覆盖率报告生成在 htmlcov/index.html"

# 开发服务器
runserver: ensure-services ## 启动开发服务器（自动启动容器）
	@echo "启动开发服务器..."
	@uv run python manage.py runserver $(if $(PORT),$(PORT),8000)

runserver-plus: ensure-services ## 启动增强开发服务器（自动启动容器）
	@echo "启动增强开发服务器..."
	@uv run python manage.py runserver_plus $(if $(PORT),$(PORT),8000)

# 数据库相关
migrate: ensure-services ## 应用数据库迁移（自动启动容器）
	@echo "应用数据库迁移..."
	@uv run python manage.py migrate

makemigrations: ## 创建数据库迁移
	@echo "创建数据库迁移..."
	@uv run python manage.py makemigrations

showmigrations: ## 显示迁移状态
	@uv run python manage.py showmigrations

sqlmigrate: ## 显示迁移的 SQL (使用: make sqlmigrate APP=grading NUM=0001)
	@uv run python manage.py sqlmigrate $(APP) $(NUM)

# Django 工具
shell: ensure-services ## 启动 Django shell（自动启动容器）
	@echo "启动 Django shell..."
	@uv run python manage.py shell

shell-plus: ensure-services ## 启动增强 shell（自动启动容器）
	@echo "启动增强 shell..."
	@uv run python manage.py shell_plus

createsuperuser: ensure-services ## 创建超级用户（自动启动容器）
	@echo "创建超级用户..."
	@uv run python manage.py createsuperuser

check: ## 检查项目配置
	@echo "检查项目..."
	@uv run python manage.py check

check-deploy: ## 检查生产环境配置
	@echo "检查生产环境配置..."
	@uv run python manage.py check --deploy

# 代码质量
lint: ## 运行代码检查
	@echo "运行代码检查..."
	@uv run flake8 . --max-line-length=120 --exclude=migrations,.venv,venv,env

format: ## 格式化代码
	@echo "格式化代码..."
	@uv run black . --line-length=100
	@uv run isort . --profile=black --line-length=100
	@echo "✓ 代码格式化完成"

format-check: ## 检查代码格式（不修改）
	@echo "检查代码格式..."
	@uv run black . --line-length=100 --check
	@uv run isort . --profile=black --line-length=100 --check-only

# 静态文件
collectstatic: ## 收集静态文件
	@echo "收集静态文件..."
	@uv run python manage.py collectstatic --noinput

# 清理
clean: ## 清理临时文件
	@echo "清理临时文件..."
	@uv run python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	@uv run python -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	@echo "✓ 清理完成"

clean-all: clean ## 完整清理（包括测试文件和缓存）
	@echo "清理测试文件和缓存..."
	@rm -rf .pytest_cache .coverage htmlcov
	@rm -rf *.egg-info
	@echo "✓ 完整清理完成"

# 自定义管理命令
scan-courses: ensure-services ## 扫描课程目录（自动启动容器）
	@uv run python manage.py scan_courses

import-homeworks: ensure-services ## 导入作业数据（自动启动容器）
	@uv run python manage.py import_homeworks

semester-management: ensure-services ## 学期管理（自动启动容器）
	@uv run python manage.py semester_management

clear-cache: ensure-services ## 清除缓存（自动启动容器）
	@uv run python manage.py clear_cache

# 开发辅助
requirements: ## 导出依赖到 requirements.txt
	@echo "导出依赖..."
	@uv pip compile pyproject.toml -o requirements.txt
	@echo "✓ 依赖已导出到 requirements.txt"

pip-list: ## 列出已安装的包
	@uv pip list

# 数据库备份和恢复
db-backup: ## 备份数据库 (SQLite)
	@echo "备份数据库..."
	@cp db.sqlite3 db.sqlite3.backup-$(shell date +%Y%m%d-%H%M%S)
	@echo "✓ 数据库已备份"

db-reset: ## 重置数据库（危险操作！）
	@echo "警告: 这将删除所有数据！"
	@read -p "确认继续? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f db.sqlite3; \
		uv run python manage.py migrate; \
		echo "✓ 数据库已重置"; \
	fi
