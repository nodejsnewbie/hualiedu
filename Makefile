.PHONY: help test runserver migrate makemigrations shell createsuperuser lint format clean

# 默认目标
help:
	@echo "华立教育管理系统 - 开发命令"
	@echo ""
	@echo "所有命令都在 conda py313 环境下执行"
	@echo ""
	@echo "可用命令:"
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
	@echo ""

# 测试相关
test:
	@echo "运行所有测试..."
	@conda run -n py313 python manage.py test --verbosity=2

test-app:
	@echo "运行 $(APP) 应用的测试..."
	@conda run -n py313 python manage.py test $(APP) --verbosity=2

test-file:
	@echo "运行指定测试文件: $(FILE)"
	@conda run -n py313 python manage.py test $(FILE) --verbosity=2

# 开发服务器
runserver:
	@echo "启动开发服务器..."
	@conda run -n py313 python manage.py runserver $(if $(PORT),$(PORT),8000)

# 数据库相关
migrate:
	@echo "应用数据库迁移..."
	@conda run -n py313 python manage.py migrate

makemigrations:
	@echo "创建数据库迁移..."
	@conda run -n py313 python manage.py makemigrations

# Django 工具
shell:
	@echo "启动 Django shell..."
	@conda run -n py313 python manage.py shell

createsuperuser:
	@echo "创建超级用户..."
	@conda run -n py313 python manage.py createsuperuser

# 代码质量
lint:
	@echo "运行代码检查..."
	@conda run -n py313 flake8 . --max-line-length=120 --exclude=migrations,venv,env

format:
	@echo "格式化代码..."
	@conda run -n py313 black . --line-length=100
	@conda run -n py313 isort . --profile=black --line-length=100

# 清理
clean:
	@echo "清理临时文件..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "清理完成"

# 自定义管理命令
scan-courses:
	@echo "扫描课程目录..."
	@conda run -n py313 python manage.py scan_courses

import-homeworks:
	@echo "导入作业数据..."
	@conda run -n py313 python manage.py import_homeworks

semester-management:
	@echo "学期管理..."
	@conda run -n py313 python manage.py semester_management
