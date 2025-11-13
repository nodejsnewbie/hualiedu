# 团队协作最佳实践指南

## 📋 目录
- [环境配置](#环境配置)
- [代码规范](#代码规范)
- [Git 工作流](#git-工作流)
- [依赖管理](#依赖管理)
- [代码审查](#代码审查)
- [文档规范](#文档规范)
- [测试规范](#测试规范)
- [部署流程](#部署流程)

## 🛠️ 环境配置

**详细的环境配置指南请参考**: [开发指南](./DEVELOPMENT.md)

快速开始：
```bash
# 1. 激活 Python 环境
conda activate py313

# 2. 安装依赖和配置
pip install -r requirements.txt
pre-commit install
cp .env.example .env
```

## 📝 代码规范

### 代码格式化
项目使用以下工具确保代码一致性：

```bash
# 自动格式化代码
black . --line-length=100
isort . --profile=black --line-length=100

# 检查代码质量
flake8 . --max-line-length=120
```

### 命名规范
- **文件名**: 使用小写字母和下划线 `user_profile.py`
- **类名**: 使用驼峰命名 `UserProfile`
- **函数/变量**: 使用小写字母和下划线 `get_user_data()`
- **常量**: 使用大写字母和下划线 `MAX_RETRY_COUNT`

### 代码注释
```python
def process_student_grades(student_id: int, grades: List[float]) -> Dict[str, Any]:
    """
    处理学生成绩数据
    
    Args:
        student_id: 学生ID
        grades: 成绩列表
        
    Returns:
        包含处理结果的字典
        
    Raises:
        ValueError: 当成绩数据无效时
    """
    pass
```

## 🔄 Git 工作流

### 分支策略
```
main (生产环境)
├── dev (开发环境)
    ├── feature/user-authentication
    ├── feature/grade-calculation
    └── hotfix/critical-bug-fix
```

### 提交规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```bash
# 功能开发
git commit -m "feat: 添加学生成绩计算功能"

# 问题修复
git commit -m "fix: 修复成绩导出时的编码问题"

# 文档更新
git commit -m "docs: 更新API文档"

# 代码重构
git commit -m "refactor: 优化数据库查询性能"
```

### 工作流程
1. **创建功能分支**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **开发和提交**
   ```bash
   # 开发代码...
   git add .
   git commit -m "feat: 描述你的功能"
   ```

3. **推送和创建 PR**
   ```bash
   git push origin feature/your-feature-name
   # 在 GitHub/GitLab 创建 Pull Request
   ```

## 📦 依赖管理

### 添加新依赖
```bash
# 1. 安装新包
pip install package-name

# 2. 更新 requirements.txt
pip freeze | grep package-name >> requirements.txt

# 3. 如果是开发依赖，添加到 requirements-dev.txt
```

### 依赖更新
```bash
# 定期更新依赖
pip list --outdated
pip install --upgrade package-name

# 更新 requirements 文件
pip freeze > requirements.txt
```

## 👀 代码审查

### PR 检查清单
- [ ] 代码符合项目规范
- [ ] 包含必要的测试
- [ ] 文档已更新
- [ ] 没有敏感信息泄露
- [ ] 性能影响已评估
- [ ] 向后兼容性已考虑

### 审查原则
- **建设性反馈**: 提供具体的改进建议
- **及时响应**: 24小时内完成审查
- **学习态度**: 把审查当作学习机会
- **代码质量**: 关注可读性、性能和安全性

## 📚 文档规范

### API 文档
```python
# 使用 Django REST Framework 的文档功能
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(
    operation_description="获取学生成绩",
    responses={200: "成功返回成绩数据"}
)
@api_view(['GET'])
def get_student_grades(request, student_id):
    pass
```

### README 更新
保持 README.md 包含：
- 项目简介
- 安装步骤
- 使用方法
- 贡献指南

## 🧪 测试规范

### 测试结构
```
tests/
├── unit/           # 单元测试
├── integration/    # 集成测试
└── fixtures/       # 测试数据
```

### 测试命名
```python
def test_calculate_grade_average_with_valid_scores():
    """测试使用有效分数计算平均成绩"""
    pass

def test_calculate_grade_average_with_empty_scores():
    """测试空分数列表的处理"""
    pass
```

### 运行测试
```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test grading.tests.test_models

# 生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
```

## 🚀 部署流程

### 环境部署
1. **开发环境**: 自动部署 `dev` 分支
2. **测试环境**: 手动部署 `dev` 分支
3. **生产环境**: 手动部署 `main` 分支

### 部署检查清单
- [ ] 数据库迁移已执行
- [ ] 静态文件已收集
- [ ] 环境变量已配置
- [ ] 服务健康检查通过
- [ ] 回滚方案已准备

## 🔧 开发工具推荐

### IDE 配置
**VS Code 推荐插件**:
- Python
- Django
- GitLens
- Prettier
- ESLint

**PyCharm 配置**:
- 启用 Django 支持
- 配置代码格式化工具
- 设置测试运行器

### 调试工具
```python
# 使用 Django Debug Toolbar
INSTALLED_APPS = [
    'debug_toolbar',
]

# 使用 pdb 调试
import pdb; pdb.set_trace()
```

## 📞 沟通协作

### 日常沟通
- **每日站会**: 分享进度和阻碍
- **技术讨论**: 重要决策需要团队讨论
- **代码分享**: 定期分享有趣的代码片段

### 问题报告
使用 Issue 模板报告问题：
```markdown
## 问题描述
简要描述遇到的问题

## 复现步骤
1. 步骤一
2. 步骤二
3. 步骤三

## 期望结果
描述期望的行为

## 实际结果
描述实际发生的情况

## 环境信息
- Python 版本:
- Django 版本:
- 操作系统:
```

## 🎯 最佳实践总结

1. **保持代码简洁**: 遵循 DRY 原则
2. **及时沟通**: 遇到问题及时求助
3. **持续学习**: 关注新技术和最佳实践
4. **代码审查**: 认真对待每次代码审查
5. **文档维护**: 及时更新相关文档
6. **测试驱动**: 编写测试保证代码质量
7. **安全意识**: 注意数据安全和隐私保护

---

## 📖 相关资源

- [Django 官方文档](https://docs.djangoproject.com/)
- [Python PEP 8 风格指南](https://pep8.org/)
- [Git 工作流指南](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [代码审查最佳实践](https://google.github.io/eng-practices/review/)

**记住**: 好的协作不仅仅是技术问题，更是团队文化的体现。让我们一起创造一个高效、友好的开发环境！