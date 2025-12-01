# 华立教育管理系统 - 文档中心

> **多租户教育平台** - 作业管理、AI评分、课程管理

## 📚 核心文档

### 1. [开发指南](DEVELOPMENT.md)
完整的开发环境配置、技术栈、开发流程和最佳实践。

**包含内容**：
- 环境配置（uv 包管理）
- 技术栈说明
- 开发工作流
- 代码规范
- 测试指南
- 性能优化
- 故障排查

### 2. [部署指南](DEPLOYMENT.md)
生产环境部署、配置和运维指南。

**包含内容**：
- 部署架构
- 环境配置
- 数据库设置
- 静态文件管理
- 安全配置
- 监控和日志
- 备份策略

### 3. [用户手册](USER_MANUAL.md)
系统功能使用说明和操作指南。

**包含内容**：
- 功能概览
- 用户角色
- 作业评分
- 批量登分
- 课程管理
- 学期管理
- 常见问题

## 🚀 快速开始

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
make install

# 3. 初始化数据库
make migrate

# 4. 启动服务器
make runserver
```

详见项目根目录的 [QUICKSTART_UV.md](../QUICKSTART_UV.md)

## 🏗️ 项目架构

### 核心应用
- **grading/** - 评分系统核心
- **toolbox/** - 工具箱模块
- **hualiEdu/** - 项目配置

### 关键特性
- ✅ AI 智能评分（Volcengine Ark SDK）
- ✅ 多租户数据隔离
- ✅ Git/本地双模式仓库
- ✅ 批量登分功能
- ✅ 学期自动管理
- ✅ 缓存性能优化

## 📖 技术文档

### API 参考

所有API需要用户认证，遵循多租户数据隔离。

**通用响应格式**:
```json
// 成功
{"success": true, "message": "操作成功", "data": {...}}

// 失败
{"success": false, "error": "错误信息"}
```

**主要端点**:
- `POST /grading/courses/create/` - 创建课程
- `POST /grading/classes/create/` - 创建班级
- `POST /grading/save_grade/` - 保存评分
- `GET /grading/get_file_content/` - 获取文件内容
- `POST /grading/homework/<id>/batch-grade-to-registry/` - 批量登分

详细API文档请查看代码中的 docstring 或使用 Django REST framework 的自动文档。

### 数据模型
核心模型关系：
```
Tenant → UserProfile, Repository, Submission
User → Course, Repository
Semester → Course
Course → Homework, Class
Repository → Submission
```

## 🔧 开发工具

### 常用命令
```bash
make test              # 运行测试
make format            # 格式化代码
make lint              # 代码检查
make shell             # Django shell
```

### 代码质量
- **Black** - 代码格式化（行长 100）
- **isort** - 导入排序
- **flake8** - 代码检查（行长 120）
- **pytest** - 测试框架

## 📊 性能指标

| 功能 | 性能 |
|------|------|
| 目录文件统计（缓存） | ~50ms |
| 目录树加载（缓存） | ~100ms |
| 文件内容加载（缓存） | ~50ms |
| 批量评分（200文件） | ~30s |

## 🐛 已知问题与限制

### 当前限制
- 单次批量操作建议不超过 200 个文件
- 文件大小限制 50MB
- Git 仓库需要配置 SSH 密钥或 HTTPS 认证

### 常见问题
| 问题 | 解决方案 |
|------|---------|
| 模块未找到 | 运行 `make install` 重新安装依赖 |
| 端口被占用 | 使用 `make runserver PORT=8080` 指定其他端口 |
| 数据库迁移失败 | 检查迁移状态 `uv run python manage.py showmigrations` |
| 静态文件404 | 运行 `uv run python manage.py collectstatic` |

更多问题请查看 [故障排查](DEVELOPMENT.md#故障排查) 章节。

## 🤝 团队协作

### 分支策略
- `main` - 生产环境
- `develop` - 开发环境
- `feature/*` - 功能分支

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 📞 获取帮助

1. 查看相关文档
2. 运行 `make help` 查看命令
3. 查看代码注释和 docstring
4. 联系技术负责人

## 📝 更新日志

查看 [CHANGELOG.md](../CHANGELOG.md) 了解版本历史。

---

**最后更新**: 2024-11-30  
**版本**: 1.0.0  
**维护者**: HualiEdu Team
