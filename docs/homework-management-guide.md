# 作业管理指南

## 概述

系统采用三层架构管理作业：
1. **课程（Course）**：定义课程类型（理论课/实验课等）
2. **作业（Homework）**：定义每次作业的类型（普通作业/实验报告）
3. **文件系统**：存储实际的作业文件

## 数据模型

### Course（课程）

```python
class Course:
    name: str                    # 课程名称
    course_type: str             # 课程类型
    # - theory: 理论课
    # - lab: 实验课
    # - practice: 实践课
    # - mixed: 理论+实验
```

### Homework（作业）

```python
class Homework:
    course: Course               # 所属课程
    title: str                   # 作业标题
    homework_type: str           # 作业类型
    # - normal: 普通作业
    # - lab_report: 实验报告
    folder_name: str             # 文件夹名称（用于匹配文件系统）
    description: str             # 作业描述
    due_date: datetime           # 截止日期
```

## 使用流程

### 1. 创建课程

在Django Admin中创建课程：

```
课程名称：Web前端开发
课程类型：lab（实验课）
```

### 2. 创建作业

#### 方法1：在Django Admin中手动创建

1. 访问 `/admin/grading/homework/`
2. 点击"添加作业"
3. 填写信息：
   - 课程：选择课程
   - 标题：第一次作业
   - 作业类型：实验报告
   - 文件夹名称：第一次作业（必须与文件系统中的目录名一致）

#### 方法2：使用管理命令批量导入

```bash
# 预览将要导入的作业
python manage.py import_homeworks /path/to/repo "Web前端开发" --dry-run

# 实际导入
python manage.py import_homeworks /path/to/repo "Web前端开发"

# 指定默认类型
python manage.py import_homeworks /path/to/repo "数据结构" --default-type normal
```

### 3. 文件系统结构

```
仓库目录/
├── Web前端开发/           # 课程目录
│   ├── 23计算机5班/       # 班级目录
│   │   ├── 第一次作业/    # 作业目录（对应Homework.folder_name）
│   │   │   ├── 张三.docx
│   │   │   └── 李四.docx
│   │   └── 第二次作业/
│   │       ├── 张三.docx
│   │       └── 李四.docx
│   └── 24计算机6班/
│       └── ...
```

## API接口

### 获取课程信息

```
GET /grading/api/course-info/?course_name=Web前端开发

响应：
{
    "success": true,
    "course": {
        "id": 1,
        "name": "Web前端开发",
        "course_type": "lab",
        "course_type_display": "实验课",
        "description": "..."
    }
}
```

### 获取作业列表

```
GET /grading/api/homework-list/?course_name=Web前端开发

响应：
{
    "success": true,
    "course_name": "Web前端开发",
    "homeworks": [
        {
            "id": 1,
            "title": "第一次作业",
            "homework_type": "lab_report",
            "homework_type_display": "实验报告",
            "folder_name": "第一次作业",
            "description": "...",
            "due_date": "2025-11-15T23:59:59"
        },
        ...
    ]
}
```

### 获取作业信息

```
GET /grading/api/homework-info/?course_name=Web前端开发&homework_folder=第一次作业

响应：
{
    "success": true,
    "homework": {
        "id": 1,
        "title": "第一次作业",
        "homework_type": "lab_report",
        "homework_type_display": "实验报告",
        "folder_name": "第一次作业",
        "is_lab_report": true,
        ...
    }
}
```

## 前端集成

### 1. 用户选择课程时

```javascript
// 获取课程信息
fetch(`/grading/api/course-info/?course_name=${courseName}`)
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // 显示课程类型
            console.log(`课程类型: ${data.course.course_type_display}`);
            
            // 根据课程类型显示提示
            if (data.course.course_type === 'lab') {
                showMessage('这是实验课，作业将使用实验报告格式');
            }
        }
    });
```

### 2. 用户选择作业时

