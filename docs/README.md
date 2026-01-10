# 华立教育作业管理系统（前后端分离）

## 架构
- 后端：Django + DRF，仅提供 API（不使用模板页面）
- 前端：React + Vite，独立运行
- 默认端口：后端 8000，前端 5173（冲突时会自动切换）

## 目录
- `hualiEdu/` Django 项目配置
- `grading/` 作业与评分相关业务
- `toolbox/` 通用工具
- `frontend/` React 前端
- `docs/` 文档（仅此一个）

## 本地开发
### 后端
1. 安装依赖：`uv sync --all-extras`（或使用已有虚拟环境安装依赖）
2. 运行迁移：`uv run python manage.py migrate`
3. 启动服务：`uv run python manage.py runserver 127.0.0.1:8000`
   - 可选：`make runserver`

后端配置文件为 `.env`，示例见 `env.example`。

### 前端
1. `cd frontend`
2. `npm install`
3. `npm run dev`

前端通过 `frontend/.env` 的 `VITE_API_BASE_URL` 指向后端 API。

## 作业管理（教师）
- 前端“作业管理”支持创建/修改/删除作业，设置截止时间与作业目录。
- 接口路径以 `/grading/api/` 开头。

## 学生提交（Requirement 1.4）
- 学生进入“作业提交”页面后先选择课程，再选择或创建作业目录。
- 新建目录接口：`/grading/api/student/create-directory/`。
- 选定目录后上传文件。

## 常见问题
- 前端无法访问：确认后端运行在 `127.0.0.1:8000`。
- 登录 401：先登录，确认会话正常或后端服务未重启。
- CORS：若更改端口或域名，请同步调整后端 CORS 配置。
