# Makefile 使用指南

本项目使用 Makefile 简化开发流程，提供统一的命令接口。

## 📋 目录

- [快速开始](#快速开始)
- [根目录命令](#根目录命令)
- [后端命令](#后端命令)
- [前端命令](#前端命令)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

## 🚀 快速开始

### 查看帮助

```bash
# 根目录 - 查看所有命令
make help

# 后端目录 - 查看后端命令
cd backend && make help
```

### 首次设置

```bash
# 1. 安装所有依赖（前端 + 后端）
make install

# 2. 启动容器服务（MySQL + Redis）
make services-up

# 3. 配置环境变量
cd backend && cp env.example .env
# 编辑 .env 文件

# 4. 数据库迁移
make backend-migrate

# 5. 创建超级用户
cd backend && make createsuperuser

# 6. 启动开发环境（需要两个终端）
# 终端 1
make backend-dev

# 终端 2
make frontend-dev
```

## 📦 根目录命令

在项目根目录运行这些命令。

### 环境管理

```bash
make install              # 安装所有依赖（前端 + 后端）
```

### 开发

```bash
make dev                  # 显示如何启动开发环境
make backend-dev          # 启动后端开发服务器
make frontend-dev         # 启动前端开发服务器
```

### 测试

```bash
make test                 # 运行所有测试（前端 + 后端）
make backend-test         # 仅运行后端测试
```

### 清理

```bash
make clean                # 清理所有临时文件
```

### 后端快捷命令

```bash
make backend-help         # 显示后端帮助
make backend-install      # 安装后端依赖
make backend-migrate      # 应用数据库迁移
make backend-format       # 格式化后端代码
make backend-lint         # 检查后端代码
```

### 前端快捷命令

```bash
make frontend-install     # 安装前端依赖
make frontend-build       # 构建前端生产版本
make frontend-preview     # 预览前端构建
```

## 🐍 后端命令

在 `backend/` 目录运行这些命令。

### 环境管理

```bash
make install              # 安装所有依赖（包括开发依赖）
make sync                 # 同步依赖到最新版本
make pip-list             # 列出已安装的包
make requirements         # 导出依赖到 requirements.txt
```

### 开发服务器

```bash
make runserver            # 启动开发服务器（默认端口 8000）
make runserver PORT=8080  # 启动开发服务器（指定端口）
```

### 数据库

```bash
make migrate              # 应用数据库迁移
make makemigrations       # 创建数据库迁移
make showmigrations       # 显示迁移状态
make sqlmigrate APP=grading NUM=0001  # 显示迁移的 SQL
make db-backup            # 备份数据库（SQLite）
make db-reset             # 重置数据库（危险操作！）
```

### 测试

```bash
make test                 # 运行所有测试
make test-app APP=grading # 运行指定应用的测试
make test-file FILE=grading.tests.test_models  # 运行指定测试文件
make test-coverage        # 运行测试并生成覆盖率报告
```

### 代码质量

```bash
make format               # 格式化代码（black + isort）
make format-check         # 检查代码格式（不修改）
make lint                 # 运行代码检查（flake8）
make check                # 检查项目配置
make check-deploy         # 检查生产环境配置
```

### Django 工具

```bash
make shell                # 启动 Django shell
make createsuperuser      # 创建超级用户
make collectstatic        # 收集静态文件
```

### 清理

```bash
make clean                # 清理临时文件（__pycache__, *.pyc）
make clean-all            # 完整清理（包括测试缓存）
```

### 自定义管理命令

```bash
make scan-courses         # 扫描课程目录
make import-homeworks     # 导入作业数据
make semester-management  # 学期管理
make clear-cache          # 清除缓存
```

## ⚛️ 前端命令

在 `frontend/` 目录运行这些命令。

```bash
npm install               # 安装依赖
npm run dev               # 启动开发服务器
npm run build             # 构建生产版本
npm run preview           # 预览构建
npm test                  # 运行测试
```

或在根目录使用 Makefile：

```bash
make frontend-install     # 安装依赖
make frontend-dev         # 启动开发服务器
make frontend-build       # 构建生产版本
make frontend-preview     # 预览构建
```

## 💡 最佳实践

### 日常开发流程

```bash
# 1. 拉取最新代码
git pull

# 2. 确保容器服务运行
make services-status
# 如果未运行，启动它们
make services-up

# 3. 同步依赖
cd backend && make sync

# 4. 应用迁移
make migrate

# 5. 启动开发服务器
make runserver
```

### 提交代码前

```bash
# 1. 格式化代码
make format

# 2. 检查代码
make lint

# 3. 运行测试
make test

# 4. 检查项目配置
make check
```

### 添加新功能

```bash
# 1. 创建迁移
make makemigrations

# 2. 应用迁移
make migrate

# 3. 运行测试
make test

# 4. 格式化代码
make format
```

### 生产部署前

```bash
# 1. 检查生产环境配置
make check-deploy

# 2. 运行所有测试
make test

# 3. 收集静态文件
make collectstatic

# 4. 备份数据库
make db-backup
```

## 🔧 故障排查

### 命令找不到

**问题**: `make: command not found`

**解决方案**:
- Windows: 安装 Make（通过 Chocolatey: `choco install make`）
- macOS: 已预装
- Linux: `sudo apt-get install make` 或 `sudo yum install make`

### uv 命令失败

**问题**: `uv: command not found`

**解决方案**:
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 依赖安装失败

**问题**: `make install` 失败

**解决方案**:
```bash
# 清理并重新安装
cd backend
make clean-all
make install
```

### 测试失败

**问题**: 测试运行失败

**解决方案**:
```bash
# 1. 确保数据库迁移已应用
make migrate

# 2. 清理测试缓存
make clean-all

# 3. 重新运行测试
make test
```

### 端口被占用

**问题**: `Error: That port is already in use.`

**解决方案**:
```bash
# 使用不同端口
make runserver PORT=8080

# 或查找并关闭占用端口的进程
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

## 📚 参考

### Makefile 语法

- `.PHONY`: 声明伪目标（不是文件）
- `@`: 不显示命令本身，只显示输出
- `$(VAR)`: 引用变量
- `$(if condition,then,else)`: 条件判断

### 常用变量

- `APP`: 应用名称（用于 test-app）
- `FILE`: 测试文件路径（用于 test-file）
- `PORT`: 服务器端口（用于 runserver）
- `NUM`: 迁移编号（用于 sqlmigrate）

### 示例

```bash
# 使用变量
make test-app APP=grading
make runserver PORT=8080
make sqlmigrate APP=grading NUM=0001

# 链式命令
make format && make lint && make test
```

## 🎯 快速参考

### 最常用命令

```bash
# 开发
make backend-dev          # 启动后端
make frontend-dev         # 启动前端

# 测试
make test                 # 运行测试

# 代码质量
make format               # 格式化
make lint                 # 检查

# 数据库
make migrate              # 迁移
```

### 完整工作流

```bash
# 1. 首次设置
make install
make services-up
cd backend && cp env.example .env
make backend-migrate
cd backend && make createsuperuser

# 2. 日常开发
make services-status        # 检查容器
make backend-dev            # 终端 1
make frontend-dev           # 终端 2

# 3. 提交前
make format && make lint && make test

# 4. 停止服务
# Ctrl+C 停止前后端
make services-down          # 停止容器（可选）
```

---

**提示**: 运行 `make help` 或 `cd backend && make help` 查看所有可用命令。