```javascript
// 获取作业信息
fetch(`/grading/api/homework-info/?course_name=${courseName}&homework_folder=${homeworkFolder}`)
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // 显示作业类型
            console.log(`作业类型: ${data.homework.homework_type_display}`);
            
            // 根据作业类型调整UI
            if (data.homework.is_lab_report) {
                showLabReportUI();  // 显示实验报告评分界面
            } else {
                showNormalHomeworkUI();  // 显示普通作业评分界面
            }
        }
    });
```

### 3. 评分时传递参数

```javascript
// 保存评分
fetch('/grading/add_grade_to_file/', {
    method: 'POST',
    body: JSON.stringify({
        path: filePath,
        grade: grade,
        course: courseName,
        homework_folder: homeworkFolder,  // 新增参数
        repo_id: repoId
    })
});
```

## 自动识别逻辑

系统按以下优先级判断作业类型：

1. **数据库查询**（最准确）
   - 根据 `course_name` 和 `homework_folder` 查询 `Homework` 表
   - 返回 `homework_type`

2. **文件路径提取**
   - 从文件路径提取课程名和作业文件夹名
   - 查询数据库

3. **课程类型判断**（备用）
   - 根据课程类型判断
   - `lab`/`practice`/`mixed` → 实验报告

4. **关键词匹配**（最后备用）
   - 课程名或作业名包含"实验"等关键词 → 实验报告

## 管理命令

### 导入作业

```bash
# 基本用法
python manage.py import_homeworks <仓库路径> <课程名称>

# 预览模式
python manage.py import_homeworks /path/to/repo "Web前端开发" --dry-run

# 指定默认类型
python manage.py import_homeworks /path/to/repo "数据结构" --default-type normal
```

### 更新课程类型

```bash
python manage.py update_course_types --dry-run
python manage.py update_course_types
```

## 最佳实践

### 1. 课程设置

- 创建课程时，正确设置课程类型
- 实验课程选择 `lab` 类型
- 理论课程选择 `theory` 类型

### 2. 作业管理

- 每次作业创建对应的 `Homework` 记录
- `folder_name` 必须与文件系统中的目录名完全一致
- 明确设置作业类型（`normal` 或 `lab_report`）

### 3. 文件系统

- 保持规范的目录结构：`课程/班级/作业/文件`
- 作业目录名要有意义，如"第一次作业"、"实验一"等
- 避免使用特殊字符

### 4. 灵活性

- 同一门实验课可以有普通作业
- 同一门理论课可以有实验报告
- 每次作业的类型独立设置

## 示例场景

### 场景1：纯实验课

```python
# 课程设置
Course(name="Web前端开发实验", course_type="lab")

# 作业设置
Homework(title="实验一", homework_type="lab_report")
Homework(title="实验二", homework_type="lab_report")
Homework(title="期末报告", homework_type="lab_report")
```

### 场景2：理论+实验混合课

```python
# 课程设置
Course(name="数据结构", course_type="mixed")

# 作业设置
Homework(title="第一次作业", homework_type="normal")      # 理论作业
Homework(title="实验一", homework_type="lab_report")       # 实验报告
Homework(title="第二次作业", homework_type="normal")       # 理论作业
Homework(title="实验二", homework_type="lab_report")       # 实验报告
```

### 场景3：纯理论课

```python
# 课程设置
Course(name="计算机网络", course_type="theory")

# 作业设置
Homework(title="第一次作业", homework_type="normal")
Homework(title="第二次作业", homework_type="normal")
Homework(title="期末论文", homework_type="normal")
```

## 故障排查

### Q1: 作业类型识别不正确

**检查步骤**：
1. 确认 `Homework` 记录是否存在
2. 确认 `folder_name` 是否与文件系统一致
3. 查看日志了解识别过程

### Q2: 无法导入作业

**可能原因**：
- 课程不存在
- 路径不正确
- 目录名包含特殊字符

### Q3: 前端无法获取作业信息

**检查步骤**：
1. 确认API参数正确
2. 确认课程名和作业文件夹名正确
3. 查看浏览器控制台错误

## 相关文件

- 模型定义：`grading/models.py`
- API接口：`grading/views.py`
- URL路由：`grading/urls.py`
- 管理命令：`grading/management/commands/import_homeworks.py`
- 迁移文件：`grading/migrations/0017_add_homework_model.py`
