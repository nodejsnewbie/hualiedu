# 更新日志

## [2026-01-15] - 服务启动优化和 Podman 标准化

### 新增功能

#### 自动服务检查和启动
- ✅ 添加 `make check-services` - 检查 MySQL 和 Redis 容器状态
- ✅ 添加 `make ensure-services` - 自动启动未运行的容器
- ✅ `make backend-dev` 现在会自动检查并启动容器服务
- ✅ 所有需要数据库的命令（migrate, shell, createsuperuser 等）都会自动启动容器

#### 跨平台脚本支持
- ✅ 创建 `scripts/check-services.ps1` - Windows PowerShell 脚本
- ✅ 创建 `scripts/check-services.sh` - Linux/macOS Bash 脚本
- ✅ Makefile 自动检测操作系统并使用对应脚本

#### 容器管理标准化
- ✅ **固定使用 Podman** - 不再支持 Docker
- ✅ 如果系统没有 Podman，脚本会报错并提示安装
- ✅ Windows/macOS 自动检查 Podman Machine 状态
- ✅ 容器启动失败时提供清晰的错误信息

### 删除的文件
- ❌ `docker-compose.yml` - 不再使用 Docker Compose
- ❌ `podman-compose.yml` - 直接使用 Podman CLI
- ❌ `scripts/start-services.ps1` - 被 check-services.ps1 替代
- ❌ `scripts/stop-services.ps1` - 功能已集成到 Makefile

### 改进

#### Makefile 优化
- ✅ 根目录 Makefile 添加服务检查功能
- ✅ 后端 Makefile 所有数据库相关命令依赖 `ensure-services`
- ✅ 简化了容器启动流程，`make services-up` 现在调用 `ensure-services`

#### 前端配置修复
- ✅ 修复 Tailwind CSS v4 配置问题
- ✅ 安装 `@tailwindcss/postcss` 插件
- ✅ 更新 PostCSS 配置使用新的插件
- ✅ 更新 CSS 导入语法为 `@import "tailwindcss"`

#### 文档更新
- ✅ README.md - 更新环境要求，说明只使用 Podman
- ✅ DOCKER_SETUP.md - 重命名为 Podman 设置指南
- ✅ 添加 Podman 安装说明（Windows, macOS, Linux）
- ✅ 更新所有文档中的容器相关说明

### 技术细节

#### 服务检查逻辑
```bash
# 检查容器是否运行
podman ps --filter name=huali-mysql --filter status=running

# 如果容器存在但未运行，启动它
podman start huali-mysql

# 如果容器不存在，创建并启动
podman run -d --name huali-mysql ...
```

#### 跨平台兼容性
- Windows: 使用 PowerShell 脚本 (.ps1)
- Linux/macOS: 使用 Bash 脚本 (.sh)
- Makefile 通过 `powershell` 或 `bash` 命令调用对应脚本

### 使用示例

#### 启动开发环境（推荐方式）
```bash
# 一键启动后端（自动检查并启动容器）
make backend-dev

# 一键启动前端
make frontend-dev
```

#### 手动管理容器
```bash
# 检查容器状态
make check-services

# 确保容器运行
make ensure-services

# 启动容器
make services-up

# 停止容器
make services-down

# 查看容器状态
make services-status
```

### 破坏性变更

⚠️ **不再支持 Docker**
- 项目现在固定使用 Podman
- 如果系统只有 Docker，需要安装 Podman
- 原因：Podman 更安全、更轻量、完全开源

### 迁移指南

如果你之前使用 Docker：

1. 安装 Podman Desktop: https://podman-desktop.io/downloads
2. 停止并删除 Docker 容器：
   ```bash
   docker stop huali-mysql huali-redis
   docker rm huali-mysql huali-redis
   ```
3. 启动 Podman Machine（Windows/macOS）：
   ```bash
   podman machine init
   podman machine start
   ```
4. 使用 Makefile 启动容器：
   ```bash
   make services-up
   ```

### 已知问题

- Windows 上 Makefile 的 bash 语法不兼容，已通过 PowerShell 脚本解决
- 文件编码问题可能导致中文显示异常，已使用英文输出

---

## [2026-01-15] - 初始版本

### 项目设置
- ✅ 修复 Volcengine Ark SDK 依赖问题
- ✅ 添加缺失的依赖包
- ✅ 修复 CORS 配置冲突
- ✅ 完善 env.example 文件

### 文档
- ✅ 创建完整的项目文档结构
- ✅ 删除冗余文档
- ✅ 创建核心文档（README, CONTRIBUTING, LICENSE）

### Makefile
- ✅ 重写根目录和后端 Makefile
- ✅ 添加 40+ 实用命令
- ✅ 自动生成帮助系统
- ✅ 跨平台兼容

### 容器化
- ✅ 使用 Podman 管理容器
- ✅ MySQL 8.0 和 Redis 7 配置
- ✅ 数据持久化和健康检查
- ✅ 跨平台脚本支持（PowerShell 和 Bash）
