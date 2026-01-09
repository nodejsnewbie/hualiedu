# Scripts 目录

> **项目维护和工具脚本**

## 📋 脚本列表

### 清理脚本

#### `cleanup_test_directories.sh`
清理 Hypothesis 测试生成的随机目录（Bash 版本）。

**使用方法：**
```bash
./scripts/cleanup_test_directories.sh

# 或使用 Makefile
make clean-test-dirs
```

**功能：**
- 删除测试生成的随机目录
- 保护项目核心目录（白名单）
- 显示彩色输出和统计信息
- 清理 `.hypothesis` 目录

#### `cleanup_test_directories.py`
清理 Hypothesis 测试生成的随机目录（Python 版本）。

**使用方法：**
```bash
# 实际删除
uv run python scripts/cleanup_test_directories.py

# 预览模式（不实际删除）
uv run python scripts/cleanup_test_directories.py --dry-run
```

**优势：**
- 跨平台兼容
- 支持预览模式
- 更可靠的错误处理
- 详细的日志输出

### 开发辅助脚本

**注意**：以下脚本已废弃，请使用新的方式：

| 废弃脚本 | 替代方式 |
|---------|---------|
| `activate_env.sh` | `uv run` |
| `manage.sh` | `uv run python manage.py` 或 `make` 命令 |
| `runserver.sh` | `make runserver` |
| `test.sh` | `make test` |

### 诊断脚本

#### `diagnose_batch_grade.py`
诊断批量评分功能。

**使用方法：**
```bash
uv run python scripts/diagnose_batch_grade.py
```

#### `manual_test_ssh_key.py`
手动测试 SSH 密钥配置。

**使用方法：**
```bash
uv run python scripts/manual_test_ssh_key.py
```

#### `verify_database_structure.py`
验证数据库结构。

**使用方法：**
```bash
uv run python scripts/verify_database_structure.py
```

## 🔧 使用建议

### 优先使用 Makefile

大多数常用操作都有 Makefile 命令：

```bash
make help              # 查看所有可用命令
make test              # 运行测试
make runserver         # 启动服务器
make clean             # 清理临时文件
make clean-test-dirs   # 清理测试目录
make clean-all         # 完整清理
```

### 直接使用 uv run

对于没有 Makefile 命令的脚本：

```bash
uv run python scripts/<script_name>.py
```



## 📝 添加新脚本

### 脚本规范

1. **命名规范**
   - 使用小写字母和下划线
   - 描述性名称
   - 示例：`cleanup_test_directories.py`

2. **文件头部**
   ```python
   #!/usr/bin/env python3
   """
   脚本简短描述
   
   详细说明...
   
   使用方法：
       python scripts/script_name.py
   """
   ```

3. **可执行权限**
   ```bash
   chmod +x scripts/script_name.sh
   ```

4. **文档**
   - 在本 README 中添加说明
   - 在脚本中添加详细注释
   - 提供使用示例

### Python 脚本模板

```python
#!/usr/bin/env python3
"""
脚本名称

功能描述...

使用方法：
    python scripts/script_name.py [options]
"""

import sys
from pathlib import Path


def main():
    """主函数"""
    print("脚本执行中...")
    # 实现逻辑
    

if __name__ == "__main__":
    main()
```

### Bash 脚本模板

```bash
#!/bin/bash
# 脚本名称
# 
# 功能描述...
# 
# 使用方法：
#   ./scripts/script_name.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}脚本开始执行...${NC}"

# 实现逻辑

echo -e "${GREEN}完成！${NC}"
```

## 🐛 故障排查

### 权限错误

```bash
# 添加执行权限
chmod +x scripts/script_name.sh
```

### Python 模块未找到

```bash
# 确保使用 uv run
uv run python scripts/script_name.py

# 或安装依赖
make install
```

### 路径错误

脚本应该从项目根目录运行：

```bash
# 正确
./scripts/script_name.sh

# 错误
cd scripts && ./script_name.sh
```

## 📚 相关文档

- [开发指南](../docs/DEVELOPMENT.md) - 完整的开发环境和工作流程
- [文档导航](../docs/README.md) - 所有项目文档索引
