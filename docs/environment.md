# 环境配置指南

## 概述
本项目使用环境变量来保护敏感信息，确保配置的安全性和灵活性。

## 快速开始

### 1. 创建环境变量文件
```bash
cp .env.example .env
```

### 2. 配置必需变量
编辑 `.env` 文件，设置以下关键变量：
- `SECRET_KEY`: Django密钥
- `DEBUG`: 调试模式
- `ALLOWED_HOSTS`: 允许的主机
- `ARK_API_KEY`: 火山引擎API密钥
- `ARK_MODEL`: AI模型名称

## 环境变量详解

### Django基础设置
```bash
# Django密钥（生产环境必须更改）
SECRET_KEY=your_django_secret_key_here

# 调试模式（生产环境设为False）
DEBUG=False

# 允许的主机
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### 火山引擎AI API设置
```bash
# API密钥
ARK_API_KEY=your_ark_api_key_here

# AI模型名称（默认deepseek-r1-250528）
ARK_MODEL=deepseek-r1-250528
```

### 数据库设置
```bash
# SQLite数据库（默认）
DATABASE_URL=sqlite:///db.sqlite3

# MySQL配置（可选）
MYSQL_ROOT_PASSWORD=your_mysql_password
MYSQL_DATABASE=huali_edu
MYSQL_USER=huali_user
MYSQL_PASSWORD=your_mysql_password
```

### 文件上传设置
```bash
# 最大上传文件大小（字节）
MAX_UPLOAD_SIZE=10485760

# 允许的文件扩展名
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx
```

### 日志设置
```bash
# 日志级别
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=logs/app.log
```

### 安全设置
```bash
# CORS设置
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOW_CREDENTIALS=True

# 会话设置
SESSION_COOKIE_AGE=86400
SESSION_EXPIRE_AT_BROWSER_CLOSE=False

# CSRF设置
CSRF_COOKIE_SECURE=False
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

## 环境配置

### 开发环境
```bash
DEBUG=True
LOG_LEVEL=DEBUG
CSRF_COOKIE_SECURE=False
```

### 生产环境
```bash
DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=<强随机密钥>
CSRF_COOKIE_SECURE=True
ALLOWED_HOSTS=your-domain.com
```

## 验证配置

### 检查Django配置
```bash
python manage.py check
```

### 验证环境变量
```bash
python scripts/verify_env.py
```

### 测试API连接
```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('ARK_API_KEY:', os.getenv('ARK_API_KEY')[:10] + '...' if os.getenv('ARK_API_KEY') else 'Not set')
"
```

## 故障排除

### 环境变量未加载
1. 确保`.env`文件存在于项目根目录
2. 检查文件格式（无多余空格）
3. 变量名和值之间使用`=`连接

### API调用失败
1. 确认`ARK_API_KEY`正确设置
2. 检查API密钥有效性
3. 验证网络连接
4. 检查代理设置

### 权限错误
1. 确保日志目录有写入权限
2. 检查媒体目录权限
3. 验证数据库文件权限

## 最佳实践

### 安全管理
- `.env`文件添加到`.gitignore`
- 生产环境使用环境变量而非文件
- 定期轮换敏感密钥
- 使用强随机密钥

### 配置管理
- 不同环境使用不同配置
- 模型名和端点可通过环境变量覆盖
- 日志统一写入`logs/app.log`
- 配置验证脚本定期检查

### 部署建议
- Docker部署时设置环境变量
- 服务器部署使用export设置
- 监控配置变更
- 备份重要配置文件
