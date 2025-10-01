# 教师评分系统 Makefile
# 所有命令都在py313环境中执行

.PHONY: help install runserver test migrate shell clean check-env

# 默认目标
help:
	@echo "教师评分系统 - 可用命令:"
	@echo ""
	@echo "环境管理:"
	@echo "  check-env     检查py313环境状态"
	@echo "  install       安装/更新依赖"
	@echo ""
	@echo "开发服务器:"
	@echo "  runserver     启动Django开发服务器"
	@echo "  shell         打开Django shell"
	@echo ""
	@echo "数据库:"
	@echo "  migrate       运行数据库迁移"
	@echo "  makemigrations 创建数据库迁移"
	@echo ""
	@echo "测试:"
	@echo "  test          运行所有测试"
	@echo "  test-semester 测试学期管理器"
	@echo "  test-unit     运行单元测试"
	@echo ""
	@echo "维护:"
	@echo "  clean         清理临时文件"
	@echo "  format        格式化代码"
	@echo ""

# 环境管理
check-env:
	@echo "检查py313环境状态..."
	@python run_in_env.py python --version
	@python run_in_env.py python -c "import django; print(f'Django版本: {django.get_version()}')"

install:
	@echo "安装/更新依赖..."
	@python run_in_env.py pip install -r requirements.txt

# 开发服务器
runserver:
	@echo "启动Django开发服务器..."
	@python manage_py313.py runserver

shell:
	@echo "打开Django shell..."
	@python manage_py313.py shell

# 数据库
migrate:
	@echo "运行数据库迁移..."
	@python manage_py313.py migrate

makemigrations:
	@echo "创建数据库迁移..."
	@python manage_py313.py makemigrations

# 测试
test:
	@echo "运行所有测试..."
	@python manage_py313.py test

test-semester:
	@echo "测试学期管理器..."
	@python test_py313.py test_semester_manager_simple.py

test-unit:
	@echo "运行学期管理器单元测试..."
	@python test_py313.py grading.tests.test_semester_manager

test-auto-creator:
	@echo "运行学期自动创建器测试..."
	@python test_py313.py grading.tests.test_semester_auto_creator

test-detector:
	@echo "运行学期检测器测试..."
	@python test_py313.py grading.tests.test_semester_detector

test-status:
	@echo "测试学期状态功能..."
	@python test_py313.py test_semester_status.py

test-integration:
	@echo "运行集成测试..."
	@python test_py313.py grading.tests.test_semester_integration

# 维护
clean:
	@echo "清理临时文件..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -delete
	@rm -rf htmlcov/
	@rm -f .coverage

format:
	@echo "格式化代码..."
	@python run_in_env.py black .
	@python run_in_env.py isort .

# 快速启动
dev: migrate runserver

# 完整测试套件
test-all: test-semester test-unit test-auto-creator test-detector test-status test-integration

# 项目初始化
init: check-env install migrate
	@echo "项目初始化完成！"
	@echo "运行 'make runserver' 启动开发服务器"
