# 华立教育评分系统

这是一个基于Django的评分系统，用于管理和评分学生作业。

## 系统要求

- Python 3.9+
- MySQL 8.0+
- Docker & Docker Compose (可选，用于容器化部署)

## 项目结构

```
huali-edu/
├── hualiEdu/          # Django项目主目录
├── grading/           # 评分应用
├── static/            # 静态文件
├── templates/         # 模板文件
├── media/             # 媒体文件
├── requirements.txt   # Python依赖
├── Dockerfile         # Docker配置
├── docker-compose.yml # Docker Compose配置
└── .env              # 环境变量配置
```

## 快速开始

### 1. 环境准备

```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

项目根目录下提供了`.env.example`文件作为环境变量配置模板。请按以下步骤操作：

1. 复制`.env.example`为`.env`：
```bash
cp .env.example .env
```

2. 编辑`.env`文件，修改以下配置：
   - 将`DEBUG`设置为`0`（生产环境）
   - 生成并设置安全的`SECRET_KEY`
   - 配置数据库连接信息
   - 设置`ALLOWED_HOSTS`为你的域名
   - 根据需要配置邮件设置
   - 配置SSL相关设置

注意：`.env`文件包含敏感信息，请确保：
- 不要将`.env`文件提交到版本控制系统
- 在生产环境中使用安全的密码和密钥
- 定期更新密钥和密码

### 3. 数据库迁移

```bash
python manage.py migrate
```

### 4. 收集静态文件

```bash
python manage.py collectstatic
```

### 5. 创建超级用户

```bash
python manage.py createsuperuser
```

## Docker部署

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 创建超级用户

```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. 检查服务状态

```bash
docker-compose ps
```

### 5. 查看日志

```bash
docker-compose logs -f
```

## 生产环境注意事项

1. **安全配置**
   - 确保修改所有默认密码和密钥
   - 配置适当的ALLOWED_HOSTS
   - 设置DEBUG=False
   - 配置SSL/TLS证书

2. **数据库**
   - 配置适当的数据库备份策略
   - 定期优化数据库性能

3. **日志记录**
   - 配置适当的日志记录级别
   - 设置日志轮转策略

4. **文件权限**
   - 确保适当的文件权限设置
   - 保护敏感配置文件

5. **监控**
   - 设置系统监控
   - 配置错误告警

## 依赖说明

主要依赖包：
- Django>=4.2,<5.0
- mysqlclient==2.2.4
- python-docx>=0.8.11
- mammoth==1.6.0
- django-jazzmin==3.0.1
- GitPython>=3.1.40
- gunicorn==21.2.0
- whitenoise==6.6.0
- python-dotenv==1.0.1
- django-cors-headers==4.3.1
- django-storages==1.14.2

## 技术支持

如有问题，请联系系统管理员。

## 许可证

[添加许可证信息] 