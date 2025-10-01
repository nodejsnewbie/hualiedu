# 测试指南

## 概述

本项目采用Django单元测试最佳实践，提供全面的测试覆盖，包括模型、视图、表单、工具函数和中间件测试。

## 测试结构

```
grading/tests/
├── __init__.py              # 测试包初始化
├── base.py                  # 测试基类和通用工具
├── test_models.py           # 模型测试
├── test_views.py            # 视图测试
├── test_forms.py            # 表单测试
├── test_utils.py            # 工具函数测试
├── test_middleware.py       # 中间件测试
├── test_settings.py         # 测试专用设置
└── test_fixtures.py         # 测试数据固件

tests/
├── __init__.py
├── test_integration.py      # 集成测试
└── test_utils.py           # 通用工具测试
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **模型测试**: 测试数据模型的创建、验证、方法等
- **表单测试**: 测试表单验证、清理、保存等
- **工具函数测试**: 测试独立的工具函数
- **中间件测试**: 测试中间件逻辑

### 2. 视图测试 (View Tests)
- **URL路由测试**: 测试URL映射
- **权限测试**: 测试访问控制
- **响应测试**: 测试HTTP响应
- **模板测试**: 测试模板渲染

### 3. 集成测试 (Integration Tests)
- **工作流测试**: 测试完整的业务流程
- **API测试**: 测试API接口
- **文件操作测试**: 测试文件上传下载

## 运行测试

### 基本命令

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行Django测试
python manage.py test

# 运行pytest测试
python -m pytest
```

### 按类型运行

```bash
# 运行模型测试
python scripts/run_tests.py --type models

# 运行视图测试
python scripts/run_tests.py --type views

# 运行表单测试
python scripts/run_tests.py --type forms

# 运行单元测试
python scripts/run_tests.py --type unit

# 运行集成测试
python scripts/run_tests.py --type integration
```

### 高级选项

```bash
# 详细输出
python scripts/run_tests.py --verbose

# 生成覆盖率报告
python scripts/run_tests.py --coverage

# 遇到失败立即停止
python scripts/run_tests.py --failfast

# 并行运行测试
python scripts/run_tests.py --parallel 4

# 指定测试文件模式
python scripts/run_tests.py --pattern "*model*"
```

## 测试基类

### BaseTestCase
提供通用的测试设置和工具方法：

```python
from grading.tests.base import BaseTestCase

class MyTest(BaseTestCase):
    def test_something(self):
        # 自动创建的测试用户
        self.user
        self.admin_user
        self.teacher_user

        # 登录用户
        self.login_user()

        # 创建测试文件
        test_file = self.create_test_file('test.txt', '内容')

        # 断言方法
        self.assertResponseOK(response)
        self.assertResponseRedirect(response)
```

### APITestCase
专门用于API测试：

```python
from grading.tests.base import APITestCase

class MyAPITest(APITestCase):
    def test_api_endpoint(self):
        response = self.api_get('/api/endpoint/')
        self.assertJSONResponse(response, {'status': 'ok'})
```

### MockTestCase
提供Mock功能：

```python
from grading.tests.base import MockTestCase

class MyMockTest(MockTestCase):
    def test_with_mock(self):
        # Mock火山引擎API
        mock_api = self.mock_volcengine_api(return_value=(85, "好评"))

        # 测试代码
        result = some_function()

        # 验证Mock调用
        mock_api.assert_called_once()
```

## 测试数据

### 使用固件创建测试数据

```python
from grading.tests.test_fixtures import TestDataFixtures

class MyTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # 创建完整测试数据
        self.test_data = TestDataFixtures.create_full_test_data()

        # 或创建特定数据
        self.users = TestDataFixtures.create_test_users()
        self.tenants = TestDataFixtures.create_test_tenants()
```

### 手动创建测试数据

```python
def test_with_custom_data(self):
    # 创建租户
    tenant = Tenant.objects.create(name='测试租户')

    # 创建用户配置文件
    profile = UserProfile.objects.create(
        user=self.user,
        tenant=tenant
    )
```

## Mock和补丁

### Mock外部API

```python
@patch('grading.views.volcengine_score_homework')
def test_ai_scoring(self, mock_ai):
    mock_ai.return_value = (85, "评分结果")

    # 测试代码
    response = self.client.post('/ai-score/', {'content': '测试内容'})

    # 验证
    self.assertEqual(response.status_code, 200)
    mock_ai.assert_called_once_with('测试内容')
```

### Mock文件操作

```python
@patch('builtins.open', mock_open(read_data='文件内容'))
@patch('os.path.exists', return_value=True)
def test_file_operation(self, mock_exists):
    # 测试文件读取
    result = read_file('/path/to/file')
    self.assertEqual(result, '文件内容')
```

