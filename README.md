# 华立教育项目 - 作业评分系统

一个功能完整的多租户教育平台，支持作业管理、智能评分和课程管理。

## 🚀 快速开始

### 环境要求
- Python 3.13（使用 uv 管理）
- Django 4.2.20
- SQLite (开发) / PostgreSQL (生产)

### 安装和运行

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
make install

# 3. 初始化数据库
make migrate

# 4. 启动开发服务器
make runserver
```

**常用命令**：

```bash
make test              # 运行测试
make format            # 格式化代码
make lint              # 代码检查
make clean-all         # 完整清理
make help              # 查看所有命令
```

📖 **完整开发指南**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)  
📖 **快速入门**: [QUICKSTART_UV.md](QUICKSTART_UV.md)

## 📚 项目结构

```
huali-edu/
├── grading/           # 核心应用 - 评分系统
│   ├── services/      # 业务逻辑服务层
│   ├── tests/         # 应用测试
│   └── static/        # 静态资源
├── toolbox/           # 工具箱应用
├── templates/         # 全局模板
├── static/            # 静态文件
├── docs/              # 项目文档
├── tests/             # 集成测试
└── scripts/           # 工具脚本
```

## 🎯 核心功能

### 课程和班级管理
- **课程创建** - 支持理论课、实验课、实践课和混合课
- **班级管理** - 多班级支持，学生名单管理
- **课程类型** - 自动识别和手动配置

### 仓库管理
- **双模式支持** - Git仓库方式和文件系统方式
- **Git集成** - 远程仓库配置、分支管理、SSH认证
- **文件系统** - 本地存储空间分配、目录结构验证
- **学生上传** - 文件系统方式支持学生直接上传作业

### 智能评分系统
- **三种评分方式** - 字母等级(A/B/C/D/E)、文字等级(优秀/良好/中等/及格/不及格)、百分制(0-100)
- **AI辅助评分** - 基于火山引擎Ark SDK的智能评分
- **批量评分** - 支持批量手动评分和批量AI评分
- **实验报告特殊处理** - 自动定位"教师（签字）"单元格，强制评价验证
- **格式验证** - 自动检测实验报告格式，错误时自动降级处理

### 评价功能
- **评价缓存** - 浏览器本地存储，防止意外丢失
- **评价模板** - 个人常用评价和系统推荐评价
- **智能推荐** - 基于使用频率的评价模板推荐
- **自动统计** - 评价使用次数自动累加和排序

### 批量操作
- **批量评分** - 统一评分等级或分数
- **批量AI评分** - 智能批量处理，速率限制保护
- **进度显示** - 实时显示处理进度和状态
- **错误处理** - 单个文件失败不影响整体流程

### 多租户架构
- **数据隔离** - 租户间数据完全隔离
- **权限控制** - 基于角色的访问控制
- **配置管理** - 租户级和全局配置

### 学期管理
- **自动检测** - 基于日期自动识别当前学期
- **模板系统** - 学期模板自动创建
- **状态显示** - 学期状态和时间线可视化

## 🔧 技术栈

- **后端框架**: Django 4.2.20, Python 3.13
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI服务**: 火山引擎 Ark SDK (volcengine 1.0.206)
- **文档处理**: python-docx 1.2.0, openpyxl 3.1.5, pandas 2.3.3
- **版本控制**: GitPython 3.1.45
- **前端**: Bootstrap 5, jQuery, jsTree
- **管理界面**: django-jazzmin 3.0.1
- **代码质量**: black, isort, flake8, pre-commit

## 🛠️ 开发指南

### 代码规范

项目使用 pre-commit 确保代码质量：

```bash
# 格式化代码
make format

# 代码检查
make lint
```

### 测试

```bash
# 运行所有测试
make test

# 运行特定应用测试
make test-app APP=grading

# 运行特定测试文件
uv run python manage.py test grading.tests.test_models --verbosity=2
```

### 数据库管理

```bash
# 创建迁移
make makemigrations

# 应用迁移
make migrate

# 创建超级用户
uv run python manage.py createsuperuser
```

### 自定义管理命令

```bash
# 扫描课程目录
uv run python manage.py scan_courses

# 导入作业数据
uv run python manage.py import_homeworks <仓库路径> <课程名称>

# 学期管理
uv run python manage.py semester_management

# 创建学期模板
uv run python manage.py create_templates

# 更新课程类型
uv run python manage.py update_course_types
```

## 📖 文档

### 主要文档
- **[文档导航](docs/README.md)** - 完整文档索引
- **[开发指南](docs/DEVELOPMENT.md)** - 环境配置、开发流程、测试指南
- **[用户手册](docs/USER_MANUAL.md)** - 系统功能使用说明
- **[快速入门](QUICKSTART_UV.md)** - uv 环境快速配置

### 技术规范
- **[技术栈](.kiro/steering/tech.md)** - 核心技术和命令
- **[项目结构](.kiro/steering/structure.md)** - 目录组织和架构
- **[Django 模式](.kiro/steering/django-patterns.md)** - Django 最佳实践
- **[Python 规范](.kiro/steering/python-conventions.md)** - 代码规范

## 🤝 贡献

我们欢迎所有形式的贡献！

### 贡献方式

1. **报告问题**：在Issues中报告bug或提出功能建议
2. **提交代码**：Fork项目，创建功能分支，提交Pull Request
3. **改进文档**：帮助完善文档和示例
4. **分享经验**：分享使用经验和最佳实践

### 贡献流程

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 Python代码规范
- 使用 black 格式化代码（行长度100）
- 使用 isort 组织导入
- 提交前运行 `make format` 和 `make lint`
- 为新功能编写测试
- 更新相关文档

详细规范请参考：[团队协作指南](docs/TEAM_COLLABORATION.md)

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

## 📞 联系方式

- 项目主页：[GitHub Repository]
- 问题反馈：[GitHub Issues]
- 文档：[docs/README.md](docs/README.md)

## 🔗 相关链接

- [Django 官方文档](https://docs.djangoproject.com/)
- [Python 官方文档](https://docs.python.org/)
- [火山引擎 Ark SDK](https://www.volcengine.com/docs/82379/1099320)