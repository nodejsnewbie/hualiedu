# 批量登分功能设置指南

## 问题：批量登分失败 - 未找到作业目录

### 原因
批量登分功能需要数据库中有对应的 Homework（作业）记录。如果数据库中没有作业记录，或者作业的 `folder_name` 与实际文件夹名称不匹配，就会出现"未找到作业目录"的错误。

## 解决方案

### 方法1：使用管理命令自动导入作业

使用 `import_homeworks` 命令从文件系统自动扫描并创建作业记录。

#### 步骤：

1. **预览将要导入的作业**（不实际导入）：
```bash
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称> --dry-run
```

例如：
```bash
conda run -n py313 python manage.py import_homeworks /path/to/repo/Python程序设计 Python程序设计 --dry-run
```

2. **实际导入作业**：
```bash
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称>
```

3. **指定默认作业类型**（可选）：
```bash
conda run -n py313 python manage.py import_homeworks <仓库路径> <课程名称> --default-type lab_report
```

#### 命令说明：
- `<仓库路径>`：作业文件夹所在的完整路径
- `<课程名称>`：数据库中的课程名称（必须先创建课程）
- `--dry-run`：预览模式，不实际导入
- `--default-type`：默认作业类型（`normal` 或 `lab_report`）

#### 自动判断规则：
- 如果课程类型是实验课/实践课，自动设置为实验报告
- 如果文件夹名称包含"实验"或"lab"，自动设置为实验报告
- 否则使用默认类型（normal）

### 方法2：在Django Admin中手动创建作业

1. 访问 Django Admin：http://127.0.0.1:8000/admin/
2. 进入"作业"管理页面
3. 点击"添加作业"
4. 填写信息：
   - **课程**：选择对应的课程
   - **标题**：作业标题（如"第一次作业"）
   - **作业类型**：普通作业或实验报告
   - **文件夹名称**：必须与文件系统中的文件夹名称完全一致
5. 保存

### 方法3：使用API创建作业

发送POST请求到作业创建API（需要实现）。

## 验证作业是否创建成功

### 方法1：Django Admin
访问 http://127.0.0.1:8000/admin/grading/homework/

### 方法2：Django Shell
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

## 常见问题

### Q: 导入时提示"课程不存在"
A: 需要先创建课程。可以通过Django Admin或使用管理命令创建。

### Q: 文件夹名称包含特殊字符
A: 确保数据库中的 `folder_name` 与文件系统中的文件夹名称完全一致，包括空格、中文等。

### Q: 批量登分时仍然提示"未找到作业目录"
A: 检查以下几点：
1. 数据库中是否有对应的 Homework 记录
2. Homework 的 `folder_name` 是否与实际文件夹名称一致
3. 文件夹路径是否正确（检查是否有班级子目录）
4. 查看服务器日志获取详细错误信息
5. 系统会尝试在仓库中回退搜索同名目录，如果日志提示"检测到多个同名作业目录"，需要清理重复目录或为课程设置准确的班级/作业信息

## 调试技巧

### 查看前端传递的参数
打开浏览器开发者工具 → Console，查看日志：
```
=== 更新批量登分按钮状态 ===
文件夹路径: ...
提取的文件夹名称: ...
当前课程名称: ...
```

### 查看后端日志
检查 `logs/app.log` 文件，查找相关错误信息。

### 测试API
使用curl测试作业信息API：
```bash
curl "http://127.0.0.1:8000/grading/api/homework-info/?course_name=Python程序设计&homework_folder=第一次作业"
```

应该返回：
```json
{
  "success": true,
  "homework": {
    "id": 1,
    "title": "第一次作业",
    "folder_name": "第一次作业",
    ...
  }
}
```
