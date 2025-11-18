# 批量登分功能指南

> **最后更新**: 2025-11-19  
> **版本**: 2.0 (整合版)

## 目录

1. [快速开始](#快速开始) - 5分钟上手
2. [功能规范](#功能规范) - 完整功能说明
3. [设置指南](#设置指南) - 环境准备
4. [用户界面](#用户界面) - UI说明
5. [故障排查](#故障排查) - 问题诊断
6. [测试指南](#测试指南) - 测试清单
7. [API参考](#api参考) - 技术接口

---

## 快速开始

### 基本流程（5分钟）

1. **选择仓库和课程**
2. **点击作业文件夹**（非文件）
3. **点击"批量登分"按钮**
4. **等待处理完成**
5. **查看结果模态框**

### 常见问题快速解决

| 问题 | 解决方案 |
|------|---------|
| 按钮禁用 | 确保选择了作业文件夹（非文件） |
| 未找到作业 | 运行 `conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>` |
| 按钮卡住 | 清除浏览器缓存（Ctrl+Shift+R） |
| 404错误 | 检查作业是否存在于数据库 |

### 前置条件

- ✅ 已创建课程（Course）
- ✅ 已导入作业（Homework）
- ✅ 作业文件夹中有学生Word文档
- ✅ 班级目录中有成绩登记表Excel

---

## 功能规范

### 功能概述

批量登分功能允许教师一键将作业文件夹中所有学生的成绩批量写入到班级成绩登记表Excel文件中。


### 用户交互流程

#### 1. 选择作业
- 用户在评分页面选择仓库和课程
- 用户点击作业文件夹（非文件）
- 批量登分按钮启用，显示"批量登分 (作业名称)"

#### 2. 执行批量登分
- 用户点击批量登分按钮
- **直接执行，不显示确认对话框**
- 按钮变为禁用状态，显示"正在批量登分..."
- 进度条出现，显示处理状态

#### 3. 处理完成

**情况A：完全成功（failed = 0）**
- 绿色标题："批量登分完成"
- 大的绿色对勾图标
- 文本："已成功处理 X 个文件"
- 如果有跳过：显示"，跳过 Y 个"

**情况B：部分失败（failed > 0）**
- 黄色标题："批量登分完成（有错误）"
- 红色警告框："以下文件处理失败"
- 失败文件列表（文件名 + 错误原因）
- 底部小字："成功处理 X 个文件，失败 Y 个"

**情况C：完全失败（请求失败）**
- 蓝色标题："批量登分提示"
- 黄色提示框：显示错误信息

### 按钮状态管理

**状态转换流程**:
```
初始状态（禁用）
  ↓ 选择作业文件夹
启用状态（显示作业名称）
  ↓ 点击按钮
处理中（禁用，显示"正在批量登分..."）
  ↓ 处理完成
结果状态（启用，显示"批量登分成功"或"查看提示"）
  ↓ 关闭模态框
恢复状态（启用，显示作业名称）
```

**按钮文本**:
- 初始/未选择: `批量登分`
- 选中作业: `批量登分 (作业名称)`
- 处理中: `正在批量登分...`
- 成功: `批量登分成功`（绿色，3秒后恢复）
- 失败: `查看提示`（黄色，关闭模态框后恢复）

---

## 设置指南

### 问题：批量登分失败 - 未找到作业目录

**原因**: 数据库中没有对应的 Homework（作业）记录，或 `folder_name` 与实际文件夹名称不匹配。


### 解决方案

#### 方法1：使用管理命令自动导入作业（推荐）

```bash
# 预览将要导入的作业（不实际导入）
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称> --dry-run

# 实际导入作业
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>

# 指定默认作业类型（可选）
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称> --default-type lab_report
```

**命令说明**:
- `<仓库路径>`: 作业文件夹所在的完整路径
- `<课程名称>`: 数据库中的课程名称（必须先创建课程）
- `--dry-run`: 预览模式，不实际导入
- `--default-type`: 默认作业类型（`normal` 或 `lab_report`）

**自动判断规则**:
- 如果课程类型是实验课/实践课 → 自动设置为实验报告
- 如果文件夹名称包含"实验"或"lab" → 自动设置为实验报告
- 否则使用默认类型（normal）

#### 方法2：在Django Admin中手动创建作业

1. 访问 http://127.0.0.1:8000/admin/grading/homework/
2. 点击"添加作业"
3. 填写信息：
   - **课程**: 选择对应的课程
   - **标题**: 作业标题（如"第一次作业"）
   - **作业类型**: 普通作业或实验报告
   - **文件夹名称**: 必须与文件系统中的文件夹名称完全一致
4. 保存

#### 方法3：使用诊断脚本排查问题

```bash
conda run -n py313 python scripts/diagnose_batch_grade.py <课程名称> <作业文件夹名称>
```

### 验证作业是否创建成功

**方法1: Django Admin**
访问 http://127.0.0.1:8000/admin/grading/homework/

**方法2: Django Shell**
```bash
conda run -n py313 python manage.py shell
```

```python
from grading.models import Homework, Course

# 查看所有作业
for hw in Homework.objects.all():
    print(f"{hw.course.name} - {hw.title} - {hw.folder_name}")

# 查看特定课程的作业
course = Course.objects.get(name="Python程序设计")
for hw in course.homeworks.all():
    print(f"{hw.title} - {hw.folder_name} - {hw.get_homework_type_display()}")
```

### 文件结构要求

```
仓库/
├── 课程名/
│   ├── 班级名/（可选）
│   │   ├── 作业文件夹/
│   │   │   ├── 学生1_作业.docx
│   │   │   ├── 学生2_作业.docx
│   │   │   └── ...
│   │   └── 班级成绩登记表.xlsx
│   └── 或直接在课程下/
│       ├── 作业文件夹/
│       └── 成绩登记表.xlsx
```

**Word文档要求**:
- 文件名包含学生姓名
- 文档中包含成绩信息（表格或文本）
- 支持的格式: .docx, .doc

**Excel登记表要求**:
- 包含学生姓名列
- 包含对应的作业列
- 格式符合系统要求

---

## 用户界面

### 进度显示

**进度条功能**:
- 实时显示批量登分进度
- 状态文本显示已处理/总数、成功/失败/跳过数量
- 动画效果：处理中显示条纹动画，完成后静态显示

**进度条状态**:
- 蓝色条纹动画：正在处理
- 绿色：处理成功
- 红色：处理失败


### 结果模态框

**显示内容**:
- 作业信息（作业名、课程名、班级名）
- 统计卡片（总数、成功、失败、跳过）
- 失败文件列表及错误原因（如有）
- 成绩登记表路径

### UI规范

**颜色使用**:
- 成功：绿色（#198754）
- 警告/部分失败：黄色（#ffc107）
- 信息：蓝色（#0dcaf0）
- 错误：红色（#dc3545，仅用于错误列表）

**图标使用**:
- 成功：`bi-check-circle` 或 `bi-check-circle-fill`
- 警告：`bi-exclamation-triangle`
- 信息：`bi-info-circle`
- 错误：`bi-x-circle`

**文本规范**:
- 使用友好的语言，不要吓唬用户
- 错误信息要具体、可操作
- 避免使用"失败"、"错误"等负面词汇作为标题
- 使用"提示"、"完成"等中性词汇

---

## 故障排查

### 常见问题诊断

#### 问题1：按钮一直禁用

**可能原因**:
- 未选择课程
- 选择的是文件而不是文件夹
- 作业不存在于数据库

**解决方案**:
1. 确保选择了课程
2. 点击文件夹而不是文件
3. 检查作业是否存在：访问 http://127.0.0.1:8000/admin/grading/homework/

#### 问题2：按钮卡在"正在批量登分..."状态

**最常见原因：浏览器缓存**

**解决步骤**:

1. **清除浏览器缓存（最重要！）**
   - Chrome/Edge: Ctrl+Shift+Delete → 清除缓存的图片和文件
   - Firefox: Ctrl+Shift+Delete → 缓存
   - Safari: Cmd+Option+E
   - **或使用硬刷新**: Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)
   - **或使用无痕模式测试**

2. **检查JavaScript文件版本**
   - 打开开发者工具 → Network标签 → 刷新页面
   - 查找 `grading.js` 文件
   - 检查URL是否包含版本号：`grading.js?v=20251113-6`
   - 检查状态码：应该是200（不是304 Not Modified）

3. **查看控制台日志**
   - 打开开发者工具 → Console标签
   - 点击批量登分按钮后应该看到：
     ```
     === showBatchGradeProcessingState 被调用 ===
     按钮当前状态 - disabled: false html: ...
     按钮已设置为处理中 - disabled: true html: ...
     ```
   - 批量登分完成后应该看到：
     ```
     === showBatchGradeResultState 被调用 ===
     isSuccess: true
     customText: 批量登分成功
     ```

4. **手动恢复按钮状态**
   - 在Console中执行：
     ```javascript
     restoreBatchGradeButtonState()
     ```
   - 或者：
     ```javascript
     $('#batch-grade-btn')
         .removeClass('btn-success btn-danger')
         .prop('disabled', false)
         .html('<i class="bi bi-tasks"></i> 批量登分 (作业名称)')
     ```

#### 问题3：部分文件失败

**原因**:
- 文件格式错误
- 文件名不符合要求
- 文档中没有成绩信息
- 学生姓名在登记表中不存在

**解决方案**:
1. 查看结果模态框中的失败文件列表
2. 根据错误原因修复文件
3. 重新运行批量登分

#### 问题4：进度条不显示

**原因**: 浏览器缓存

**解决方案**:
- 硬刷新：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)
- 清除浏览器缓存
- 使用无痕模式


### 错误处理

#### 错误分类

**跳过（不算错误）**:
- 成绩相同，无需更新
- 计数在 `summary.skipped` 中
- 不显示在错误列表中

**失败（真正的错误）**:
- 未找到匹配的学生
- 无法提取成绩
- 文件格式错误
- 计数在 `summary.failed` 中
- 显示在错误列表中，包含具体原因

#### 错误类型和解决方案

**1. 未找到作业目录**

错误信息：`批量登分失败：未找到作业目录: xxx`

原因：
- 数据库中没有对应的Homework记录
- Homework的folder_name与实际文件夹名称不匹配

解决方案：
```bash
# 使用诊断脚本
conda run -n py313 python scripts/diagnose_batch_grade.py <课程名称> <作业文件夹名称>

# 导入作业
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>
```

**2. 权限错误（403）**

错误信息：`没有权限执行批量登分操作`

原因：
- 用户不是该课程的教师
- 用户权限不足

解决方案：
- 确认您是该课程的教师
- 检查用户权限设置

**3. 未找到资源（404）**

错误信息：`未找到批量登分接口或作业不存在`

原因：
- 作业ID不正确
- 作业记录不存在

解决方案：
- 检查作业ID是否正确
- 确认作业记录存在于数据库中

**4. 服务器错误（500）**

错误信息：`服务器内部错误：xxx`

原因：
- 服务器代码错误
- 数据库错误
- 文件系统错误

解决方案：
- 查看服务器日志：`logs/app.log`
- 联系系统管理员

**5. 网络错误（0）**

错误信息：`网络连接失败，请检查网络连接`

原因：
- 网络断开
- 服务器未运行
- 防火墙阻止

解决方案：
- 检查网络连接
- 确认服务器正在运行
- 检查防火墙设置

### 调试技巧

**查看浏览器控制台**:
- 打开开发者工具（F12）→ Console标签
- 查看JavaScript错误、网络请求详情、错误堆栈信息

**查看网络请求**:
- 开发者工具 → Network标签
- 查看请求URL、参数、响应内容、HTTP状态码

**查看服务器日志**:
```bash
tail -f logs/app.log
```

**使用诊断脚本**:
```bash
conda run -n py313 python scripts/diagnose_batch_grade.py <课程名称> <作业文件夹名称>
```

---

## 测试指南

### 测试前准备

1. 硬刷新浏览器（Ctrl+Shift+R 或 Cmd+Shift+R）
2. 打开开发者工具（F12）
3. 确保有测试数据

### 功能测试清单

#### 1. 按钮状态测试
- [ ] 初始状态：禁用，显示"批量登分"
- [ ] 选择作业后：启用，显示"批量登分 (作业名称)"
- [ ] 处理中：禁用，显示"正在批量登分..."
- [ ] 成功后：绿色，显示"批量登分成功"
- [ ] 失败后：红色，显示"批量登分失败"
- [ ] 关闭模态框后：恢复正常状态

#### 2. 进度显示测试
- [ ] 点击按钮后进度条出现
- [ ] 进度条显示蓝色条纹动画
- [ ] 进度条文本显示处理状态
- [ ] 成功后进度条变绿
- [ ] 失败后进度条变红

#### 3. 成功结果展示测试
- [ ] 弹出结果模态框
- [ ] 显示作业信息（作业名、课程名、班级名）
- [ ] 显示统计卡片（总数、成功、失败、跳过）
- [ ] 如有失败文件，显示失败列表
- [ ] 显示成绩登记表路径
- [ ] 有"确定"按钮
- [ ] 底部显示提示信息

#### 4. 错误处理测试
- [ ] 弹出错误模态框
- [ ] 显示清晰的错误标题
- [ ] 显示错误信息
- [ ] 显示HTTP状态码（如适用）
- [ ] 显示针对性的解决方案
- [ ] 可展开查看技术详情
- [ ] 有"关闭"按钮

#### 5. 按钮恢复测试
- [ ] 关闭成功模态框后按钮恢复
- [ ] 关闭错误模态框后按钮恢复
- [ ] 按钮文本正确
- [ ] 按钮状态正确（启用/禁用）
- [ ] 可以再次点击批量登分


### 错误场景测试

**场景1：未找到作业目录**

操作：选择一个没有Homework记录的文件夹

预期结果：
- [ ] 显示错误模态框
- [ ] 错误信息："未找到作业目录: xxx"
- [ ] 解决方案包含导入命令
- [ ] 解决方案包含诊断脚本使用方法

**场景2：权限错误**

操作：使用非教师账号尝试批量登分

预期结果：
- [ ] 显示错误模态框
- [ ] 错误信息："没有权限执行批量登分操作"
- [ ] HTTP状态码：403
- [ ] 解决方案提示检查权限

**场景3：网络错误**

操作：停止服务器后点击批量登分

预期结果：
- [ ] 显示错误模态框
- [ ] 错误信息："网络连接失败"
- [ ] HTTP状态码：0
- [ ] 解决方案提示检查网络和服务器

**场景4：部分文件失败**

操作：批量登分时部分文件格式错误

预期结果：
- [ ] 显示成功模态框（不是错误模态框）
- [ ] 统计显示失败数量 > 0
- [ ] 显示失败文件列表
- [ ] 每个失败文件显示错误原因

### 用户体验测试

**易用性**:
- [ ] 错误信息清晰易懂
- [ ] 解决方案具体可操作
- [ ] 模态框布局美观
- [ ] 按钮状态变化流畅

**性能**:
- [ ] 模态框打开速度快
- [ ] 按钮状态切换流畅
- [ ] 大量失败文件时不卡顿

**可访问性**:
- [ ] 模态框可用键盘关闭（ESC）
- [ ] 按钮有清晰的提示文本
- [ ] 颜色对比度足够

### 浏览器兼容性
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### 控制台检查

**不应该看到的错误**:
- [ ] JavaScript语法错误
- [ ] 未定义的函数或变量
- [ ] Bootstrap相关错误
- [ ] jQuery相关错误

**应该看到的日志**:
```
=== 更新批量登分按钮状态 ===
批量登分按钮被点击
批量登分失败: xxx (如果失败)
XHR状态: xxx (如果失败)
```

### 回归测试

**其他功能不受影响**:
- [ ] 文件选择功能正常
- [ ] 评分功能正常
- [ ] 教师评价功能正常
- [ ] AI评分功能正常
- [ ] 导航按钮功能正常

### 测试通过标准
- 所有功能测试项通过
- 至少测试3种错误场景
- 在2种以上浏览器测试通过
- 控制台无严重错误
- 用户体验良好

---

## API参考

### 查询作业信息

**端点**: `GET /grading/api/homework-info/`

**参数**:
- `course_name`: 课程名称
- `homework_folder`: 作业文件夹名称

**响应**:
```json
{
  "success": true,
  "homework": {
    "id": 1,
    "title": "第一次作业",
    "folder_name": "第一次作业",
    "homework_type": "normal",
    "course": {
      "id": 1,
      "name": "Python程序设计"
    }
  }
}
```

### 批量登分

**端点**: `POST /grading/homework/{homework_id}/batch-grade-to-registry/`

**参数**:
- `relative_path`: 相对路径（可选）
- `tracking_id`: 跟踪ID（可选）

**成功响应**:
```json
{
  "success": true,
  "message": "批量登分完成",
  "homework_number": 1,
  "homework_name": "第一次作业",
  "course_name": "Python程序设计",
  "class_name": "计算机2301",
  "summary": {
    "total": 30,
    "success": 28,
    "failed": 2,
    "skipped": 17
  },
  "details": {
    "processed_files": [...],
    "failed_files": [
      {
        "file_name": "学生姓名.docx",
        "file_path": "/path/to/file.docx",
        "student_name": "学生姓名",
        "error_message": "具体错误原因",
        "grade": "C",
        "success": false,
        "skipped": false
      }
    ],
    "skipped_files": [...]
  },
  "registry_path": "/path/to/registry.xlsx"
}
```

**失败响应**:
```json
{
  "success": false,
  "message": "错误信息",
  "error": "详细错误"
}
```

### 前端数据访问

```javascript
// 兼容两种数据结构
const data = response.data || response;
const summary = data.summary || data.statistics || {};
const details = data.details || {};

// 失败文件字段
const fileName = file.student_name || file.file_name || file.file;
const errorMsg = file.error_message || file.error || file.message;
```

---

## 技术实现

### 关键函数

- `updateBatchGradeButton(folderPath, folderId)` - 更新按钮状态
- `showBatchGradeProcessingState()` - 显示处理中状态
- `startBatchGradeProgress(trackingId)` - 启动进度显示
- `completeBatchGradeProgress(isSuccess, message)` - 完成进度显示
- `showBatchGradeResultState(isSuccess, customText, autoRestore)` - 显示结果状态
- `showBatchGradeResultModal(data)` - 显示成功结果模态框
- `showBatchGradeErrorModal(errorData)` - 显示错误提示模态框
- `restoreBatchGradeButtonState()` - 恢复按钮状态

### 全局变量

- `currentHomeworkFolder` - 当前作业文件夹名称
- `currentHomeworkId` - 当前作业ID
- `currentHomeworkRelativePath` - 当前作业相对路径
- `currentCourse` - 当前课程名称
- `currentRepoId` - 当前仓库ID

### 事件绑定

- 批量登分按钮点击：`$(document).on('click', '#batch-grade-btn', ...)`
- 文件夹选择：在 jstree 的 `select_node` 事件中调用 `updateBatchGradeButton`
- 模态框关闭：调用 `restoreBatchGradeButtonState` 恢复按钮

### 技术栈

**前端**:
- jQuery 3.x
- Bootstrap 5.x
- JSTree
- 自定义JavaScript（grading.js）

**后端**:
- Django 4.2.20
- Python 3.13
- python-docx（Word文档处理）
- openpyxl（Excel文件处理）

**服务层**:
- `GradeRegistryWriterService` - 批量登分核心服务
- `RegistryManager` - Excel登记表管理

---

## 已知限制

1. 不支持实时进度更新（后端未实现进度查询接口）
2. 不支持取消操作
3. 不支持批量重试失败文件
4. 处理大量文件时可能超时

## 后续改进建议

1. 实现后端进度查询接口
2. 添加取消功能
3. 添加重试失败文件功能
4. 添加批量操作历史记录
5. 优化大文件处理性能
6. 添加导出结果报告功能
7. 添加邮件通知功能

---

## 相关文档

- [设计文档](../.kiro/specs/grade-registry-writer/design.md) - 批量登分功能设计
- [已知问题](./KNOWN_ISSUES.md) - 系统已知问题
- [开发指南](./DEVELOPMENT.md) - 开发环境配置

## 相关代码

- `grading/views.py` - 主要业务逻辑
- `grading/services/grade_registry_writer_service.py` - 批量登分服务
- `templates/grading_simple.html` - 评分页面
- `grading/static/grading/js/grading.js` - 前端交互
- `scripts/diagnose_batch_grade.py` - 诊断脚本

---

**文档版本**: 2.0 (整合版)  
**最后更新**: 2025-11-19  
**维护者**: 开发团队
