# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装项目依赖
RUN pip install -r requirements.txt

# 暴露应用运行的端口
EXPOSE 8000

# 运行Django开发服务器
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]