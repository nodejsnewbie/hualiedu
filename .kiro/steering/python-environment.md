---
inclusion: always
---

# Python 环境执行规则

## 强制要求

**所有 Python 命令必须在 conda py313 环境下执行**

## 执行命令的正确方式

### 运行 Django 管理命令

```bash
# ✅ 正确
conda run -n py313 python manage.py <command>

# ❌ 错误
python manage.py <command>
```

### 运行测试

```bash
# ✅ 正确
conda run -n py313 python manage.py test
conda run -n py313 python manage.py test grading --verbosity=2

# ❌ 错误
python manage.py test
```

### 运行开发服务器

```bash
# ✅ 正确
conda run -n py313 python manage.py runserver

# ❌ 错误
python manage.py runserver
```

### 运行 Python 脚本

```bash
# ✅ 正确
conda run -n py313 python scripts/some_script.py

# ❌ 错误
python scripts/some_script.py
```

### 代码质量工具

```bash
# ✅ 正确
conda run -n py313 black . --line-length=100
conda run -n py313 isort . --profile=black --line-length=100
conda run -n py313 flake8 . --max-line-length=120

# ❌ 错误
black . --line-length=100
```

## 推荐的执行方式

### 优先级 1: 使用 Makefile

```bash
make test              # 运行测试
make runserver         # 启动服务器
make migrate           # 数据库迁移
make format            # 格式化代码
```

Makefile 会自动使用 conda py313 环境。

### 优先级 2: 使用辅助脚本

```bash
./scripts/test.sh              # 运行测试
./scripts/runserver.sh         # 启动服务器
./scripts/manage.sh migrate    # 数据库迁移
```

辅助脚本会自动使用 conda py313 环境。

### 优先级 3: 直接使用 conda run

```bash
conda run -n py313 python manage.py <command>
```

## AI 助手执行规则

当 AI 助手（如 Kiro）需要执行 Python 命令时：

1. **必须使用** `conda run -n py313` 前缀
2. **优先使用** Makefile 命令（如 `make test`）
3. **优先使用** 辅助脚本（如 `./scripts/test.sh`）
4. **绝不使用** 裸的 `python` 命令

### 示例

```bash
# ✅ AI 助手应该执行
conda run -n py313 python manage.py test grading.tests.test_models --verbosity=2

# ✅ 或者使用 Makefile
make test-file FILE=grading.tests.test_models

# ❌ AI 助手不应该执行
python manage.py test grading.tests.test_models
```

## 环境验证

在执行任何命令前，可以验证环境：

```bash
# 检查 Python 版本
conda run -n py313 python --version
# 应该输出: Python 3.13.x

# 检查 Django 版本
conda run -n py313 python -c "import django; print(django.get_version())"
# 应该输出: 4.2.20
```

## 故障排查

如果遇到 "ModuleNotFoundError: No module named 'django'" 错误：

1. 确认使用了 `conda run -n py313` 前缀
2. 确认 py313 环境已安装依赖：
   ```bash
   conda run -n py313 pip install -r requirements.txt
   ```

## 环境信息

- **环境名称**: py313
- **Python 版本**: 3.13
- **Django 版本**: 4.2.20
- **激活命令**: `conda activate py313`
- **运行前缀**: `conda run -n py313`
