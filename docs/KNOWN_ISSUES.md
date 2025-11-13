# 已知问题

## 批量登分按钮无响应问题（已修复 - 2025-11-13）

### 问题描述
在作业评分系统中，点击"批量登分"按钮没有反应，而且该功能没有体现出应该针对某一次作业的设计理念。

### 根本原因
1. **ID不匹配**：HTML模板中按钮ID是 `batch-grade-btn`（带连字符），但JavaScript代码中使用的是 `batchGradeBtn`（驼峰命名），导致事件绑定失败
2. 原有设计没有明确批量登分应该针对特定作业文件夹
3. 没有跟踪当前选中的作业文件夹信息

### 解决方案
1. **修复ID不匹配问题**：将JavaScript代码中所有 `batchGradeBtn` 统一改为 `batch-grade-btn`
2. **实现作业关联功能**：
   - 添加 `currentHomeworkFolder` 和 `currentHomeworkId` 全局变量跟踪当前作业
   - 实现 `updateBatchGradeButton()` 函数，根据选中的文件夹自动查询作业信息并更新按钮状态
   - 按钮文本动态显示当前选中的作业名称，如"批量登分 (作业1)"
   - 只有选中作业文件夹时按钮才启用，选中文件时自动禁用
3. **改进用户体验**：
   - 在HTML模板中添加提示信息："选择作业文件夹后可批量操作"
   - 按钮tooltip动态更新，显示当前操作的作业名称
   - 点击按钮前显示确认对话框，明确告知用户将要操作的作业

### 修改的文件
- `grading/static/grading/js/grading.js`：
  - 修复ID不匹配（统一使用 `batch-grade-btn`）
  - 实现作业关联逻辑
  - 整合重复的事件绑定，确保按钮状态正确更新
  - 选中文件时重置按钮文本和tooltip
  - 添加详细的调试日志
- `templates/grading_simple.html`：
  - 修复按钮ID（从 `batchGradeBtn` 改为 `batch-grade-btn`）
  - 添加初始禁用状态和提示信息
  - 添加图标和说明文字
- `grading/templates/grading.html`：改进按钮提示信息（备用模板）

### 重要说明
实际使用的模板是 `templates/grading_simple.html`，而不是 `grading/templates/grading.html`。
`grading_page` 视图返回的是 `grading_simple.html` 模板。

## 批量登分失败 - 未找到作业目录

### 问题描述
点击批量登分按钮后，提示"批量登分失败：未找到作业目录: xxx"

### 原因
批量登分功能需要数据库中有对应的 Homework（作业）记录。如果：
1. 数据库中没有对应的作业记录
2. 作业的 `folder_name` 与实际文件夹名称不匹配
3. 文件夹路径结构不符合预期

就会出现此错误。

### 解决方案

> 2025-11 更新：系统会在每个激活仓库中有限深度地回退搜索同名作业文件夹。如果找到唯一匹配，会自动使用该目录继续登分；如果找到多个同名目录，则会提示冲突并要求手动修正。因此仍需保持课程名称、班级名称及 `folder_name` 与文件系统一致，并避免在同一仓库里出现多个同名作业目录。

#### 方法1：使用管理命令自动导入作业（推荐）
```bash
# 预览将要导入的作业
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称> --dry-run

# 实际导入作业
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>
```

#### 方法2：使用诊断脚本排查问题
```bash
conda run -n py313 python scripts/diagnose_batch_grade.py <课程名称> <作业文件夹名称>
```

#### 方法3：在Django Admin中手动创建作业
1. 访问 http://127.0.0.1:8000/admin/grading/homework/
2. 点击"添加作业"
3. 填写信息，确保 `folder_name` 与实际文件夹名称完全一致

### 详细文档
参考 `docs/BATCH_GRADE_SETUP.md` 获取完整的设置指南。

### 技术细节
- 移除了重复的 `select_node.jstree` 事件绑定
- 在 jstree 初始化时统一处理文件和文件夹的选择事件
- 确保选中文件时按钮被禁用并重置显示文本

### 相关文档
详细的批量登分功能设计请参考：`.kiro/specs/grade-registry-writer/design.md`

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
