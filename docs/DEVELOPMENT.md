# 开发指南

> **完整的开发环境配置、工作流程和最佳实践**

## 📋 目录

- [环境配置](#环境配置)
- [快速开始](#快速开始)
- [开发工作流](#开发工作流)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

## 🛠️ 环境配置

### Python 环境

本项目使用 **uv** 管理 Python 环境和依赖，Python 版本为 **3.13**。

#### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv
```

#### 安装项目依赖

```bash
# 方式 1: 使用 Makefile (推荐)
make install

# 方式 2: 直接使用 uv
uv sync --all-extras
```

#### 验证环境

```bash
# 检查 Python 版本
uv run python --version  # 应该输出: Python 3.13.x

# 检查 Django 版本
uv run python -c "import django; print(django.get_version())"  # 应该输出: 4.2.20

# 运行测试验证
make test
```

## 🚀 快速开始

### 使用 Makefile（推荐）

```bash
# 查看所有可用命令
make help

# 安装依赖
make install

# 初始化数据库
make migrate

# 创建超级用户
make createsuperuser

# 启动开发服务器
make runserver

# 运行测试
make test
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装所有依赖（包括开发依赖） |
| `make sync` | 更新依赖到最新版本 |
| `make runserver` | 启动开发服务器（端口 8000） |
| `make runserver PORT=8080` | 指定端口启动 |
| `make test` | 运行所有测试 |
| `make test-app APP=grading` | 测试指定应用 |
| `make migrate` | 应用数据库迁移 |
| `make makemigrations` | 创建数据库迁移 |
| `make shell` | Django shell |
| `make format` | 格式化代码 |
| `make lint` | 代码检查 |
| `make clean` | 清理临时文件 |
| `make clean-test-dirs` | 清理测试生成的目录 |
| `make clean-all` | 完整清理（包括测试目录） |

## 🔄 开发工作流

### 1. 分支策略

```
main (生产环境)
├── develop (开发环境)
    ├── feature/功能名称
    ├── fix/问题描述
    └── hotfix/紧急修复
```

### 2. 功能开发流程

```bash
# 1. 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature

# 2. 开发代码
# ... 编写代码 ...

# 3. 格式化和检查
make format
make lint

# 4. 运行测试
make test

# 5. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 6. 推送并创建 PR
git push origin feature/your-feature
```

### 3. 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```bash
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具相关
perf: 性能优化
```

**示例**：
```bash
git commit -m "feat: 添加百分制评分功能"
git commit -m "fix: 修复文件上传编码问题"
git commit -m "docs: 更新API文档"
```

## 📝 代码规范

### 代码格式化

项目使用以下工具确保代码一致性：

- **Black**: 代码格式化（行长 100）
- **isort**: 导入排序
- **flake8**: 代码检查（行长 120）

```bash
# 自动格式化
make format

# 代码检查
make lint
```

### 命名规范

```python
# 文件名: lowercase_with_underscores.py
# 类名: PascalCase
class UserProfile:
    pass

# 函数/变量: lowercase_with_underscores
def get_user_data():
    user_name = "test"

# 常量: UPPERCASE_WITH_UNDERSCORES
MAX_RETRY_COUNT = 3

# 私有: _leading_underscore
def _internal_function():
    pass
```

### 文档字符串

```python
def process_grades(student_id: int, grades: List[float]) -> Dict[str, Any]:
    """
    处理学生成绩数据
    
    Args:
        student_id: 学生ID
        grades: 成绩列表
        
    Returns:
        包含处理结果的字典，包括平均分、最高分等
        
    Raises:
        ValueError: 当成绩数据无效时
    """
    pass
```

### 导入顺序

```python
# 1. 标准库
import os
from datetime import datetime

# 2. 第三方库 - Django
from django.db import models
from django.contrib.auth.models import User

# 3. 第三方库 - 其他
from rest_framework import serializers

# 4. 本地应用
from grading.models import Student
from grading.services.semester_manager import SemesterManager
```

## 🧪 测试指南

### 测试结构

```
grading/tests/
├── __init__.py
├── base.py                    # 测试基类
├── test_models.py             # 模型测试
├── test_views.py              # 视图测试
├── test_services.py           # 服务层测试
└── test_integration.py        # 集成测试
```

### 编写测试

```python
from django.test import TestCase
from grading.models import Student

class StudentModelTest(TestCase):
    """学生模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.student = Student.objects.create(
            student_id="2024001",
            name="张三"
        )
    
    def test_student_creation(self):
        """测试学生创建"""
        self.assertEqual(self.student.student_id, "2024001")
        self.assertEqual(self.student.name, "张三")
    
    def tearDown(self):
        """清理测试数据"""
        self.student.delete()
```

### 运行测试

```bash
# 运行所有测试
make test

# 运行指定应用测试
make test-app APP=grading

# 运行指定测试文件
make test-file FILE=grading.tests.test_models

# 详细输出
uv run python manage.py test --verbosity=2

# 生成覆盖率报告
uv run pytest --cov=grading --cov-report=html
```

### 测试目录清理

测试运行时可能在项目根目录产生临时目录，包括：
- 单字符目录（如 `0/`, `A/`）- Hypothesis 生成的随机目录
- 包含控制字符的目录（如 `0ñ\x04`）- 测试代码 bug 产生
- 测试课程目录（如 `其他课程/`, `数据结构/`）

**清理方法**：

```bash
# 方式 1: 使用 Makefile（推荐）
make clean-test-dirs

# 方式 2: 使用 Python 脚本
uv run python scripts/cleanup_test_directories.py

# 方式 3: 预览模式（不实际删除）
uv run python scripts/cleanup_test_directories.py --dry-run
```

**预防措施**：
- Hypothesis 已配置使用系统临时目录（`grading/tests/hypothesis_config.py`）
- 测试代码应使用 `tempfile.TemporaryDirectory()` 或 `tempfile.mkdtemp()`
- 确保 `tearDown()` 方法正确清理临时文件
- 这些目录已在 `.gitignore` 中忽略

### 属性测试（Property-Based Testing）

本项目使用 **Hypothesis** 进行属性测试，自动生成大量测试数据验证代码的通用属性。

**详细文档：** 参见 [Hypothesis Testing Guide](HYPOTHESIS_TESTING.md)

**快速开始：**

```python
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

# 导入共享配置（必须）
from . import hypothesis_config  # noqa: F401

class MyPropertyTest(TestCase):
    @given(name=st.text(min_size=1, max_size=100))
    def test_property(self, name):
        # Hypothesis 会生成各种 name 值进行测试
        result = process_name(name)
        self.assertIsNotNone(result)
```

**运行属性测试：**

```bash
# 使用默认配置（100 examples）
uv run python manage.py test grading.tests.test_assignment_management_service_properties

# 使用开发配置（10 examples，更快）
HYPOTHESIS_PROFILE=dev uv run python manage.py test grading.tests.test_*_properties

# 使用调试配置（5 examples，详细输出）
HYPOTHESIS_PROFILE=debug uv run python manage.py test grading.tests.test_*_properties
```

**注意事项：**
- 属性测试文件命名：`test_*_properties.py`
- 所有属性测试必须导入 `hypothesis_config`
- Hypothesis 数据库存储在系统临时目录，不会污染项目
- 测试生成的随机目录已在 `.gitignore` 中忽略

## ⚡ 性能优化

### 数据库查询优化

```python
# ❌ 错误：N+1 查询
for course in Course.objects.all():
    print(course.teacher.name)  # 每次循环都查询数据库

# ✅ 正确：使用 select_related
courses = Course.objects.select_related('teacher').all()
for course in courses:
    print(course.teacher.name)  # 只查询一次

# ✅ 使用 prefetch_related（多对多/反向外键）
courses = Course.objects.prefetch_related('homeworks').all()
```

### 缓存使用

```python
from grading.cache_manager import get_cache_manager

# 获取缓存管理器
cache_manager = get_cache_manager(request)

# 获取缓存
count = cache_manager.get_file_count("/path/to/dir")
if count is None:
    # 缓存未命中，计算并设置
    count = calculate_file_count("/path/to/dir")
    cache_manager.set_file_count("/path/to/dir", count)
```

### 性能监控

```bash
# 查看慢查询
uv run python manage.py shell
>>> from django.db import connection
>>> print(connection.queries)

# 使用 Django Debug Toolbar（开发环境）
# 在 settings.py 中启用
INSTALLED_APPS += ['debug_toolbar']
```

## 🐛 故障排查

### 常见问题

#### 1. ModuleNotFoundError

**问题**: `ModuleNotFoundError: No module named 'django'`

**解决方案**:
```bash
# 确保依赖已安装
make install

# 或
uv sync --all-extras
```

#### 2. 数据库迁移错误

**问题**: 迁移冲突或失败

**解决方案**:
```bash
# 查看迁移状态
uv run python manage.py showmigrations

# 回滚迁移
uv run python manage.py migrate grading 0001

# 重新应用
make migrate
```

#### 3. 静态文件404

**问题**: 静态文件无法加载

**解决方案**:
```bash
# 收集静态文件
uv run python manage.py collectstatic --noinput

# 检查 settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### 4. 端口被占用

**问题**: `Error: That port is already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
make runserver PORT=8080
```

### 调试技巧

```python
# 1. 使用 pdb 调试
import pdb; pdb.set_trace()

# 2. 使用 Django shell
make shell
>>> from grading.models import Student
>>> Student.objects.all()

# 3. 查看日志
tail -f logs/app.log

# 4. 使用 print 调试（临时）
import logging
logger = logging.getLogger(__name__)
logger.debug(f"变量值: {variable}")
```

## 🔧 IDE 配置

### VS Code

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. 打开 Settings/Preferences
2. Project > Python Interpreter
3. 选择项目的 `.venv` 环境
4. 配置 Black 和 isort 作为外部工具

## 📚 项目结构

```
huali-edu/
├── grading/              # 核心应用
│   ├── services/         # 业务逻辑层
│   ├── tests/            # 测试
│   ├── models.py         # 数据模型
│   ├── views.py          # 视图
│   └── urls.py           # 路由
├── toolbox/              # 工具箱应用
├── docs/                 # 文档
├── static/               # 静态文件
├── media/                # 用户上传
├── pyproject.toml        # 项目配置
├── Makefile              # 开发命令
└── manage.py             # Django 管理
```

详见 [项目结构文档](PROJECT_STRUCTURE.md)

## 🤝 团队协作

### 代码审查

**PR 检查清单**:
- [ ] 代码符合规范（运行 `make format` 和 `make lint`）
- [ ] 包含必要的测试
- [ ] 文档已更新
- [ ] 没有敏感信息
- [ ] 测试通过（运行 `make test`）

### 沟通协作

- **日常沟通**: 及时分享进度和问题
- **技术讨论**: 重要决策需要团队讨论
- **代码分享**: 定期分享有趣的代码和技巧

## 📖 参考资源

- [Django 官方文档](https://docs.djangoproject.com/)
- [uv 文档](https://docs.astral.sh/uv/)
- [Python PEP 8](https://pep8.org/)
- [项目技术栈](.kiro/steering/tech.md)
- [UV 迁移指南](UV_MIGRATION_GUIDE.md)

## 🎯 最佳实践

1. **使用 Makefile** - 简化命令，统一工作流
2. **提交前检查** - 运行 `make format` 和 `make test`
3. **编写测试** - 新功能必须有测试覆盖
4. **及时沟通** - 遇到问题及时求助
5. **文档同步** - 代码变更时更新文档
6. **代码审查** - 认真对待每次审查
7. **持续学习** - 关注新技术和最佳实践

---

**开始编码吧！** 🚀

如有问题，运行 `make help` 查看所有可用命令。
