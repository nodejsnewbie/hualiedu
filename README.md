# Huali Edu 项目

## 简介
本项目为华立教育成绩管理与批量评分系统，基于Django开发，支持多班级、多作业自动登记成绩。

## 目录结构
- grading/         主应用，包含视图、模板、静态资源
- huali_edu/       核心业务逻辑与工具
- hualiEdu/        Django项目配置
- tests/           自动化测试用例
- static/          静态资源（JS/CSS/图片）
- staticfiles/     Django收集的静态文件
- media/           运行时上传/生成文件
- scripts/         自动化脚本
- docs/            项目文档

## 快速开始

### 1. 环境变量配置
本项目使用环境变量保护敏感信息，请先配置环境变量：

```bash
# 方法1：使用自动设置脚本
python scripts/setup_env.py

# 方法2：手动复制并编辑
cp env.example .env
# 然后编辑 .env 文件，填入实际的配置值
```

**重要配置项：**
- `SECRET_KEY`: Django 密钥
- `VOLCENGINE_API_KEY`: 火山引擎 AI API 密钥
- `DEBUG`: 调试模式 (True/False)

### 2. 验证配置
```bash
python scripts/verify_env.py
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
python manage.py migrate
```

### 5. 创建管理员账号
```bash
python manage.py createsuperuser
```

### 6. 启动开发服务器
```bash
python manage.py runserver
```

### 7. 访问应用
访问 http://localhost:8000/

**详细文档请查看 `docs/` 目录：**
- 📚 [文档索引](docs/README.md) - 完整的文档导航
- 🔧 [环境配置](docs/environment.md) - 环境变量和部署配置
- 🤖 [AI评分功能](docs/features/ai-scoring.md) - 智能评分系统
- 📁 [仓库管理](docs/features/repository-management.md) - 用户级仓库管理系统
- 🏢 [多租户系统](docs/features/multi-tenant.md) - 多租户架构
- 📅 [校历功能](docs/features/calendar.md) - 学期和课程管理
- 🔒 [安全指南](docs/security/api-security.md) - API安全最佳实践
- 🧪 [测试指南](docs/testing.md) - 完整的测试框架

## 测试

### 测试结构
```
grading/tests/
├── base.py                  # 测试基类和工具
├── test_models.py           # 模型测试
├── test_views.py            # 视图测试
├── test_forms.py            # 表单测试
├── test_utils.py            # 工具函数测试
├── test_middleware.py       # 中间件测试
├── test_settings.py         # 测试配置
└── test_fixtures.py         # 测试数据固件

tests/
├── test_integration.py      # 集成测试
└── test_utils.py           # 通用工具测试
```

### 运行测试
```bash
# 运行所有测试
python scripts/run_tests.py

# 运行特定类型的测试
python scripts/run_tests.py --type models     # 模型测试
python scripts/run_tests.py --type views      # 视图测试
python scripts/run_tests.py --type forms      # 表单测试
python scripts/run_tests.py --type unit       # 单元测试
python scripts/run_tests.py --type integration # 集成测试

# 高级选项
python scripts/run_tests.py --coverage        # 生成覆盖率报告
python scripts/run_tests.py --verbose         # 详细输出
python scripts/run_tests.py --failfast        # 遇到失败立即停止
python scripts/run_tests.py --parallel 4      # 并行运行

# 原生Django/pytest命令
python manage.py test                          # Django测试
python -m pytest                              # pytest测试
```

### 测试覆盖率
- 模型测试覆盖率: > 90%
- 视图测试覆盖率: > 85%
- 工具函数覆盖率: > 95%
- 总体覆盖率: > 80%

详细测试指南请查看：`docs/testing.md`

## 开发规范

- 代码格式化与检查：使用 black + isort + flake8，并通过 pre-commit 自动校验。
- 安装开发依赖与安装钩子：
  ```bash
  pip install -r requirements-dev.txt
  pre-commit install
  # 首次可对全库执行一遍
  pre-commit run --all-files
  ```

## 部署
- 推荐使用 Docker 部署，见 `Dockerfile` 和 `docker-compose.yml`
- 生产环境请配置环境变量，分离敏感信息

## 常见问题
- **静态文件未加载？**
  - 请运行 `python manage.py collectstatic` 并确保 `STATIC_ROOT` 配置正确
- **数据库迁移失败？**
  - 检查 `migrations/` 目录，尝试 `python manage.py makemigrations` 后再 migrate
- **成绩未写入Excel？**
  - 检查日志输出、文件权限、学生名与Excel一致性

## 贡献
- 欢迎提交PR和Issue，建议先阅读 `docs/project_rules.md`

## 项目维护

### 清理项目文件
```bash
# 清理缓存文件、日志文件和临时文件
python scripts/cleanup.py
```

### 更新依赖
```bash
# 更新requirements.txt
pip-compile requirements.in

# 安装更新的依赖
pip install -r requirements.txt
```

## 其它
- 日志文件默认输出到 logs/ 目录
- 环境变量配置请参考 `.env.example`
