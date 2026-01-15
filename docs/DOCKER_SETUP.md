# Podman 容器设置指南

本项目使用 Podman 管理 MySQL 和 Redis 容器服务。

## 📋 目录

- [为什么选择 Podman](#为什么选择-podman)
- [安装指南](#安装指南)
- [快速开始](#快速开始)
- [容器管理](#容器管理)
- [故障排查](#故障排查)

## 🐳 为什么选择 Podman

项目固定使用 Podman 而不是 Docker，原因如下：

- **无守护进程架构** - 更安全，资源占用更少
- **Rootless 容器** - 无需 root 权限运行
- **兼容 Docker** - 命令和镜像格式完全兼容
- **开源免费** - Apache 2.0 许可证
- **跨平台支持** - Windows, macOS, Linux

## 📦 安装指南

### Windows

**推荐：Podman Desktop**

```powershell
# 下载并安装 Podman Desktop
# https://podman-desktop.io/downloads/windows

# 安装后初始化 Podman Machine
podman machine init
podman machine start

# 验证安装
podman --version
podman ps
```

### macOS

**推荐：Podman Desktop 或 Homebrew**

```bash
# 选项 1: Podman Desktop
# 下载安装包: https://podman-desktop.io/downloads/macOS

# 选项 2: Homebrew
brew install podman

# 初始化 Podman Machine
podman machine init
podman machine start

# 验证安装
podman --version
podman ps
```

### Linux

**原生支持，无需 Machine**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install podman

# Fedora/RHEL
sudo dnf install podman

# Arch Linux
sudo pacman -S podman

# 验证安装
podman --version
podman ps
```

## 🚀 快速开始

### 1. 启动容器服务

```bash
# 在项目根目录
make services-up
```

这将启动：
- **MySQL 8.0** - 端口 3306
- **Redis 7** - 端口 6379

### 2. 验证服务状态

```bash
# 查看容器状态
make services-status

# 查看日志
make services-logs
```

### 3. 初始化数据库

```bash
# 应用数据库迁移
make backend-migrate

# 创建超级用户
cd backend && make createsuperuser
```

### 4. 启动应用

```bash
# 终端 1 - 后端
make backend-dev

# 终端 2 - 前端
make frontend-dev
```

## 🔧 容器管理

### 基本命令

```bash
# 启动容器
make services-up

# 停止容器
make services-down

# 重启容器
make services-restart

# 查看状态
make services-status

# 查看日志
make services-logs

# 清理容器和数据（危险！）
make services-clean
```

### 直接使用 Podman

#### 启动 Redis

```bash
podman run -d --name huali-redis -p 6379:6379 redis:7-alpine redis-server --appendonly yes
```

#### 启动 MySQL

```bash
podman run -d --name huali-mysql \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=huali_edu \
  -e MYSQL_USER=huali_user \
  -e MYSQL_PASSWORD=HualiUser_2026 \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

## 🔍 故障排查

### 容器无法启动

**问题**: `Cannot connect to Podman/Docker`

**解决方案**:

```bash
# Docker Desktop
# 确保 Docker Desktop 正在运行

# Podman
podman machine list
podman machine start

# 如果没有 machine
podman machine init
podman machine start
```

### 端口被占用

**问题**: `port is already allocated`

**解决方案**:

```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :3306
netstat -ano | findstr :6379

# macOS/Linux
lsof -ti:3306
lsof -ti:6379

# 停止现有容器
make services-down

# 或更改端口（修改 docker-compose.yml）
```

### MySQL 连接失败

**问题**: `Can't connect to MySQL server`

**解决方案**:

```bash
# 1. 检查容器状态
make services-status

# 2. 查看 MySQL 日志
docker logs huali-mysql
# 或
podman logs huali-mysql

# 3. 等待 MySQL 完全启动（首次启动需要时间）
# 查看日志直到看到 "ready for connections"

# 4. 测试连接
docker exec -it huali-mysql mysql -uhuali_user -pHualiUser_2026 huali_edu
# 或
podman exec -it huali-mysql mysql -uhuali_user -pHualiUser_2026 huali_edu
```

### Redis 连接失败

**问题**: `Error connecting to Redis`

**解决方案**:

```bash
# 1. 检查容器状态
make services-status

# 2. 测试 Redis 连接
docker exec -it huali-redis redis-cli ping
# 或
podman exec -it huali-redis redis-cli ping

# 应该返回 PONG
```

### 数据持久化

容器使用命名卷存储数据：

```bash
# 查看卷
docker volume ls | grep huali
# 或
podman volume ls | grep huali

# 备份数据
docker exec huali-mysql mysqldump -uroot -proot_password huali_edu > backup.sql

# 恢复数据
docker exec -i huali-mysql mysql -uroot -proot_password huali_edu < backup.sql
```

### 完全重置

如果遇到无法解决的问题：

```bash
# 1. 停止并删除容器
make services-clean

# 2. 删除卷（会丢失所有数据！）
docker volume rm huali-edu_mysql_data huali-edu_redis_data
# 或
podman volume rm huali-edu_mysql_data huali-edu_redis_data

# 3. 重新启动
make services-up

# 4. 重新初始化数据库
make backend-migrate
cd backend && make createsuperuser
```

## 📝 配置说明

### 环境变量

容器配置在 `backend/.env` 中：

```bash
# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=huali_edu
MYSQL_USER=huali_user
MYSQL_PASSWORD=HualiUser_2026

# Redis 配置
REDIS_URL=redis://127.0.0.1:6379/1
```

### Docker Compose 配置

配置文件：`docker-compose.yml` 或 `podman-compose.yml`

主要配置：
- MySQL 8.0 with utf8mb4
- Redis 7 with AOF persistence
- 数据卷持久化
- 健康检查

## 🎯 最佳实践

### 开发环境

```bash
# 1. 启动容器（只需一次）
make services-up

# 2. 开发时保持容器运行
# 容器会在后台持续运行

# 3. 完成开发后停止
make services-down
```

### 生产环境

生产环境建议使用：
- 托管的 MySQL 服务（如 AWS RDS, Azure Database）
- 托管的 Redis 服务（如 AWS ElastiCache, Azure Cache）
- 或使用 Kubernetes 部署

### 数据备份

```bash
# 定期备份数据库
docker exec huali-mysql mysqldump -uroot -proot_password huali_edu > backup_$(date +%Y%m%d).sql

# 备份 Redis
docker exec huali-redis redis-cli SAVE
docker cp huali-redis:/data/dump.rdb redis_backup_$(date +%Y%m%d).rdb
```

## 🔗 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [Podman 官方文档](https://docs.podman.io/)
- [MySQL Docker 镜像](https://hub.docker.com/_/mysql)
- [Redis Docker 镜像](https://hub.docker.com/_/redis)
- [Docker Compose 文档](https://docs.docker.com/compose/)

---

**提示**: 运行 `make help` 查看所有可用的容器管理命令。
