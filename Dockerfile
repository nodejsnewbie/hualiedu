# 使用官方 Python 镜像
FROM python:3.13-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=hualiEdu.settings

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件到容器中
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露应用运行的端口
EXPOSE 8000

# 使用gunicorn运行应用
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hualiEdu.wsgi:application"]
