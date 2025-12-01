# 快速开始 - 使用 uv

> 本项目现在使用 **uv** 进行 Python 包管理，提供更快、更现代的开发体验。

## 前置要求

- Python 3.13+ (uv 会自动管理)
- Git

## 5 分钟快速开始

### 1. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv
```

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd huali-edu
```

### 3. 安装依赖

```bash
# 方式 1: 使用 Makefile (推荐)
make install

# 方式 2: 直接使用 uv
uv sync --all-extras
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# 至少需要设置 SECRET_KEY
```

### 5. 初始化数据库

```bash
# 运行数据库迁移
make migrate

# 创建超级用户
make createsuperuser
```

### 6. 启动开发服务器

```bash
make runserver
```

访问 http://localhost:8000 查看应用！

## 常用命令

```bash
# 开发服务器
make runserver              # 启动服务器 (端口 8000)
make runserver PORT=8080    # 指定端口

# 数据库
make migrate                # 应用迁移
make makemigrations         # 创建迁移

# 测试
make test                   # 运行所有测试
make test-app APP=grading   # 测试指定应用

# 代码质量
make format                 # 格式化代码
make lint                   # 代码检查

# Django 工具
make shell                  # Django shell
make createsuperuser        # 创建超级用户

# 清理
make clean                  # 清理临时文件
```

## 添加新依赖

```bash
# 添加生产依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 示例
uv add requests
uv add --dev pytest
```

## 更新依赖

```bash
# 更新所有依赖到最新版本
make sync

# 或
uv sync --upgrade
```

## 故障排查

### 问题: ModuleNotFoundError

**解决方案**: 确保依赖已安装
```bash
make install
```

### 问题: uv 命令未找到

**解决方案**: 重新安装 uv 或重启终端
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或 ~/.zshrc
```

### 问题: Python 版本不对

**解决方案**: uv 会自动使用正确的 Python 版本
```bash
uv run python --version  # 应该显示 Python 3.13.x
```

## 从 conda 迁移？

如果你之前使用 conda，请查看 [UV 迁移指南](docs/UV_MIGRATION_GUIDE.md)。

## 下一步

- 阅读 [用户手册](docs/USER_MANUAL.md)
- 查看 [API 文档](docs/API.md)
- 了解 [部署指南](docs/DEPLOYMENT.md)

## 获取帮助

```bash
# 查看所有可用命令
make help

# 查看 uv 帮助
uv --help
```

---

**开始编码吧！** 🚀
