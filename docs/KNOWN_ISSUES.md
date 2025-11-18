# 已知问题

## 批量登分功能完整修复（2025-11-13）

### 最终实现
批量登分功能已完全实现并优化，详细规范请参考 `docs/BATCH_GRADE_SPECIFICATION.md`

## 批量登分功能

详细说明请参考：**[批量登分功能指南](./BATCH_GRADE.md)**

### 快速链接
- [快速开始](./BATCH_GRADE.md#快速开始) - 5分钟上手
- [设置指南](./BATCH_GRADE.md#设置指南) - 导入作业、环境准备
- [故障排查](./BATCH_GRADE.md#故障排查) - 常见问题诊断
- [测试指南](./BATCH_GRADE.md#测试指南) - 测试清单

### 常见问题快速解决

| 问题 | 解决方案 |
|------|---------|
| 按钮禁用 | 确保选择了作业文件夹（非文件） |
| 未找到作业 | 运行 `conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>` |
| 按钮卡住 | 清除浏览器缓存（Ctrl+Shift+R） |
| 404错误 | 检查作业是否存在于数据库 |

### 相关文档
- [批量登分功能指南](./BATCH_GRADE.md) - 完整文档
- [设计文档](../.kiro/specs/grade-registry-writer/design.md) - 技术设计

## Homework模型未导入问题（已修复）

### 问题描述
加载目录树时出现错误：`name 'Homework' is not defined`

### 原因
在 `get_directory_tree` 函数中使用了 `Homework` 模型，但在文件顶部的导入语句中没有包含它。

### 解决方案
在 `grading/views.py` 的导入语句中添加 `Homework`：
```python
from .models import (
    Course,
    GlobalConfig,
    GradeTypeConfig,
    Homework,  # 添加这一行
    Repository,
    Semester,
)
```

## 目录树显示问题（已修复）

### 问题描述
目录树无法显示，页面空白。

### 原因
在 `addHomeworkTypeLabels()` 函数中，使用了正则表达式替换 `\$&`，但Kiro IDE的自动格式化会将其替换成UUID，导致JavaScript语法错误。

### 临时解决方案
已暂时注释掉 `addHomeworkTypeLabels()` 函数的调用，目录树可以正常显示，但作业类型标签功能暂时不可用。

### 永久解决方案
需要重写 `addHomeworkTypeLabels()` 函数，使用jstree的API来获取节点元素，避免使用正则表达式中的特殊字符。

修改后的代码：
```javascript
// 使用jstree的API获取节点的DOM元素
const nodeElement = $('#directory-tree').jstree(true).get_node(nodeId, true);

if (nodeElement && nodeElement.length > 0) {
    const anchorElement = nodeElement.find('a.jstree-anchor');
    // ...
}
```

## 作业类型标签功能

### 当前状态
- ✅ 后端API已实现
- ✅ 数据模型已完善
- ⚠️ 前端显示功能暂时禁用（等待修复）

### 可用功能
- 可以通过API直接调用来设置作业类型
- 作业类型数据会正确保存到数据库
- 评分功能会根据作业类型正确处理

### 待修复功能
- 在目录树中显示作业类型标签
- 点击标签修改作业类型

## 解决步骤

1. 重新实现 `addHomeworkTypeLabels()` 函数，避免使用会被格式化工具修改的代码
2. 测试确认目录树正常显示
3. 取消注释函数调用
4. 测试作业类型标签功能

## 当前可用的替代方案

如果需要设置作业类型，可以：

1. 直接调用API：
```javascript
$.ajax({
    url: '/grading/api/update-homework-type/',
    method: 'POST',
    data: {
        course_name: '课程名称',
        folder_name: '作业文件夹名称',
        homework_type: 'lab_report'  // 或 'normal'
    }
});
```

2. 在Django Admin中管理作业类型

3. 使用数据库管理工具直接修改
