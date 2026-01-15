# 华立教育后端 API

Django + DRF 后端服务，提供作业管理、AI 评分和多租户支持。

## 技术栈

- **Python**: 3.13
- **Django**: 4.2.20
- **Django REST Framework**: 3.16.0
- **数据库**: SQLite (开发) / MySQL (生产)
- **AI SDK**: Volcengine Ark Runtime
- **缓存**: Redis / LocMem

## 快速开始

### 1. 安装依赖
```bash
uv sync --all-extras
```

### 2. 配置环境
```bash
cp env.example .env
# 编辑 .env 文件
```

### 3. 数据库迁移
```bash
uv run python manage.py migrate
```

### 4. 创建超级用户
```bash
uv run python manage.py createsuperuser
```

### 5. 启动服务
```bash
make runserver
# 或
uv run python manage.py runserver
```

## 项目结构

```
backend/
├── grading/              # 核心应用
│   ├── models.py         # 数据模型
│   ├── views.py          # 视图函数
│   ├── api_views.py      # API 视图
│   ├── admin.py          # 管理后台
│   ├── services/         # 业务逻辑
│   ├── tests/            # 测试
│   └── management/       # 管理命令
├── toolbox/              # 工具应用
├── hualiEdu/             # 项目配置
│   ├── settings.py       # 设置
│   ├── urls.py           # 路由
│   └── middleware.py     # 中间件
├── media/                # 上传文件
├── static/               # 静态文件
├── logs/                 # 日志
└── pyproject.toml        # 依赖配置
```

## 核心模型

### Tenant (租户)
- 机构级别的数据隔离
- 独立配置和权限

### Repository (仓库)
- Git 仓库或本地路径
- 学生代码提交

### Submission (提交)
- 学生作业提交
- 关联评分和评论

### Semester (学期)
- 学期管理
- 自动检测和创建

### Course (课程)
- 课程信息
- 课程安排

### Homework (作业)
- 作业定义
- 截止时间和要求

## API 端点

### 认证
- `POST /admin/login/` - 管理员登录
- `GET /admin/logout/` - 登出

### 作业管理
- `GET /grading/api/homeworks/` - 作业列表
- `POST /grading/api/homeworks/` - 创建作业
- `PUT /grading/api/homeworks/{id}/` - 更新作业
- `DELETE /grading/api/homeworks/{id}/` - 删除作业

### 学生提交
- `POST /grading/api/student/create-directory/` - 创建目录
- `POST /grading/api/student/upload/` - 上传文件

### 评分
- `POST /grading/api/grade/batch/` - 批量评分
- `GET /grading/api/grade/export/` - 导出成绩

## 开发命令

### Makefile 命令（推荐）

查看所有可用命令：
```bash
make help
```

#### 常用命令
```bash
# 环境管理
make install           # 安装所有依赖
make sync              # 同步依赖到最新版本

# 开发服务器
make runserver         # 启动服务器（端口 8000）
make runserver PORT=8080  # 指定端口

# 数据库
make migrate           # 应用迁移
make makemigrations    # 创建迁移
make showmigrations    # 显示迁移状态

# 测试
make test              # 运行所有测试
make test-app APP=grading  # 运行指定应用测试
make test-file FILE=grading.tests.test_models  # 运行指定文件
make test-coverage     # 生成覆盖率报告

# 代码质量
make format            # 格式化代码（black + isort）
make format-check      # 检查格式（不修改）
make lint              # 代码检查（flake8）
make check             # 检查项目配置
make check-deploy      # 检查生产环境配置

# Django 工具
make shell             # Django shell
make createsuperuser   # 创建超级用户
make collectstatic     # 收集静态文件

# 清理
make clean             # 清理临时文件
make clean-all         # 完整清理（包括测试缓存）
```

### 自定义管理命令
```bash
make scan-courses          # 扫描课程目录
make import-homeworks      # 导入作业数据
make semester-management   # 学期管理
make clear-cache           # 清除缓存

# 或直接使用
uv run python manage.py scan_courses
uv run python manage.py import_homeworks
```

## 配置

### 环境变量 (.env)

#### 必需配置
```bash
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 数据库（可选）
```bash
# 不配置则使用 SQLite
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=huali_edu
MYSQL_USER=huali_user
MYSQL_PASSWORD=your_password
```

#### AI 评分
```bash
ARK_API_KEY=your_ark_api_key
ARK_MODEL=deepseek-r1-250528
```

#### 缓存（可选）
```bash
REDIS_URL=redis://127.0.0.1:6379/1
```

#### CORS
```bash
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOW_CREDENTIALS=True
```

## 多租户架构

### 中间件
`MultiTenantMiddleware` 自动设置：
- `request.tenant` - 当前租户
- `request.user_profile` - 用户配置

### 数据隔离
所有租户相关模型必须：
```python
class MyModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'grading_mymodel'
```

查询时必须过滤租户：
```python
MyModel.objects.filter(tenant=request.tenant)
```

## 业务逻辑层

业务逻辑放在 `services/` 目录：

```python
# grading/services/semester_manager.py
class SemesterManager:
    def auto_update_current_semester(self):
        # 业务逻辑
        pass
```

视图保持简洁：
```python
def my_view(request):
    manager = SemesterManager()
    result = manager.auto_update_current_semester()
    return JsonResponse(result)
```

## 测试

### 运行测试
```bash
# 所有测试
make test

# 指定应用
make test-app APP=grading

# 指定文件
make test-file FILE=grading.tests.test_models

# 详细输出
uv run python manage.py test --verbosity=2
```

### 测试结构
```
grading/tests/
├── __init__.py
├── base.py              # 基础测试类
├── test_models.py       # 模型测试
├── test_views.py        # 视图测试
└── test_services.py     # 服务测试
```

## 代码质量

### 格式化
```bash
make format
# 或
uv run black . --line-length=100
uv run isort . --profile=black --line-length=100
```

### 检查
```bash
make lint
# 或
uv run flake8 . --max-line-length=120
```

### Pre-commit
```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## 日志

日志配置在 `settings.py`：
- 控制台输出
- 文件输出: `logs/app.log`
- 级别: DEBUG, INFO, WARNING, ERROR

使用方式：
```python
import logging
logger = logging.getLogger(__name__)

logger.info("操作成功")
logger.error("操作失败", exc_info=True)
```

## 部署

### 生产环境检查
```bash
uv run python manage.py check --deploy
```

### 收集静态文件
```bash
uv run python manage.py collectstatic --noinput
```

### 使用 Gunicorn
```bash
uv run gunicorn hualiEdu.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

### 环境变量（生产）
```bash
DEBUG=False
ALLOWED_HOSTS=your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## 故障排查

### AI 评分不可用
```bash
# 检查依赖
uv sync --all-extras

# 验证 SDK
uv run python -c "from volcenginesdkarkruntime import Ark; print('OK')"
```

### 数据库连接失败
- SQLite: 确保没有配置 MYSQL_DATABASE
- MySQL: 检查服务状态和凭据

### CORS 错误
检查 `.env` 中的 CORS_ALLOWED_ORIGINS

## 开发规范

详见项目根目录 `.kiro/steering/` 下的规范文档：
- `tech.md` - 技术栈和命令
- `structure.md` - 项目结构
- `python-conventions.md` - Python 规范
- `django-patterns.md` - Django 模式
- `product.md` - 产品概述

## 许可证

MIT License
