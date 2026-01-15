# 贡献指南

感谢你考虑为华立教育作业管理系统做出贡献！

## 行为准则

参与本项目即表示你同意遵守我们的行为准则：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 报告 Bug

在创建 Bug 报告之前，请检查是否已有相关的 Issue。如果没有，请创建新的 Issue 并包含：

- **清晰的标题和描述**
- **重现步骤**
- **预期行为**
- **实际行为**
- **截图**（如果适用）
- **环境信息**（操作系统、Python 版本、Node.js 版本等）

### 建议新功能

如果你有新功能的想法：

1. 检查是否已有相关的 Issue
2. 创建新的 Feature Request Issue
3. 清楚地描述功能和使用场景
4. 解释为什么这个功能对项目有价值

### 提交代码

#### 开发流程

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上 Fork 仓库
   git clone https://github.com/YOUR_USERNAME/hualiedu.git
   cd hualiedu
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **设置开发环境**
   ```bash
   # 后端
   cd backend
   uv sync --all-extras
   cp env.example .env
   # 编辑 .env
   uv run python manage.py migrate
   
   # 前端
   cd ../frontend
   npm install
   ```

4. **进行更改**
   - 编写代码
   - 添加测试
   - 更新文档

5. **运行测试**
   ```bash
   # 在项目根目录
   make test
   
   # 或仅后端测试
   make backend-test
   
   # 或在 backend 目录
   cd backend
   make test
   
   # 代码质量检查
   make format
   make lint
   ```

6. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

7. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 等待代码审查

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构（既不是新功能也不是 Bug 修复）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**范围 (scope)** (可选):
- `backend`: 后端相关
- `frontend`: 前端相关
- `grading`: 评分模块
- `api`: API 相关
- `docs`: 文档
- `deps`: 依赖更新

**示例**:
```
feat(grading): add batch grading support

Add ability to grade multiple submissions at once using AI.
This improves efficiency for teachers with large classes.

Closes #123
```

## 代码规范

### Python (后端)

#### 格式化
```bash
cd backend
make format
```

使用的工具：
- **black**: 代码格式化（line length: 100）
- **isort**: import 排序（profile: black）
- **flake8**: 代码检查（max line length: 120）

#### 命名规范
- 变量/函数: `snake_case`
- 类: `PascalCase`
- 常量: `UPPER_SNAKE_CASE`
- 私有: `_leading_underscore`
- 模型: 单数名词 (`Student`, not `Students`)

#### 导入顺序
```python
# 1. 标准库
import os
from datetime import datetime

# 2. Django
from django.db import models
from django.contrib.auth.models import User

# 3. 第三方库
from rest_framework import serializers

# 4. 本地应用
from grading.models import Student
from grading.services.semester_manager import SemesterManager
```

#### 文档字符串
```python
def calculate_grade(submission: Submission, rubric: dict) -> float:
    """Calculate grade for submission.
    
    Args:
        submission: Student submission to grade
        rubric: Grading criteria
        
    Returns:
        Grade as float (0-100)
        
    Raises:
        ValueError: If rubric invalid
    """
    pass
```

### JavaScript/React (前端)

#### 格式化
- 使用 Prettier（如果配置）
- 2 空格缩进
- 单引号
- 末尾分号

#### 命名规范
- 组件: `PascalCase`
- 函数/变量: `camelCase`
- 常量: `UPPER_SNAKE_CASE`
- 文件名: `PascalCase.jsx` (组件) 或 `camelCase.js` (工具)

### Django 模式

#### 多租户（关键）
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

#### 业务逻辑
- 业务逻辑放在 `services/` 目录
- 视图保持简洁
- 使用服务层处理复杂逻辑

```python
# services/my_service.py
class MyService:
    def process_data(self, data):
        # 业务逻辑
        pass

# views.py
def my_view(request):
    service = MyService()
    result = service.process_data(request.data)
    return JsonResponse(result)
```

## 测试

### 后端测试

#### 运行测试
```bash
cd backend
make test                    # 所有测试
make test-app APP=grading    # 指定应用
make test-file FILE=grading.tests.test_models  # 指定文件
```

#### 编写测试
```python
from django.test import TestCase
from grading.models import Student

class StudentTestCase(TestCase):
    def setUp(self):
        self.student = Student.objects.create(name="Test Student")
    
    def test_student_creation(self):
        self.assertEqual(self.student.name, "Test Student")
    
    def tearDown(self):
        self.student.delete()
```

#### 测试覆盖率
```bash
uv run pytest --cov=grading --cov-report=html
# 查看 htmlcov/index.html
```

### 前端测试

```bash
cd frontend
npm test
```

## 文档

### 更新文档

如果你的更改影响到：
- API 端点 - 更新 API 文档
- 配置选项 - 更新配置文档
- 功能 - 更新用户文档
- 开发流程 - 更新开发文档

### 文档位置
- `README.md` - 项目概述
- `docs/README.md` - 完整文档
- `backend/README.md` - 后端文档
- `CHANGELOG.md` - 更新日志
- `.kiro/steering/` - 开发规范

## Pull Request 流程

### PR 检查清单

在提交 PR 之前，确保：

- [ ] 代码遵循项目的代码规范
- [ ] 已添加必要的测试
- [ ] 所有测试通过
- [ ] 已更新相关文档
- [ ] 提交信息遵循规范
- [ ] PR 描述清晰
- [ ] 已关联相关 Issue

### PR 模板

```markdown
## 描述
简要描述这个 PR 的目的和内容

## 类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 其他

## 相关 Issue
Closes #(issue number)

## 更改内容
- 更改 1
- 更改 2
- 更改 3

## 测试
描述你如何测试这些更改

## 截图（如果适用）
添加截图帮助解释你的更改

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 已添加测试
- [ ] 测试通过
- [ ] 文档已更新
- [ ] 提交信息规范
```

### 代码审查

PR 提交后：
1. 自动运行 CI/CD 检查
2. 至少一位维护者审查代码
3. 根据反馈进行修改
4. 审查通过后合并

## 开发环境

### 推荐工具

- **IDE**: VS Code, PyCharm
- **Git 客户端**: Git CLI, GitHub Desktop
- **API 测试**: Postman, Insomnia
- **数据库**: DBeaver, MySQL Workbench

### VS Code 扩展

- Python
- Pylance
- Django
- ESLint
- Prettier
- GitLens
- Thunder Client

### 环境变量

开发环境使用 `.env` 文件：
```bash
# 后端
cp backend/env.example backend/.env

# 前端
# frontend/.env 已包含默认配置
```

## 获取帮助

如果你需要帮助：

1. 查看 [文档](docs/README.md)
2. 搜索现有的 [Issues](https://github.com/nodejsnewbie/hualiedu/issues)
3. 创建新的 Issue 提问
4. 加入讨论区

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

## 致谢

感谢所有为这个项目做出贡献的人！

---

再次感谢你的贡献！🎉
