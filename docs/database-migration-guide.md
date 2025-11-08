# 数据库迁移指南

## 课程类型字段迁移

### 背景

为了支持实验报告的自动识别，我们在 `Course` 模型中添加了 `course_type` 字段。

### 迁移步骤

#### 1. 执行数据库迁移

```bash
python manage.py migrate grading
```

这将执行以下迁移：
- `0015_add_course_type`：添加 `course_type` 字段
- `0016_update_existing_course_types`：自动更新现有课程的类型

#### 2. 验证迁移结果

```bash
python manage.py shell -c "from grading.models import Course; print([f.name for f in Course._meta.get_fields()])"
```

应该能看到 `course_type` 字段。

#### 3. 查看课程类型

```bash
python manage.py shell -c "from grading.models import Course; [print(f'{c.name}: {c.course_type}') for c in Course.objects.all()]"
```

### 课程类型说明

| 类型 | 值 | 说明 | 作业格式 |
|------|-----|------|----------|
| 理论课 | `theory` | 普通理论课程 | 普通作业（段落格式） |
| 实验课 | `lab` | 实验课程 | 实验报告（表格格式） |
| 实践课 | `practice` | 实践课程 | 实验报告（表格格式） |
| 理论+实验 | `mixed` | 理论与实验结合 | 实验报告（表格格式） |

### 手动更新课程类型

#### 方法1：使用管理命令（推荐）

**预览将要更新的课程**：
```bash
python manage.py update_course_types --dry-run
```

**实际更新课程类型**：
```bash
python manage.py update_course_types
```

这个命令会根据课程名称自动判断：
- 包含"实验"、"lab"、"experiment"、"实训"、"practice"等关键词 → `lab`
- 其他 → 保持 `theory`

#### 方法2：在Django Shell中手动更新

```bash
python manage.py shell
```

```python
from grading.models import Course

# 更新单个课程
course = Course.objects.get(name='Web前端开发实验')
course.course_type = 'lab'
course.save()

# 批量更新包含"实验"的课程
Course.objects.filter(name__contains='实验').update(course_type='lab')

# 批量更新包含"lab"的课程
Course.objects.filter(name__icontains='lab').update(course_type='lab')
```

#### 方法3：在Django Admin中手动更新

1. 访问 Django Admin：`http://localhost:8000/admin/`
2. 进入"课程"管理页面
3. 编辑每个课程，设置正确的课程类型
4. 保存

### 自动识别逻辑

系统会按以下优先级判断是否为实验报告：

1. **手动指定**（最高优先级）
   - API参数：`is_lab_report=true`

2. **数据库查询**
   - 根据课程名称查询 `Course` 表
   - 检查 `course_type` 字段
   - `lab`/`practice`/`mixed` → 实验报告

3. **关键词匹配**（备用方法）
   - 课程名称包含：实验、lab、experiment、实训、practice
   - → 实验报告

4. **路径提取**
   - 从文件路径中提取课程名称
   - 按上述方法判断

### 常见问题

#### Q1: 迁移失败怎么办？

**错误**：`django.db.utils.OperationalError: no such column: grading_course.course_type`

**解决**：
```bash
python manage.py migrate grading 0015_add_course_type
```

#### Q2: 如何回滚迁移？

```bash
python manage.py migrate grading 0014_merge_20251108_1157
```

这会删除 `course_type` 字段。

#### Q3: 如何重新运行数据迁移？

```bash
# 回滚到0015
python manage.py migrate grading 0015_add_course_type

# 重新运行0016
python manage.py migrate grading 0016_update_existing_course_types
```

#### Q4: 现有课程没有自动更新类型？

运行管理命令：
```bash
python manage.py update_course_types
```

### 测试验证

#### 1. 创建测试课程

```python
from grading.models import Course, Semester
from django.contrib.auth.models import User

semester = Semester.objects.first()
teacher = User.objects.first()

# 创建理论课
Course.objects.create(
    name='数据结构',
    course_type='theory',
    semester=semester,
    teacher=teacher,
    location='教学楼101'
)

# 创建实验课
Course.objects.create(
    name='Web前端开发实验',
    course_type='lab',
    semester=semester,
    teacher=teacher,
    location='实验室201'
)
```

#### 2. 测试自动识别

```python
from grading.views import is_lab_report_file

# 测试1：根据课程名称
result = is_lab_report_file(course_name='Web前端开发实验')
print(f"实验课识别结果: {result}")  # 应该是 True

result = is_lab_report_file(course_name='数据结构')
print(f"理论课识别结果: {result}")  # 应该是 False

# 测试2：根据文件路径
result = is_lab_report_file(
    file_path='/path/to/repo/Web前端开发实验/作业1/张三.docx',
    base_dir='/path/to/repo'
)
print(f"路径识别结果: {result}")  # 应该是 True
```

### 数据备份建议

在执行迁移前，建议备份数据库：

```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup

# PostgreSQL
pg_dump dbname > backup.sql

# MySQL
mysqldump -u username -p dbname > backup.sql
```

### 相关文件

- 迁移文件：
  - `grading/migrations/0015_add_course_type.py`
  - `grading/migrations/0016_update_existing_course_types.py`
  
- 管理命令：
  - `grading/management/commands/update_course_types.py`
  
- 模型定义：
  - `grading/models.py` - `Course` 模型
  
- 识别逻辑：
  - `grading/views.py` - `is_lab_report_file()` 函数

### 更新日志

- **2025-11-08**：添加 `course_type` 字段，支持实验报告自动识别
