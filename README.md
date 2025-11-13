# 华立教育项目

## 🚀 快速开始

### 环境要求
- Python 3.13 (conda py313环境)
- Django 4.2.20

### 安装和运行

**重要**: 所有命令必须在 conda py313 环境下执行

```bash
# 推荐: 使用 Makefile（最简单）
make runserver          # 启动开发服务器
make test              # 运行测试
make migrate           # 数据库迁移

# 或使用辅助脚本
./scripts/runserver.sh  # 启动开发服务器
./scripts/test.sh       # 运行测试

# 或手动激活环境
conda activate py313
python manage.py runserver
```

📖 **完整开发指南**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 📚 项目结构

```
huali-edu/
├── grading/           # 核心应用 - 评分系统
├── toolbox/           # 工具箱应用
├── templates/         # 全局模板
├── static/            # 静态文件
├── docs/              # 项目文档
├── tests/             # 测试文件
└── scripts/           # 工具脚本
```

## 🎯 核心功能

- **智能评分系统** - AI驱动的作业评分
- **多租户架构** - 支持多个教育机构
- **仓库管理** - Git和本地仓库管理
- **学期管理** - 自动学期检测和状态显示
- **批量处理** - 批量评分和文档处理

## 🔧 技术栈

- **后端**: Django 4.2.20, Python 3.13
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI服务**: 火山引擎 Ark SDK
- **文件处理**: python-docx, openpyxl, pandas
- **版本控制**: GitPython
- **前端**: Bootstrap + Django Crispy Forms

## 🛠️ 开发指南

### 代码规范
项目使用 pre-commit 确保代码质量：
```bash
# 安装 pre-commit 钩子
pre-commit install

# 手动运行检查
black . --line-length=100
isort . --profile=black
flake8 .
```

### 测试
```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test grading.tests.test_models
```

### 环境管理
项目支持多种环境管理方式：
- direnv (推荐)
- conda-project
- VS Code 集成

## 📖 文档

### 开发文档
- **[开发指南](docs/DEVELOPMENT.md)** - 环境配置、开发流程、常用命令
- **[项目结构](docs/PROJECT_STRUCTURE.md)** - 目录结构和代码组织
- **[团队协作](docs/TEAM_COLLABORATION.md)** - Git工作流、代码审查、协作规范

### 功能文档
- **[功能文档索引](docs/README.md)** - 完整功能文档和设计文档
- **[快速参考](docs/SUMMARY.md)** - 核心概念速查
- **[已知问题](docs/KNOWN_ISSUES.md)** - 问题追踪和修复记录

## 🤝 贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。