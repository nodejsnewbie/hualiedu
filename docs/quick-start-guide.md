# 快速开始指南

## 初始化系统

### 1. 创建学期

```bash
python manage.py shell
```

```python
from grading.models import Semester
from datetime import date

# 创建当前学期
semester = Semester.objects.create(
    name='2025年秋季学期',
    start_date=date(2025, 9, 1),
    end_date=date(2026, 1, 15),
    is_active=True
)
print(f'创建学期: {semester.name}')
```

### 2. 扫描并创建课程

```bash
# 预览将要创建的课程
python manage.py scan_courses /path/to/repo --dry-run

# 实际创建课程
python manage.py scan_courses /path/to/repo

# 指定教师
python manage.py scan_courses /path/to/repo --teacher username
```

### 3. 调整课程类型（如需要）

```bash
python manage.py shell
```

```python
from grading.models import Course

# 查看所有课程
for c in Course.objects.all():
    print(f'{c.name}: {c.course_type} ({c.get_course_type_display()})')

# 修改课程类型
course = Course.objects.get(name='Web前端开发')
course.course_type = 'lab'  # theory/lab/practice/mixed
course.save()
print(f'已更新: {course.name} -> {course.get_course_type_display()}')
```

## 使用流程

### 方式1：自动创建（推荐）

前端调用API时，系统会自动创建课程：

```javascript
// 获取课程信息（自动创建）
fetch(`/grading/api/course-info/?course_name=Web前端开发&auto_create=true`)
    .then(res => res.json())
    .then(data => {
        console.log(data.course.course_type_display);  // "实验课"
        if (data.course.auto_created) {
            console.log('课程已自动创建');
        }
    });
```

### 方式2：批量扫描

定期运行扫描命令，自动发现新课程：

```bash
# 每学期开始时运行一次
python manage.py scan_courses /path/to/repo
```

## 课程类型识别规则

系统根据课程名称自动识别类型：

| 关键词 | 课程类型 | 说明 |
|--------|----------|------|
| 实验、lab、experiment | lab | 实验课 |
| 实训、practice、实践 | practice | 实践课 |
| 理论与实验、理论+实验、mixed | mixed | 混合课 |
| 其他 | theory | 理论课（默认） |

## 手动管理

### 在Django Admin中管理

1. 访问 `/admin/grading/course/`
2. 添加或编辑课程
3. 设置课程类型

### 批量更新

```bash
python manage.py shell
```

```python
from grading.models import Course

# 批量更新包含"实验"的课程
Course.objects.filter(name__contains='实验').update(course_type='lab')

# 批量更新包含"实训"的课程
Course.objects.filter(name__contains='实训').update(course_type='practice')
```

## API使用

### 获取课程信息

```
GET /grading/api/course-info/?course_name=Web前端开发&auto_create=true

响应：
{
    "success": true,
    "course": {
        "id": 1,
        "name": "Web前端开发",
        "course_type": "lab",
        "course_type_display": "实验课",
        "in_database": true,
        "auto_created": false
    }
}
```

参数说明：
- `course_name`: 课程名称（必需）
- `auto_create`: 是否自动创建课程（默认true）

响应字段：
- `in_database`: 课程是否在数据库中
- `auto_created`: 是否为本次请求自动创建

## 常见问题

### Q1: 课程类型识别不准确？

**解决方案**：
1. 在课程名称中包含关键词（如"实验"、"lab"）
2. 或者手动修改课程类型
3. 或者在Django Admin中设置

### Q2: 自动创建失败？

**可能原因**：
- 没有可用的学期
- 没有可用的教师用户

**解决方案**：
```bash
# 创建学期
python manage.py shell -c "from grading.models import Semester; from datetime import date; Semester.objects.create(name='2025年秋季学期', start_date=date(2025,9,1), end_date=date(2026,1,15), is_active=True)"

# 创建教师用户
python manage.py createsuperuser
```

### Q3: 如何禁用自动创建？

在API调用时设置 `auto_create=false`：

```javascript
fetch(`/grading/api/course-info/?course_name=Web前端开发&auto_create=false`)
```

## 推荐工作流程

### 学期开始时

1. 创建新学期
2. 运行 `scan_courses` 扫描所有课程
3. 在Django Admin中调整课程类型（如需要）
4. 导入作业信息（如需要）

### 日常使用

- 前端自动调用API，系统自动识别课程类型
- 新增课程会自动创建
- 定期检查和调整课程设置

### 学期结束时

- 将当前学期设置为非活跃
- 创建下学期
- 重新扫描课程

## 相关命令

```bash
# 扫描课程
python manage.py scan_courses <repo_path> [--dry-run] [--teacher username]

# 更新课程类型
python manage.py update_course_types [--dry-run]

# 导入作业
python manage.py import_homeworks <repo_path> <course_name> [--dry-run]
```

## 相关文档

- [作业管理指南](homework-management-guide.md)
- [数据库迁移指南](database-migration-guide.md)
- [功能文档](features/homework-grading.md)
