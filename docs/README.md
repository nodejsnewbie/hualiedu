# 华立教育管理系统

> **多租户教育平台** - 作业管理、AI评分、课程管理

## 📚 文档导航

### [开发指南](DEVELOPMENT.md)
完整的开发环境配置、技术栈、开发流程和最佳实践。

**适合：** 开发者、技术人员

### [用户手册](USER_MANUAL.md)
系统功能使用说明和操作指南。

**适合：** 教师、学生、管理员

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

## 🏗️ 核心特性

- ✅ **AI 智能评分** - Volcengine Ark SDK
- ✅ **多租户隔离** - 机构数据完全隔离
- ✅ **作业管理** - Git远程直接访问 / 文件上传
- ✅ **学生自助提交** - 作业次数自动管理
- ✅ **批量登分** - 高效的成绩管理
- ✅ **学期自动管理** - 智能学期检测

## 🔧 常用命令

```bash
make help              # 查看所有命令
make test              # 运行测试
make format            # 格式化代码
make lint              # 代码检查
make clean-all         # 完整清理
```

## 📖 技术栈

- **Python 3.13** - 使用 uv 管理
- **Django 4.2** - Web 框架
- **SQLite / PostgreSQL** - 数据库
- **Hypothesis** - 属性测试
- **Black / isort / flake8** - 代码质量

## 🤝 贡献指南

1. 查看 [开发指南](DEVELOPMENT.md)
2. 遵循代码规范
3. 编写测试
4. 提交 PR

## 📞 获取帮助

1. 查看相关文档
2. 运行 `make help`
3. 联系技术负责人

---

**版本**: 1.0.0  
**最后更新**: 2024-12-02
