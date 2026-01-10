.PHONY: help install sync test runserver migrate makemigrations shell createsuperuser lint format clean

# 默认目标
help:
	@echo "华立教育管理系统 - 开发命令"
	@echo ""
	@echo "所有命令都使用 uv 管理 Python 环境"
	@echo ""
	@echo "环境管理:"
	@echo "  make install           - 安装所有依赖（包括开发依赖）"
	@echo "  make sync              - 同步依赖到最新版本"
	@echo ""
	@echo "开发命令:"
	@echo "  make test              - 运行所有测试"
	@echo "  make test-app APP=grading - 运行指定应用的测试"
	@echo "  make runserver         - 启动开发服务器 (端口 8000)"
	@echo "  make runserver PORT=8080 - 启动开发服务器 (指定端口)"
	@echo "  make migrate           - 应用数据库迁移"
	@echo "  make makemigrations    - 创建数据库迁移"
	@echo "  make shell             - 启动 Django shell"
	@echo "  make createsuperuser   - 创建超级用户"
	@echo "  make lint              - 运行代码检查"
	@echo "  make format            - 格式化代码"
	@echo "  make clean             - 清理临时文件"
	@echo "  make clean-test-dirs   - 清理测试生成的随机目录"
	@echo "  make clean-all         - 完整清理（临时文件 + 测试目录）"
	@echo ""

# 环境管理
install:
	@echo "安装项目依赖（包括开发依赖）..."
	@uv sync --all-extras

sync:
	@echo "同步依赖到最新版本..."
	@uv sync --upgrade

# 测试相关
test:
	@echo "运行所有测试..."
	@uv run python manage.py test --verbosity=2

test-app:
	@echo "运行 $(APP) 应用的测试..."
	@uv run python manage.py test $(APP) --verbosity=2

test-file:
	@echo "运行指定测试文件: $(FILE)"
	@uv run python manage.py test $(FILE) --verbosity=2

# 开发服务器
runserver:
	@echo "Starting development server..."
	@C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev.ps1 services
	@C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path .\\.uv-venv\\Scripts\\python.exe) { & .\\.uv-venv\\Scripts\\python.exe manage.py runserver $(if $(PORT),$(PORT),8000) } elseif (Test-Path .\\.venv\\Scripts\\python.exe) { & .\\.venv\\Scripts\\python.exe manage.py runserver $(if $(PORT),$(PORT),8000) } else { uv run python manage.py runserver $(if $(PORT),$(PORT),8000) }"

# 数据库相关
migrate:
	@echo "应用数据库迁移..."
	@uv run python manage.py migrate

makemigrations:
	@echo "创建数据库迁移..."
	@uv run python manage.py makemigrations

# Django 工具
shell:
	@echo "启动 Django shell..."
	@uv run python manage.py shell

createsuperuser:
	@echo "创建超级用户..."
	@uv run python manage.py createsuperuser

# 代码质量
lint:
	@echo "运行代码检查..."
	@uv run flake8 . --max-line-length=120 --exclude=migrations,venv,env,.venv

format:
	@echo "格式化代码..."
	@uv run black . --line-length=100
	@uv run isort . --profile=black --line-length=100

# 清理
clean:
	@echo "清理临时文件..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "清理完成"

clean-test-dirs:
	@echo "清理测试生成的随机目录..."
	@./scripts/cleanup_test_directories.sh

clean-all: clean clean-test-dirs
	@echo "完整清理完成"

# 自定义管理命令
scan-courses:
	@echo "扫描课程目录..."
	@uv run python manage.py scan_courses

import-homeworks:
	@echo "导入作业数据..."
	@uv run python manage.py import_homeworks

semester-management:
	@echo "学期管理..."
	@uv run python manage.py semester_management

clear-cache:
	@echo "清除缓存..."
	@uv run python manage.py clear_cache
