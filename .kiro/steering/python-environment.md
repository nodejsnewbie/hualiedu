---
inclusion: always
---

# Python 环境执行规则

## 强制要求

**所有 Python 命令必须使用 uv 执行**

## 执行命令的正确方式

### 运行 Django 管理命令

```bash
# ✅ 正确
uv run python manage.py <command>

# ❌ 错误
python manage.py <command>
conda run -n py313 python manage.py <command>  # 已废弃
```

### 运行测试

```bash
# ✅ 正确
uv run python manage.py test
uv run python manage.py test grading --verbosity=2

# ❌ 错误
python manage.py test
conda run -n py313 python manage.py test  # 已废弃
```

### 运行开发服务器

```bash
# ✅ 正确
uv run python manage.py runserver

# ❌ 错误
python manage.py runserver
conda run -n py313 python manage.py runserver  # 已废弃
```

### 运行 Python 脚本

```bash
# ✅ 正确
uv run python scripts/some_script.py

# ❌ 错误
python scripts/some_script.py
conda run -n py313 python scripts/some_script.py  # 已废弃
```

### 代码质量工具

```bash
# ✅ 正确
uv run black . --line-length=100
uv run isort . --profile=black --line-length=100
uv run flake8 . --max-line-length=120

# ❌ 错误
black . --line-length=100
conda run -n py313 black . --line-length=100  # 已废弃
```

## 推荐的执行方式

### 优先级 1: 使用 Makefile（推荐）

```bash
make install           # 安装依赖
make test              # 运行测试
make runserver         # 启动服务器
make migrate           # 数据库迁移
make format            # 格式化代码
make lint              # 代码检查
```

Makefile 会自动使用 uv 管理环境。

### 优先级 2: 直接使用 uv run

```bash
uv run python manage.py <command>
```

### 优先级 3: 使用辅助脚本（需要更新）

```bash
./scripts/test.sh              # 运行测试（需要更新为 uv）
./scripts/runserver.sh         # 启动服务器（需要更新为 uv）
./scripts/manage.sh migrate    # 数据库迁移（需要更新为 uv）
```

注意：辅助脚本需要更新为使用 uv。

## AI 助手执行规则

当 AI 助手（如 Kiro）需要执行 Python 命令时：

1. **必须使用** `uv run` 前缀
2. **优先使用** Makefile 命令（如 `make test`）
3. **绝不使用** 裸的 `python` 命令
4. **不再使用** `conda run -n py313`（已废弃）

### 示例

```bash
# ✅ AI 助手应该执行（推荐）
make test-file FILE=grading.tests.test_models

# ✅ 或者直接使用 uv
uv run python manage.py test grading.tests.test_models --verbosity=2

# ❌ AI 助手不应该执行
python manage.py test grading.tests.test_models
conda run -n py313 python manage.py test grading.tests.test_models  # 已废弃
```

## 环境验证

在执行任何命令前，可以验证环境：

```bash
# 检查 uv 版本
uv --version

# 检查 Python 版本
uv run python --version
# 应该输出: Python 3.13.x

# 检查 Django 版本
uv run python -c "import django; print(django.get_version())"
# 应该输出: 4.2.20

# 查看已安装的包
uv pip list
```

## 故障排查

### 问题 1: "ModuleNotFoundError: No module named 'django'"

**解决方案**：
1. 确认使用了 `uv run` 前缀
2. 安装依赖：
   ```bash
   uv sync --all-extras
   # 或
   make install
   ```

### 问题 2: uv 未安装

**解决方案**：
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 问题 3: Python 版本不匹配

**解决方案**：
```bash
# uv 会自动下载并使用 Python 3.13
# 如果需要手动指定：
uv python install 3.13
```

## 环境信息

- **包管理器**: uv (fast Python package installer)
- **Python 版本**: 3.13 (自动管理)
- **Django 版本**: 4.2.20
- **配置文件**: pyproject.toml
- **运行前缀**: `uv run`
- **依赖安装**: `uv sync --all-extras`
