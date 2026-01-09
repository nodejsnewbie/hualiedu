# 环境变量配置指南

## 概述
本项目使用环境变量来保护敏感信息，确保配置的安全性和灵活性。

## 环境变量文件

### 1. 创建环境变量文件
复制 `env.example` 为 `.env`：
```bash
cp env.example .env
# PowerShell
Copy-Item env.example .env
```

### 2. 必需的环境变量

#### Django 基础设置
```bash
# Django 密钥 (生产环境必须更改)
SECRET_KEY=your_django_secret_key_here

# 调试模式 (生产环境设为 False)
DEBUG=False

# 允许的主机
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 火山引擎 AI API 设置
```bash
# 火山引擎 Ark API 密钥
ARK_API_KEY=your_ark_api_key_here

# AI 模型名称 (可选，默认 deepseek-r1-250528)
ARK_MODEL=deepseek-r1-250528
```

#### 安全设置
```bash
# CORS 设置
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOW_CREDENTIALS=True

# 会话设置
SESSION_COOKIE_AGE=86400
SESSION_EXPIRE_AT_BROWSER_CLOSE=False

# CSRF 设置
CSRF_COOKIE_SECURE=False
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

#### 文件上传设置
```bash
# 最大上传文件大小 (字节)
MAX_UPLOAD_SIZE=10485760

# 允许的文件扩展名
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx
```

#### 日志设置
```bash
# 日志级别
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=logs/app.log
```

## 环境变量说明

### 开发环境
```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

### 生产环境
```bash
DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=<强随机密钥>
CSRF_COOKIE_SECURE=True
```

## 获取火山引擎 API 密钥

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 创建或选择项目
3. 开通 Ark 服务
4. 在 API 密钥管理中创建密钥
5. 将密钥添加到 `.env` 文件中的 `ARK_API_KEY`

## 安全注意事项

### 1. 文件保护
- `.env` 文件已添加到 `.gitignore`
- 不要将 `.env` 文件提交到版本控制
- 生产环境使用不同的环境变量文件

### 2. 密钥管理
- 使用强随机密钥作为 `SECRET_KEY`
- 定期轮换 API 密钥
- 限制 API 密钥的权限范围

### 3. 生产环境配置
```bash
# 生产环境示例
DEBUG=False
SECRET_KEY=<强随机密钥>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_COOKIE_SECURE=True
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

## 验证配置

运行以下命令验证环境变量是否正确加载：

```bash
uv run python manage.py check
```

## 故障排除

### 1. 环境变量未加载
确保：
- `.env` 文件存在于项目根目录
- 文件格式正确（无多余空格）
- 变量名和值之间使用 `=` 连接

### 2. API 调用失败
检查：
- `ARK_API_KEY` 是否正确设置
- API 密钥是否有效
- 网络连接是否正常

### 3. 权限错误
确保：
- 日志目录有写入权限
- 媒体目录有写入权限
- 数据库文件有读写权限

## 部署注意事项

### Docker 部署
```dockerfile
# 在 Dockerfile 中设置环境变量
ENV DEBUG=False
ENV SECRET_KEY=your-production-secret-key
```

### 服务器部署
```bash
# 在服务器上设置环境变量
export DEBUG=False
export SECRET_KEY=your-production-secret-key
export ARK_API_KEY=your-ark-api-key
```

## 监控和日志

### 日志文件位置
- 默认：`logs/app.log`
- 可通过 `LOG_FILE` 环境变量自定义

### 日志级别
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 查看日志
```bash
# 实时查看日志
tail -f logs/app.log

# 查看最近的错误
grep ERROR logs/app.log
```
