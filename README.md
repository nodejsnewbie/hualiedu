# Huali Edu 项目

## 简介
本项目为华立教育成绩管理与批量评分系统，后端基于 Django，前端使用 React。
后端仅提供 API，模板页面已移除。

## 目录结构
- grading/         主应用（API、业务逻辑）
- hualiEdu/        Django 项目配置
- frontend/        React 前端（Vite）
- tests/           自动化测试用例
- static/          静态资源（JS/CSS/图片）
- staticfiles/     Django 收集的静态文件
- media/           运行时上传/生成文件
- scripts/         自动化脚本
- docs/            项目文档

## 快速开始

### 1. 环境变量配置
```bash
cp env.example .env
# PowerShell
Copy-Item env.example .env
```

主要配置项：
- `SECRET_KEY`: Django 密钥
- `ARK_API_KEY`: 火山引擎 AI API 密钥
- `DEBUG`: 调试模式 (True/False)

### 2. 安装依赖
```bash
uv sync
```

### 3. 初始化数据库
```bash
uv run python manage.py migrate
```

### 4. 创建管理员账号
```bash
uv run python manage.py createsuperuser
```

### 5. 启动后端
```bash
uv run python manage.py runserver
```
后端默认地址：`http://localhost:8000/`（根路径为健康检查）

### 6. 启动前端
```bash
cd frontend
npm install
npm run dev
```
前端默认地址：`http://localhost:5173/`

### Makefile（可选）
```bash
make runserver
```
Windows 无 make 时可使用 `scripts/dev.ps1`。

## 文档
- 文档索引：`docs/README.md`
- 环境与变量说明：`docs/environment.md`
- 前端开发说明：`docs/frontend.md`
- 开发规范：`docs/DEVELOPMENT.md`

## 测试
```bash
uv run python -m unittest discover tests
```
