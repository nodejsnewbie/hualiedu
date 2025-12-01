# 部署指南

## 目录
- [系统要求](#系统要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker部署](#docker部署)
- [配置说明](#配置说明)
- [数据库迁移](#数据库迁移)
- [静态文件管理](#静态文件管理)
- [日志配置](#日志配置)
- [备份和恢复](#备份和恢复)
- [监控和维护](#监控和维护)
- [故障排查](#故障排查)

## 系统要求

### 硬件要求

**最低配置**：
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB

**推荐配置**：
- CPU: 4核或更多
- 内存: 8GB或更多
- 磁盘: 50GB或更多（根据作业文件量调整）

### 软件要求

**必需**：
- Python 3.13
- conda (用于环境管理)
- Git (用于代码管理和Git仓库功能)

**可选**：
- PostgreSQL 12+ (生产环境推荐)
- Redis (用于缓存，推荐)
- Nginx (用于反向代理)
- Supervisor (用于进程管理)

## 开发环境部署

### 1. 克隆代码

```bash
git clone <repository-url>
cd huali-edu
```

### 2. 创建Python环境

```bash
# 创建conda环境
conda create -n py313 python=3.13
conda activate py313

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env
```

必需的环境变量：
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### 4. 初始化数据库

```bash
# 运行迁移
conda run -n py313 python manage.py migrate

# 创建超级用户
conda run -n py313 python manage.py createsuperuser
```

### 5. 收集静态文件

```bash
conda run -n py313 python manage.py collectstatic --noinput
```

### 6. 启动开发服务器

```bash
# 使用Makefile
make runserver

# 或直接运行
conda run -n py313 python manage.py runserver
```

访问 http://localhost:8000

## 生产环境部署

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y python3.13 python3-pip git nginx postgresql redis-server supervisor
```

### 2. 配置PostgreSQL

```bash
# 切换到postgres用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE huali_edu;
CREATE USER huali_user WITH PASSWORD 'your-password';
ALTER ROLE huali_user SET client_encoding TO 'utf8';
ALTER ROLE huali_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE huali_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE huali_edu TO huali_user;
\q
```

### 3. 配置应用

```bash
# 克隆代码
cd /var/www
sudo git clone <repository-url> huali-edu
cd huali-edu

# 创建Python环境
conda create -n py313 python=3.13
conda activate py313
pip install -r requirements.txt

# 安装生产环境依赖
pip install gunicorn psycopg2-binary
```

### 4. 配置环境变量

创建 `/var/www/huali-edu/.env`：

```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://huali_user:your-password@localhost/huali_edu

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO

# 文件上传配置
MAX_UPLOAD_SIZE=52428800  # 50MB

# AI服务配置
VOLCENGINE_API_KEY=your-api-key
VOLCENGINE_API_SECRET=your-api-secret
```

### 5. 初始化数据库

```bash
conda run -n py313 python manage.py migrate
conda run -n py313 python manage.py collectstatic --noinput
conda run -n py313 python manage.py createsuperuser
```

### 6. 配置Gunicorn

创建 `/var/www/huali-edu/gunicorn_config.py`：

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = "/var/log/huali-edu/gunicorn-access.log"
errorlog = "/var/log/huali-edu/gunicorn-error.log"
loglevel = "info"

# 进程命名
proc_name = "huali-edu"

# 安全
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

### 7. 配置Supervisor

创建 `/etc/supervisor/conf.d/huali-edu.conf`：

```ini
[program:huali-edu]
command=/home/user/miniconda3/envs/py313/bin/gunicorn hualiEdu.wsgi:application -c /var/www/huali-edu/gunicorn_config.py
directory=/var/www/huali-edu
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/huali-edu/supervisor.log
environment=PATH="/home/user/miniconda3/envs/py313/bin"
```

启动服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start huali-edu
```

### 8. 配置Nginx

创建 `/etc/nginx/sites-available/huali-edu`：

```nginx
upstream huali_edu {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/huali-edu/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/huali-edu/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://huali_edu;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/huali-edu /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. 配置SSL (可选但推荐)

使用Let's Encrypt：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Docker部署

### 1. 使用Docker Compose

项目已包含 `docker-compose.yml`：

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 初始化数据库

```bash
# 运行迁移
docker-compose exec web python manage.py migrate

# 创建超级用户
docker-compose exec web python manage.py createsuperuser

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
```

### 3. 自定义配置

编辑 `docker-compose.yml` 根据需要调整配置。

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| SECRET_KEY | Django密钥 | - | 是 |
| DEBUG | 调试模式 | False | 否 |
| ALLOWED_HOSTS | 允许的主机 | - | 是 |
| DATABASE_URL | 数据库连接 | sqlite:///db.sqlite3 | 否 |
| REDIS_URL | Redis连接 | - | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| MAX_UPLOAD_SIZE | 最大上传大小(字节) | 52428800 | 否 |
| VOLCENGINE_API_KEY | AI服务密钥 | - | 否 |

### 数据库配置

**SQLite (开发)**：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL (生产)**：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'huali_edu',
        'USER': 'huali_user',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Redis配置

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 数据库迁移

### 创建迁移

```bash
conda run -n py313 python manage.py makemigrations
```

### 应用迁移

```bash
conda run -n py313 python manage.py migrate
```

### 查看迁移状态

```bash
conda run -n py313 python manage.py showmigrations
```

### 回滚迁移

```bash
# 回滚到指定迁移
conda run -n py313 python manage.py migrate grading 0001

# 回滚所有迁移
conda run -n py313 python manage.py migrate grading zero
```

## 静态文件管理

### 收集静态文件

```bash
conda run -n py313 python manage.py collectstatic --noinput
```

### 清理旧文件

```bash
conda run -n py313 python manage.py collectstatic --clear --noinput
```

### 配置

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## 日志配置

### 日志目录

```bash
mkdir -p /var/log/huali-edu
sudo chown www-data:www-data /var/log/huali-edu
```

### Django日志配置

在 `settings.py` 中：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/huali-edu/app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### 日志轮转

创建 `/etc/logrotate.d/huali-edu`：

```
/var/log/huali-edu/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        supervisorctl restart huali-edu > /dev/null
    endscript
}
```

## 备份和恢复

### 数据库备份

**PostgreSQL**：

```bash
# 备份
pg_dump -U huali_user huali_edu > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复
psql -U huali_user huali_edu < backup_20231201_120000.sql
```

**SQLite**：

```bash
# 备份
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# 恢复
cp db.sqlite3.backup_20231201_120000 db.sqlite3
```

### 文件备份

```bash
# 备份media文件
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# 恢复
tar -xzf media_backup_20231201.tar.gz
```

### 自动备份脚本

创建 `/usr/local/bin/backup-huali-edu.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/huali-edu"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U huali_user huali_edu > $BACKUP_DIR/db_$DATE.sql

# 备份media文件
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/huali-edu/media/

# 删除30天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

添加到crontab：

```bash
# 每天凌晨2点备份
0 2 * * * /usr/local/bin/backup-huali-edu.sh
```

## 监控和维护

### 健康检查

创建健康检查端点：

```python
# grading/views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})
```

### 性能监控

使用Django Debug Toolbar (仅开发环境)：

```bash
pip install django-debug-toolbar
```

### 日志监控

```bash
# 实时查看日志
tail -f /var/log/huali-edu/app.log

# 查看错误日志
grep ERROR /var/log/huali-edu/app.log
```

### 进程监控

```bash
# 查看Supervisor状态
sudo supervisorctl status

# 重启应用
sudo supervisorctl restart huali-edu
```

## 故障排查

### 应用无法启动

1. 检查日志：
```bash
tail -f /var/log/huali-edu/gunicorn-error.log
```

2. 检查配置：
```bash
conda run -n py313 python manage.py check
```

3. 检查数据库连接：
```bash
conda run -n py313 python manage.py dbshell
```

### 静态文件404

1. 确认静态文件已收集：
```bash
conda run -n py313 python manage.py collectstatic --noinput
```

2. 检查Nginx配置：
```bash
sudo nginx -t
```

3. 检查文件权限：
```bash
ls -la /var/www/huali-edu/staticfiles/
```

### 数据库连接错误

1. 检查PostgreSQL状态：
```bash
sudo systemctl status postgresql
```

2. 检查连接配置：
```bash
psql -U huali_user -d huali_edu -h localhost
```

3. 检查防火墙：
```bash
sudo ufw status
```

### 内存不足

1. 检查内存使用：
```bash
free -h
```

2. 减少Gunicorn workers：
```python
# gunicorn_config.py
workers = 2  # 减少worker数量
```

3. 启用swap：
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 性能问题

1. 启用数据库查询优化：
```python
# settings.py
DEBUG = False
CONN_MAX_AGE = 600
```

2. 启用Redis缓存

3. 优化数据库索引：
```bash
conda run -n py313 python manage.py sqlsequencereset grading
```

## 安全建议

1. **使用HTTPS**：配置SSL证书
2. **定期更新**：保持系统和依赖最新
3. **限制访问**：配置防火墙规则
4. **备份数据**：定期备份数据库和文件
5. **监控日志**：定期检查异常日志
6. **强密码**：使用强密码和密钥
7. **最小权限**：应用使用非root用户运行

## 相关文档

- [开发指南](./DEVELOPMENT.md)
- [API文档](./API.md)
- [用户手册](./USER_MANUAL.md)
- [项目结构](./PROJECT_STRUCTURE.md)
