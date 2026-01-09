# 批量登分功能规范

## 文档说明

本目录包含批量登分功能的规范文档。

## 文档列表

1. **[requirements.md](./requirements.md)** - 功能需求（21个需求，EARS格式）
2. **[design.md](./design.md)** - 架构设计和技术实现
3. **[tasks.md](./tasks.md)** - 实施任务清单（已完成）

## 用户文档

完整的用户指南和故障排查请参考：
- **[批量登分功能指南](../../docs/BATCH_GRADE.md)** ⭐ 主要用户文档

## 快速链接

| 我想了解... | 查看文档 |
|------------|---------|
| 如何使用批量登分？ | [批量登分指南 - 快速开始](../../docs/BATCH_GRADE.md#快速开始) |
| 如何设置和导入作业？ | [批量登分指南 - 设置指南](../../docs/BATCH_GRADE.md#设置指南) |
| 遇到问题怎么办？ | [批量登分指南 - 故障排查](../../docs/BATCH_GRADE.md#故障排查) |
| 功能需求是什么？ | [requirements.md](./requirements.md) |
| 技术架构是什么？ | [design.md](./design.md) |
| 实施进度如何？ | [tasks.md](./tasks.md) |

## 文档维护

- **需求变更**：更新 `requirements.md`
- **设计变更**：更新 `design.md`
- **用户文档**：更新 `../../docs/BATCH_GRADE.md`
- **不要创建**：新的 `implementation.md`、`ui-specification.md` 等文档（避免文档膨胀）

## 相关代码

- `grading/views.py` - 视图层
- `grading/services/grade_registry_writer_service.py` - 服务层
- `grading/grade_registry_writer.py` - 工具层
- `grading/static/grading/js/grading.js` - 前端交互
- `templates/grading_simple.html` - 评分页面

---

**维护原则**：保持文档简洁，避免重复，单一信息源。
