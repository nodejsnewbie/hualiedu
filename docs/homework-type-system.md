# 作业类型系统文档

## 概述

作业类型系统用于区分普通作业和实验报告，并根据类型采用不同的评分方式。

## 核心功能

### 1. 作业类型定义

作业类型在 `Homework` 模型中定义：

```python
class Homework(models.Model):
    HOMEWORK_TYPE_CHOICES = [
        ('normal', '普通作业'),
        ('lab_report', '实验报告'),
    ]
    
    homework_type = models.CharField(
        max_length=20,
        choices=HOMEWORK_TYPE_CHOICES,
        default='normal',
        verbose_name='作业类型'
    )
```

### 2. 自动类型判断

系统会根据以下优先级自动判断作业类型：

1. **数据库查询**（最准确）
   - 根据课程名和作业批次从数据库查询
   - 使用 `Homework.objects.filter(course__name=课程名, folder_name=作业批次)`

2. **课程类型判断**
   - 如果数据库中没有作业记录，根据课程类型判断
   - 实验课的作业默认为实验报告

3. **关键词判断**（兜底）
   - 如果课程不在数据库中，根据关键词判断
   - 包含"实验"、"lab"、"experiment"等关键词的为实验课

### 3. 评分方式差异

**实验报告：**
- 评分写入文档中的表格（查找"教师（签字）"单元格）
- 如果表格格式不正确，自动降级为C评分并提示学生

**普通作业：**
- 评分以段落形式添加到文档末尾
- 格式：`老师评分：A`

### 4. 前端显示

前端会根据作业类型显示不同的标签：
- 实验报告：显示红色"实验报告"标签
- 普通作业：显示蓝色"普通作业"标签

## 使用指南

### 管理作业类型

1. **扫描课程**
```bash
python manage.py scan_courses
```

2. **导入作业批次**
```bash
python manage.py import_homeworks
```

3. **更新课程类型**
```bash
python manage.py update_course_types
```

### 手动设置作业类型

在批改界面中，可以点击作业批次旁的标签来修改作业类型。

## 技术实现

### 路径解析

系统从文件路径中提取课程名和作业批次：

```
路径格式：课程名/班级/作业批次/文件名
示例：Web前端开发/23计算机5班/第一次作业/张三.docx
```

解析逻辑会跳过中间的仓库目录（如 `linyuan/homework`）。

### 实验报告表格写入

```python
def write_grade_to_lab_report(doc, grade, comment=None):
    # 查找包含"教师（签字）"的表格
    # 在对应单元格中写入评分和评价
```

### 安全的文档修改

为避免损坏Word文档，系统采用以下策略：
- 不删除段落，只更新现有段落的内容
- 如果没有现有评分段落，才添加新段落

## 数据库结构

```sql
-- Homework表
CREATE TABLE homework (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    folder_name VARCHAR(255),
    homework_type VARCHAR(20) DEFAULT 'normal',
    created_at DATETIME,
    updated_at DATETIME
);
```

## API接口

### 保存作业类型
```
POST /grading/save_homework_type/
参数：
  - course: 课程名
  - homework_folder: 作业批次
  - homework_type: 作业类型（normal/lab_report）
```

### 获取作业类型
```
GET /grading/get_homework_type/
参数：
  - course: 课程名
  - homework_folder: 作业批次
```

## 注意事项

1. **实验报告格式要求**
   - 必须包含"教师（签字）"表格
   - 表格格式不正确会自动降级为C评分

2. **路径解析**
   - 确保文件路径符合标准格式
   - 班级名称应包含"班"字或"class"

3. **文档安全**
   - 系统会自动备份（通过Git）
   - 建议定期提交作业仓库的更改

## 故障排除

### 作业类型判断不准确
- 检查数据库中是否有对应的作业记录
- 运行 `python manage.py import_homeworks` 重新导入

### 实验报告评分失败
- 检查文档是否包含"教师（签字）"表格
- 查看后台日志了解详细错误信息

### 文档损坏
- 使用 `git restore .` 恢复文件
- 检查是否有并发写入问题
