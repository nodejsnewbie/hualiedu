# 集成测试

> **跨应用的集成测试**

## 测试结构

```
tests/
├── README.md              # 本文件
├── __init__.py            # 测试包初始化
└── test_*.py              # 集成测试文件
```

**注意**：
- 应用级测试位于 `<app>/tests/`
- 手动测试脚本位于 `scripts/`

## 运行测试

```bash
# 运行所有测试（包括集成测试）
make test

# 只运行集成测试
uv run python manage.py test tests

# 运行特定测试文件
uv run python manage.py test tests.test_git_handler
```

## 测试类型

### 集成测试（tests/）
测试多个应用或组件的交互，如：
- Git 处理工具
- 跨应用工作流
- 端到端场景

### 单元测试（grading/tests/）
测试单个应用的功能，如：
- 模型测试
- 视图测试
- 服务层测试

## 测试规范

详见 [开发指南 - 测试部分](../docs/DEVELOPMENT.md#测试指南)
