# 开发环境配置指南

## Python 环境

本项目使用 **conda** 管理 Python 环境，环境名称为 **py313**，Python 版本为 **3.13**。

### 环境激活

所有开发命令都必须在 conda py313 环境下执行。有两种方式：

#### 方式 1: 手动激活环境（推荐用于交互式开发）

```bash
conda activate py313
```

激活后，所有命令直接运行：

```bash
python manage.py runserver
python manage.py test
```

#### 方式 2: 使用 conda run 前缀（推荐用于脚本和自动化）

```bash
conda run -n py313 python manage.py runserver
conda run -n py313 python manage.py test
```

## 快速开始

### 使用 Makefile（最简单）

项目提供了 Makefile 来简化常用命令：

```bash
# 查看所有可用命令
make help

# 运行测试
make test

# 运行指定应用的测试
make test-app APP=grading

# 启动开发服务器
make runserver

# 启动开发服务器（指定端口）
make runserver PORT=8080

# 数据库迁移
make migrate
make makemigrations

# 代码格式化和检查
make format
make lint

# 清理临时文件
make clean
```

### 使用辅助脚本

项目在 `scripts/` 目录下提供了辅助脚本：

```bash
# 运行测试
./scripts/test.sh                                    # 所有测试
./scripts/test.sh grading                           # 指定应用
./scripts/test.sh grading.tests.test_models         # 指定测试文件

# 启动开发服务器
./scripts/runserver.sh                              # 默认端口 8000
./scripts/runserver.sh 8080                         # 指定端口

# 运行 Django 管理命令
./scripts/manage.sh makemigrations
./scripts/manage.sh migrate
./scripts/manage.sh createsuperuser
./scripts/manage.sh shell
```

### 直接使用 conda run

如果你不想使用 Makefile 或脚本，可以直接使用 conda run：

```bash
# 开发服务器
conda run -n py313 python manage.py runserver

# 测试
conda run -n py313 python manage.py test
conda run -n py313 python manage.py test grading
conda run -n py313 python manage.py test grading.tests.test_models --verbosity=2

# 数据库
conda run -n py313 python manage.py makemigrations
conda run -n py313 python manage.py migrate

# 代码质量
conda run -n py313 black . --line-length=100
conda run -n py313 isort . --profile=black --line-length=100
conda run -n py313 flake8 . --max-line-length=120
```

## 常见开发任务

### 运行测试

```bash
# 推荐：使用 Makefile
make test

# 或使用脚本
./scripts/test.sh

# 或直接使用 conda run
conda run -n py313 python manage.py test --verbosity=2
```

### 启动开发服务器

```bash
# 推荐：使用 Makefile
make runserver

# 或使用脚本
./scripts/runserver.sh

# 或直接使用 conda run
conda run -n py313 python manage.py runserver
```

### 数据库迁移

```bash
# 创建迁移
make makemigrations

# 应用迁移
make migrate
```

### 代码格式化

```bash
# 格式化代码
make format

# 检查代码质量
make lint
```

## IDE 配置

### VS Code

在 `.vscode/settings.json` 中配置：

```json
{
  "python.defaultInterpreterPath": "/path/to/conda/envs/py313/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": false,
  "python.testing.unittestEnabled": true,
  "python.testing.unittestArgs": [
    "-v",
    "-s",
    ".",
    "-p",
    "test*.py"
  ]
}
```

### PyCharm

1. 打开 Settings/Preferences
2. 进入 Project > Python Interpreter
3. 点击齿轮图标 > Add
4. 选择 Conda Environment
5. 选择 Existing environment
6. 选择 py313 环境

## 环境验证

验证环境是否正确配置：

```bash
# 检查 Python 版本
conda run -n py313 python --version
# 应该输出: Python 3.13.x

# 检查 Django 版本
conda run -n py313 python -c "import django; print(django.get_version())"
# 应该输出: 4.2.20

# 运行简单测试
make test-app APP=grading.tests.test_grade_registry_writer
```

## 故障排查

### 问题：找不到 conda 命令

**解决方案**：确保 conda 已正确安装并添加到 PATH

```bash
# 初始化 conda
conda init bash  # 或 zsh, fish 等
```

### 问题：环境不存在

**解决方案**：创建 py313 环境

```bash
conda create -n py313 python=3.13
conda activate py313
pip install -r requirements.txt
```

### 问题：模块找不到

**解决方案**：确保在正确的环境中安装了依赖

```bash
conda activate py313
pip install -r requirements.txt
```

## 最佳实践

1. **始终使用 conda 环境**：不要在系统 Python 中运行项目命令
2. **使用 Makefile**：优先使用 `make` 命令，它会自动处理环境
3. **提交前检查**：运行 `make format` 和 `make lint` 确保代码质量
4. **运行测试**：提交前运行 `make test` 确保所有测试通过
5. **保持环境同步**：定期更新 requirements.txt 并重新安装依赖

## 参考资料

- [Django 文档](https://docs.djangoproject.com/)
- [Conda 文档](https://docs.conda.io/)
- [项目技术栈](.kiro/steering/tech.md)
