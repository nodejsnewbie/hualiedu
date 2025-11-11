# 作业评分系统设计文档

## 概述

作业评分系统用于教师对学生提交的作业进行评分和评价。系统支持两种作业类型：实验报告和普通作业，采用不同的评分写入格式。

## 核心设计原则

1. **统一函数设计**：所有操作使用统一的定位、提取和写入函数
2. **类型优先级**：作业批次类型 > 课程类型 > 关键词匹配
3. **格式验证**：自动检测实验报告格式，错误时自动降级处理
4. **锁定机制**：格式错误的文件被锁定，防止误操作

## 架构设计

### 评分写入流程

```
判断作业类型
  ↓
实验报告？
  ├─ 是 → 查找"教师（签字）"单元格
  │       ├─ 找到 → 清除旧内容 → 写入新内容（表格）
  │       └─ 未找到 → 格式错误 → 降级处理（D评分+锁定）
  └─ 否 → 写入文档末尾（段落）
```

### 作业类型判断流程

```
1. 查询作业批次
   ├─ 找到 → 使用 homework_type
   └─ 未找到 → 查询课程类型
       ├─ lab/practice/mixed → 实验报告
       └─ theory → 普通作业
2. 路径解析（提取课程名和作业文件夹名）
3. 关键词匹配（课程名包含"实验"、"lab"等）
4. 默认为普通作业
```

## 组件和接口

### 核心统一函数

#### 1. find_teacher_signature_cell(doc)
**功能**：定位"教师（签字）"单元格

**输入**：
- `doc`: Document对象

**输出**：
- `(cell, table_idx, row_idx, col_idx)` 或 `(None, None, None, None)`

**位置**：`grading/views.py:4019`

#### 2. extract_grade_and_comment_from_cell(cell)
**功能**：提取评分、评价和签字文本

**输入**：
- `cell`: 单元格对象

**输出**：
- `(grade, comment, signature_text)`

**逻辑**：
1. 查找"教师（签字）："所在行
2. 提取之前的内容（评分和评价）
3. 保留"教师（签字）："及之后的内容

**位置**：`grading/views.py:4037`

#### 3. write_to_teacher_signature_cell(cell, grade, comment, signature_text)
**功能**：写入评分、评价和签字文本

**输入**：
- `cell`: 单元格对象
- `grade`: 评分
- `comment`: 评价
- `signature_text`: 签字文本

**逻辑**：
1. 清空单元格
2. 写入评分（第一行，居中，加粗，14号）
3. 写入评价（第二行，左对齐，11号）
4. 写入签字文本（第三行及之后，左对齐，10号）

**位置**：`grading/views.py:4115`

### 高层封装函数

#### write_grade_to_lab_report(doc, grade, comment=None)
**功能**：实验报告评分写入

**流程**：
1. 调用 `find_teacher_signature_cell` 定位
2. 调用 `extract_grade_and_comment_from_cell` 提取
3. 调用 `write_to_teacher_signature_cell` 写入

**位置**：`grading/views.py:4180`

#### write_grade_and_comment_to_file(full_path, grade, comment, base_dir, is_lab_report)
**功能**：统一的文件写入接口

**流程**：
1. 检查文件是否被锁定
2. 判断作业类型
3. 实验报告 → `write_grade_to_lab_report`
4. 普通作业 → 写入段落

**位置**：`grading/views.py:4228`

### 作业类型判断

#### is_lab_report_file(course_name, homework_folder, file_path, base_dir)
**功能**：判断文件是否为实验报告

**优先级**：
1. 作业批次类型（Homework.homework_type）
2. 课程类型（Course.course_type）
3. 路径解析
4. 关键词匹配

**位置**：`grading/views.py:372`

## 数据模型

### Homework模型
```python
class Homework(models.Model):
    HOMEWORK_TYPE_CHOICES = [
        ('normal', '普通作业'),
        ('lab_report', '实验报告'),
    ]
    
    course = ForeignKey(Course)
    folder_name = CharField(max_length=200)
    homework_type = CharField(
        max_length=20,
        choices=HOMEWORK_TYPE_CHOICES,
        default='normal'
    )
```

### Course模型
```python
class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('theory', '理论课'),
        ('lab', '实验课'),
        ('practice', '实践课'),
        ('mixed', '理论+实验'),
    ]
    
    name = CharField(max_length=200)
    course_type = CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='theory'
    )
```

## 错误处理

### 格式错误处理

**触发条件**：
- 文件判定为实验报告
- 文档中没有"教师（签字）"单元格

**处理流程**：
1. 评分自动改为 **D**
2. 评价设置为：**"【格式错误-已锁定】请按要求的格式写实验报告，此评分不可修改"**
3. 按普通作业方式写入（文档末尾段落）
4. 文件被锁定

**锁定机制**：
- 标记：`【格式错误-已锁定】`
- 效果：后续评分操作被拒绝
- 解锁：需手动删除标记或学生重新提交

### 日志记录

```python
logger.info("✓ 成功操作")
logger.warning("! 警告信息")
logger.error("✗ 错误信息")
```

## 测试策略

### 单元测试
1. `find_teacher_signature_cell` - 定位功能
2. `extract_grade_and_comment_from_cell` - 提取功能
3. `write_to_teacher_signature_cell` - 写入功能
4. `is_lab_report_file` - 类型判断

### 集成测试
1. 手动评分流程（新建和更新）
2. AI评分流程
3. 获取评价功能
4. 撤销评分功能
5. 格式错误处理

### 边界测试
1. 没有"教师（签字）"单元格
2. 单元格内容为空
3. 只有签字文本没有评分
4. 有评分但没有评价
5. 文件已被锁定

## 性能优化

### 缓存机制
- 目录文件数量缓存
- 避免重复计算

### 懒加载
- 目录树按需加载子目录
- 减少初始加载时间

## 相关文档

- [需求文档](./requirements.md)
- [快速参考](../../docs/SUMMARY.md)
