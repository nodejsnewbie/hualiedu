# 环境与配置指南

## 快速开始
- 复制 `env.example` 为 `.env`
- 关键变量：`SECRET_KEY`、`DEBUG`、`ALLOWED_HOSTS`、`ARK_API_KEY`、`ARK_MODEL`

## 必需与可选变量
- SECRET_KEY, DEBUG, ALLOWED_HOSTS
- ARK_API_KEY, ARK_MODEL (默认 deepseek-r1-250528)
- MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS
- LOG_LEVEL, LOG_FILE

## 开发/生产建议
- 开发：`DEBUG=True`, `LOG_LEVEL=DEBUG`
- 生产：`DEBUG=False`, 强随机 `SECRET_KEY`，收紧 `ALLOWED_HOSTS`，开启 CSRF 安全

## 验证与故障排除
- `python manage.py check`
- 检查 `.env` 是否存在且变量名正确
- API 调用失败：确认 `ARK_API_KEY` 正确、有效、网络可达

## 最佳实践
- `.env` 纳入 `.gitignore`
- 模型名和端点通过环境变量可覆盖
- 日志写入 `logs/app.log`
