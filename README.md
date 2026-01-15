# 华立教育作业管理系统

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2.20-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19.2.3-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

多租户教育平台，提供作业管理、AI 智能评分和课程管理功能。

## ✨ 核心特性

- 🏢 **多租户架构** - 机构级数据隔离和独立配置
- 🤖 **AI 智能评分** - 集成火山引擎 Ark SDK
- 📚 **作业管理** - 完整的作业生命周期管理
- 🔄 **仓库管理** - 支持 Git 和本地文件系统
- 📅 **学期管理** - 自动检测和创建学期
- 📊 **成绩导出** - 多种格式的成绩报表

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- uv (Python 包管理器)
- **Podman**（容器管理，用于 MySQL 和 Redis）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/nodejsnewbie/hualiedu.git
cd hualiedu

# 2. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或 Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. 安装 Podman
# Windows/macOS: 下载 Podman Desktop from https://podman-desktop.io/downloads
# Linux: sudo apt install podman (Ubuntu/Debian) 或 sudo dnf install podman (Fedora/RHEL)

# 4. 启动 Podman machine (Windows/macOS)
podman machine init
podman machine start

# 5. 启动容器服务（MySQL + Redis）
make services-up

# 6. 后端设置
cd backend
uv sync --all-extras
cp env.example .env
# 编辑 .env 配置必要的环境变量
uv run python manage.py migrate
uv run python manage.py createsuperuser

# 7. 前端设置
cd ../frontend
npm install
```

### 启动服务

```bash
# 方式 1: 使用根目录 Makefile（推荐）
# 终端 1 - 容器服务（首次或重启后）
make services-up

# 终端 2 - 后端
make backend-dev

# 终端 3 - 前端
make frontend-dev

# 方式 2: 在各自目录中启动
# 终端 1 - 容器服务
make services-up

# 终端 2 - 后端
cd backend && make runserver

# 终端 3 - 前端
cd frontend && npm run dev
```

访问：
- 前端: http://127.0.0.1:5173
- 后端 API: http://127.0.0.1:8000
- 管理后台: http://127.0.0.1:8000/admin

## 📖 文档

- [后端文档](backend/README.md) - API 和架构说明
- [容器设置](docs/DOCKER_SETUP.md) - Docker/Podman 配置指南
- [Makefile 指南](docs/MAKEFILE_GUIDE.md) - 开发命令使用指南
- [贡献指南](CONTRIBUTING.md) - 如何参与贡献
- [更新日志](CHANGELOG.md) - 版本历史

## 🏗️ 技术栈

**后端**: Django 4.2.20 + DRF 3.16.0 + Python 3.13  
**前端**: React 19.2.3 + Vite 7.2.4 + Tailwind CSS 4.1.18  
**数据库**: SQLite (开发) / MySQL (生产)  
**AI**: Volcengine Ark SDK  
**包管理**: uv + npm

## 📁 项目结构

```
huali-edu/
├── backend/              # Django 后端
│   ├── grading/         # 核心应用
│   ├── toolbox/         # 工具应用
│   └── hualiEdu/        # 项目配置
├── frontend/            # React 前端
├── .kiro/steering/      # 开发规范
└── docs/                # 文档
```

## 🔧 常用命令

所有命令都支持通过 Makefile 执行。在项目根目录运行 `make help` 查看所有可用命令。

### 快速开始

```bash
# 安装所有依赖（前端 + 后端）
make install

# 启动开发环境（需要两个终端）
# 终端 1
make backend-dev

# 终端 2
make frontend-dev
```

### 后端命令

```bash
make backend-help       # 查看所有后端命令
make backend-install    # 安装后端依赖
make backend-dev        # 启动开发服务器
make backend-test       # 运行测试
make backend-format     # 格式化代码
make backend-lint       # 代码检查
make backend-migrate    # 数据库迁移
```

### 前端命令

```bash
make frontend-install   # 安装前端依赖
make frontend-dev       # 启动开发服务器
make frontend-build     # 生产构建
make frontend-preview   # 预览构建
```

### 其他命令

```bash
make test               # 运行所有测试
make clean              # 清理临时文件
```

### 直接使用（在对应目录）

```bash
# 后端（在 backend/ 目录）
cd backend
make help               # 查看所有命令
make runserver          # 启动服务器
make test               # 运行测试
make format             # 格式化代码
make shell              # Django shell

# 前端（在 frontend/ 目录）
cd frontend
npm run dev             # 开发服务器
npm run build           # 生产构建
npm test                # 运行测试
```

## 🔐 环境配置

### 后端 (.env)

```bash
SECRET_KEY=your_secret_key
DEBUG=True
ARK_API_KEY=your_ark_api_key  # AI 评分
ARK_MODEL=deepseek-r1-250528

# 数据库（可选，默认 SQLite）
MYSQL_DATABASE=huali_edu
MYSQL_USER=huali_user
MYSQL_PASSWORD=your_password
```

### 前端 (.env)

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 🧪 测试

```bash
# 后端
cd backend
make test

# 前端
cd frontend
npm test
```

## 📦 部署

```bash
# 1. 设置生产环境变量
DEBUG=False
ALLOWED_HOSTS=your-domain.com
SECURE_SSL_REDIRECT=True

# 2. 收集静态文件
cd backend
uv run python manage.py collectstatic

# 3. 使用 Gunicorn
uv run gunicorn hualiEdu.wsgi:application --bind 0.0.0.0:8000

# 4. 构建前端
cd frontend
npm run build
```

## ❓ 常见问题

### AI 评分不可用？
```bash
uv sync --all-extras
uv run python -c "from volcenginesdkarkruntime import Ark; print('OK')"
```

### 数据库连接失败？
- 确保容器服务已启动: `make services-status`
- 启动容器: `make services-up`
- 查看容器日志: `make services-logs`
- 详见 [容器设置指南](docs/DOCKER_SETUP.md)

### CORS 错误？
检查 `backend/.env` 中的 `CORS_ALLOWED_ORIGINS` 配置

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

### 代码规范

- Python: black (line length 100), isort, flake8
- 提交前运行: `make format && make lint`
- 遵循 Conventional Commits

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史。

### 最新版本 [1.0.0] - 2026-01-15

- ✅ 多租户架构
- ✅ AI 智能评分
- ✅ 作业管理系统
- ✅ 修复 Ark SDK 依赖问题
- ✅ 优化 CORS 配置

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📧 联系

- **仓库**: https://github.com/nodejsnewbie/hualiedu
- **问题**: [GitHub Issues](https://github.com/nodejsnewbie/hualiedu/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
