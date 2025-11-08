# 测试文档

## 测试结构

```
tests/
├── README.md                    # 本文件
├── __init__.py                  # 测试包初始化
└── test_git_handler.py          # Git处理工具测试
```

**注意：** 手动测试脚本已移至 `scripts/` 目录。

## 运行测试

### 运行所有测试
```bash
python manage.py test
```

### 运行特定测试文件
```bash
python manage.py test tests.test_utils
```

### 运行特定测试类
```bash
python manage.py test tests.test_utils.TestGitHandler
```

### 运行特定测试方法
```bash
python manage.py test tests.test_utils.TestGitHandler.test_clone_repo
```

## 测试规范

### 命名规范
- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 测试组织
- **单元测试**：测试单个函数或方法
- **集成测试**：测试多个组件的交互
- **功能测试**：测试完整的用户场景

### 测试覆盖率
目标：保持 80% 以上的代码覆盖率

## 测试数据

测试数据应该：
1. 使用 Django 的 fixtures 或工厂模式
2. 在测试后自动清理
3. 不依赖生产数据

## 持续集成

测试应该在以下情况自动运行：
- 提交代码前（pre-commit hook）
- 推送到远程仓库
- 创建 Pull Request

## 测试最佳实践

1. **独立性**：每个测试应该独立运行
2. **可重复性**：测试结果应该一致
3. **快速**：单元测试应该在秒级完成
4. **清晰**：测试名称应该描述测试内容
5. **覆盖边界情况**：测试正常和异常情况
