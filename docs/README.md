# 作业评分系统文档

## 📚 核心文档

### Spec文档（在 .kiro/specs/homework-grading-system/）

1. **[需求文档](../.kiro/specs/homework-grading-system/requirements.md)**
   - 完整的系统需求（20个需求）
   - 使用EARS格式编写

2. **[设计文档](../.kiro/specs/homework-grading-system/design.md)** ⭐ 主文档
   - 评分写入流程
   - 作业类型判断
   - 格式错误处理
   - 统一函数设计
   - 数据模型
   - 测试策略

### 辅助文档（在 docs/）

3. **[快速参考](./SUMMARY.md)**
   - 核心概念速查
   - 常见问题解答

4. **[团队协作指南](./TEAM_COLLABORATION.md)**
   - 协作规范和最佳实践

## 🔍 快速查找

| 我想了解... | 查看文档 |
|------------|---------|
| 评分如何写入实验报告？ | [设计文档](../.kiro/specs/homework-grading-system/design.md) |
| 如何判断作业类型？ | [设计文档](../.kiro/specs/homework-grading-system/design.md) - 作业类型判断 |
| 格式错误如何处理？ | [设计文档](../.kiro/specs/homework-grading-system/design.md) - 错误处理 |
| 有哪些统一函数？ | [设计文档](../.kiro/specs/homework-grading-system/design.md) - 组件和接口 |
| 批量登分如何工作？ | **[批量登分指南](./BATCH_GRADE.md)** ⭐ |
| 批量登分故障排查 | [批量登分指南 - 故障排查](./BATCH_GRADE.md#故障排查) |
| 系统有哪些功能？ | [需求文档](../.kiro/specs/homework-grading-system/requirements.md) |
| 已知问题和修复 | [已知问题](./KNOWN_ISSUES.md) |
| 核心概念速查 | [快速参考](./SUMMARY.md) |
| 开发环境配置 | [开发指南](./DEVELOPMENT.md) |
| 团队协作规范 | [协作指南](./TEAM_COLLABORATION.md) |

## 🎯 推荐阅读顺序

### 新用户
1. [快速参考](./SUMMARY.md) - 5分钟了解核心概念
2. [设计文档](../.kiro/specs/homework-grading-system/design.md) - 15分钟掌握完整逻辑

### 开发者
1. [设计文档](../.kiro/specs/homework-grading-system/design.md) - 理解实现细节
2. [需求文档](../.kiro/specs/homework-grading-system/requirements.md) - 查看完整需求

### 测试人员
1. [需求文档](../.kiro/specs/homework-grading-system/requirements.md) - 编写测试用例
2. [设计文档](../.kiro/specs/homework-grading-system/design.md) - 理解测试场景

## 📝 文档结构

```
.kiro/specs/homework-grading-system/
├── requirements.md  # 需求文档（EARS格式）
└── design.md        # 设计文档（主文档）

docs/
├── README.md                # 本文档（索引）
├── SUMMARY.md               # 快速参考
├── TEAM_COLLABORATION.md    # 团队协作
├── PROJECT_STRUCTURE.md     # 项目结构
└── KNOWN_ISSUES.md          # 已知问题
```

## 🔗 相关代码

- `grading/views.py` - 主要业务逻辑
- `grading/models.py` - 数据模型
- `templates/grading_simple.html` - 评分页面
- `grading/static/grading/js/grading.js` - 前端交互
