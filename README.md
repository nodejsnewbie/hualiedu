# Huali Edu 项目

## 简介
本项目为华立教育成绩管理与批量评分系统，基于Django开发，支持多班级、多作业自动登记成绩。

## 目录结构
- grading/         主应用，包含视图、模板、静态资源
- huali_edu/       核心业务逻辑与工具
- hualiEdu/        Django项目配置
- tests/           自动化测试用例
- static/          静态资源（JS/CSS/图片）
- staticfiles/     Django收集的静态文件
- media/           运行时上传/生成文件
- scripts/         自动化脚本
- docs/            项目文档

## 快速开始
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 初始化数据库
   ```bash
   python manage.py migrate
   ```
3. 创建管理员账号
   ```bash
   python manage.py createsuperuser
   ```
4. 启动开发服务器
   ```bash
   python manage.py runserver
   ```
5. 访问 http://localhost:8000/

## 测试
- 所有测试用例位于 `tests/` 目录
- 运行全部测试：
  ```bash
  python -m unittest discover tests
  ```

## 部署
- 推荐使用 Docker 部署，见 `Dockerfile` 和 `docker-compose.yml`
- 生产环境请配置环境变量，分离敏感信息

## 常见问题
- **静态文件未加载？**
  - 请运行 `python manage.py collectstatic` 并确保 `STATIC_ROOT` 配置正确
- **数据库迁移失败？**
  - 检查 `migrations/` 目录，尝试 `python manage.py makemigrations` 后再 migrate
- **成绩未写入Excel？**
  - 检查日志输出、文件权限、学生名与Excel一致性

## 贡献
- 欢迎提交PR和Issue，建议先阅读 `docs/project_rules.md`

## 其它
- 日志文件默认输出到 logs/ 目录
- 所有依赖请用 `pip freeze > requirements.txt` 定期更新 