### Mock数据库操作

```python
@patch('grading.models.Student.objects.create')
def test_student_creation(self, mock_create):
    mock_create.return_value = MagicMock(id=1, name='测试学生')

    # 测试代码
    student = create_student('测试学生')

    # 验证
    self.assertEqual(student.name, '测试学生')
```

## 断言方法

### 响应断言

```python
# 成功响应
self.assertResponseOK(response)

# 重定向响应
self.assertResponseRedirect(response, '/expected/url/')

# 禁止访问
self.assertResponseForbidden(response)

# 未找到
self.assertResponseNotFound(response)
```

### 内容断言

```python
# 包含内容
self.assertContains(response, '期望的文本')

# 不包含内容
self.assertNotContains(response, '不应该出现的文本')

# JSON响应
self.assertJSONResponse(response, {'key': 'value'})
```

### 数据库断言

```python
# 对象存在
self.assertTrue(Student.objects.filter(name='张三').exists())

# 对象数量
self.assertEqual(Student.objects.count(), 5)

# 字段值
student = Student.objects.get(name='张三')
self.assertEqual(student.class_name, '计算机1班')
```

## 测试配置

### 测试设置文件
`grading/tests/test_settings.py` 包含测试专用配置：

- 使用内存数据库加快测试速度
- 禁用缓存和日志
- 简化密码哈希
- 设置测试API密钥

### 环境变量
测试时会自动设置以下环境变量：

```bash
DJANGO_SETTINGS_MODULE=hualiEdu.settings
ARK_API_KEY=test-api-key
ARK_MODEL=test-model
```

## 覆盖率报告

### 生成覆盖率报告

```bash
# HTML报告
python scripts/run_tests.py --coverage

# 查看报告
open htmlcov/index.html
```

### 覆盖率目标
- 模型测试覆盖率: > 90%
- 视图测试覆盖率: > 85%
- 工具函数覆盖率: > 95%
- 总体覆盖率: > 80%

## 持续集成

### 预提交钩子
项目配置了pre-commit钩子，会在提交前运行：

```bash
# 安装钩子
pre-commit install

# 手动运行
pre-commit run --all-files
```

### GitHub Actions
`.github/workflows/test.yml` 配置了自动化测试：

- 在多个Python版本上运行测试
- 生成覆盖率报告
- 检查代码质量

## 调试测试

### 调试失败的测试

```bash
# 详细输出
python manage.py test --verbosity=2

# 保留测试数据库
python manage.py test --keepdb

# 运行特定测试
python manage.py test grading.tests.test_models.StudentModelTest.test_create_student
```

### 使用pdb调试

```python
def test_something(self):
    import pdb; pdb.set_trace()
    # 测试代码
```

### 查看SQL查询

```python
from django.test.utils import override_settings
from django.db import connection

@override_settings(DEBUG=True)
def test_with_sql_logging(self):
    # 测试代码
    print(connection.queries)
```

## 最佳实践

### 1. 测试命名
- 使用描述性的测试方法名
- 遵循 `test_<功能>_<条件>_<期望结果>` 格式

```python
def test_create_student_with_valid_data_should_succeed(self):
def test_create_student_with_duplicate_id_should_fail(self):
```

### 2. 测试组织
- 每个模型/视图/表单一个测试类
- 相关测试方法放在同一个类中
- 使用setUp和tearDown管理测试数据

### 3. 测试数据
- 使用固件创建可重用的测试数据
- 每个测试应该独立，不依赖其他测试
- 使用有意义的测试数据

### 4. Mock使用
- 只Mock外部依赖，不Mock被测试的代码
- 验证Mock的调用参数和次数
- 使用patch装饰器而不是手动Mock

### 5. 断言
- 使用具体的断言方法而不是assertTrue
- 提供有意义的断言消息
- 一个测试方法测试一个功能点

## 常见问题

### Q: 测试运行很慢怎么办？
A:
- 使用内存数据库
- 并行运行测试
- 减少不必要的数据创建

### Q: 如何测试需要登录的视图？
A:
```python
def test_protected_view(self):
    self.login_user()  # 使用基类方法
    response = self.client.get('/protected/')
    self.assertResponseOK(response)
```

### Q: 如何测试文件上传？
A:
```python
def test_file_upload(self):
    test_file = self.create_test_file('test.txt', '内容')
    response = self.client.post('/upload/', {'file': test_file})
    self.assertResponseOK(response)
```

### Q: 如何测试异步任务？
A:
```python
from django.test import override_settings

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_async_task(self):
    # 测试异步任务
    pass
```

## 参考资源

- [Django测试文档](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest-django文档](https://pytest-django.readthedocs.io/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)
- [coverage.py文档](https://coverage.readthedocs.io/)
