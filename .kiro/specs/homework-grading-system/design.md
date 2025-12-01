# 作业评分系统设计文档

## 概述

作业评分系统是一个基于Django的多租户Web应用，支持教师创建课程和班级，配置两种作业存储方式（Git仓库和文件系统），对学生作业进行评分和评价。系统支持三种评分方式（字母、文字、百分制），提供手动评分和AI辅助评分功能，并具备评价缓存和模板功能以提高评分效率。

## 核心设计原则

1. **统一函数设计**：所有操作使用统一的定位、提取和写入函数
2. **类型优先级**：作业批次类型 > 课程类型 > 关键词匹配
3. **格式验证**：自动检测实验报告格式，错误时自动降级处理
4. **锁定机制**：格式错误的文件被锁定，防止误操作
5. **双模式支持**：Git仓库方式和文件系统方式可同时使用
6. **统一目录结构**：强制"课程/班级/作业批次/学生作业"结构
7. **实验报告强制评价**：实验报告必须包含评价内容
8. **评价智能化**：支持评价缓存和常用评价模板

## 架构约束

### 统一函数使用规范

**约束来源**: 从需求文档移入，作为实现层面的架构约束

**强制要求**:
1. 所有需要定位"教师（签字）"单元格的功能必须使用 `find_teacher_signature_cell` 函数
2. 所有需要提取单元格内容的功能必须使用 `extract_grade_and_comment_from_cell` 函数
3. 所有需要写入单元格内容的功能必须使用 `write_to_teacher_signature_cell` 函数
4. 禁止在业务逻辑中直接操作 Word 文档单元格，必须通过统一函数
5. 修改定位逻辑时只需修改统一函数，不应影响调用方

**受影响的功能**:
- 手动评分功能 (`add_grade_to_file`)
- 教师评价功能 (`save_teacher_comment`)
- 获取评价功能 (`get_teacher_comment`)
- 撤销评分功能 (`remove_grade`)
- AI评分功能 (`ai_score_view`)
- 批量评分功能
- 批量AI评分功能

### 性能约束

1. **文件大小限制**: 单个文件最大 50MB
2. **批量操作限制**: 单次批量操作最多 500 个文件
3. **响应时间要求**:
   - 文件内容显示: ≤ 2秒
   - 目录树首次加载: ≤ 3秒
   - 缓存命中响应: ≤ 500毫秒
4. **并发限制**: AI评分速率限制为每秒最多 2 个请求

## 架构设计

### 系统架构层次

```
┌─────────────────────────────────────────┐
│         表现层 (Presentation)            │
│  - Django Templates                     │
│  - JavaScript (评价缓存、模板选择)       │
│  - AJAX API                             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          业务逻辑层 (Business)           │
│  - 课程/班级管理                         │
│  - 仓库配置管理                          │
│  - 评分服务                              │
│  - 评价模板服务                          │
│  - AI评分服务                            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          数据访问层 (Data)               │
│  - Django ORM                           │
│  - 文件系统操作                          │
│  - Git操作 (GitPython)                  │
│  - 浏览器本地存储 (评价缓存)             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          存储层 (Storage)                │
│  - PostgreSQL/SQLite (元数据)           │
│  - 文件系统 (作业文件)                   │
│  - Git仓库 (远程作业)                    │
└─────────────────────────────────────────┘
```

### 仓库管理架构

```
Teacher创建课程和班级
         ↓
选择仓库方式
    ├─ Git仓库方式
    │   ├─ 配置URL、分支、认证
    │   ├─ 验证连接
    │   └─ 直接访问远程仓库
    │
    └─ 文件系统方式
        ├─ 系统分配存储空间
        ├─ 生成目录名 (基于用户名)
        ├─ 处理重名 (添加数字后缀)
        └─ 学生可上传作业
         ↓
统一目录结构验证
课程/班级/作业批次/学生作业
```

### 评分写入流程

```
判断作业类型
  ↓
实验报告？
  ├─ 是 → 验证是否有评价
  │       ├─ 无评价 → 阻止保存，提示必须添加评价
  │       └─ 有评价 → 查找"教师（签字）"单元格
  │                   ├─ 找到 → 清除旧内容 → 写入评分+评价（表格）
  │                   └─ 未找到 → 格式错误 → 降级处理（D评分+锁定）
  └─ 否 → 写入文档末尾（段落）
```

### 评价缓存和模板流程

```
Teacher打开评价对话框
         ↓
    加载评价模板
    ├─ 个人常用评价 (Top 5)
    └─ 系统常用评价 (补充到5个)
         ↓
    Teacher输入评价
         ↓
    每2秒自动缓存到浏览器本地存储
         ↓
    Teacher保存评价
         ↓
    ├─ 写入文件
    ├─ 清除缓存
    ├─ 统计使用次数
    └─ 更新评价模板排序
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

### 课程和班级管理服务

#### CourseService
**功能**：课程创建和管理

**方法**：
- `create_course(teacher, name, course_type, description)` - 创建课程
- `list_courses(teacher)` - 列出教师的所有课程
- `update_course_type(course_id, course_type)` - 更新课程类型

#### ClassService
**功能**：班级创建和管理

**方法**：
- `create_class(course, name, student_count)` - 创建班级
- `list_classes(course)` - 列出课程下的所有班级
- `get_class_students(class_id)` - 获取班级学生列表

### 仓库管理服务

#### RepositoryService
**功能**：仓库配置和管理

**方法**：
- `create_git_repository(teacher, class_obj, name, git_url, branch, auth)` - 创建Git仓库配置
- `create_filesystem_repository(teacher, class_obj, name)` - 创建文件系统仓库
- `generate_directory_name(username)` - 生成目录名，处理重名
- `validate_git_connection(git_url, branch, auth)` - 验证Git连接
- `validate_directory_structure(repo_path)` - 验证目录结构
- `list_repositories(teacher)` - 列出教师的所有仓库

#### FileUploadService
**功能**：学生作业上传（仅文件系统方式）

**方法**：
- `upload_submission(student, homework, file)` - 上传作业文件
- `validate_file(file)` - 验证文件格式和大小
- `save_file(file, path)` - 保存文件到指定路径
- `create_submission_record(student, homework, file_info)` - 创建提交记录

### 评分服务

#### GradingService
**功能**：评分和评价管理

**方法**：
- `add_grade(file_path, grade, comment, grade_type)` - 添加评分
- `validate_lab_report_comment(is_lab_report, comment)` - 验证实验报告评价
- `remove_grade(file_path)` - 撤销评分
- `get_current_grade(file_path)` - 获取当前评分

**评分类型支持**：
- 字母等级：A/B/C/D/E
- 文字等级：优秀/良好/中等/及格/不及格
- 百分制：0-100分

### 评价模板服务

#### CommentTemplateService
**功能**：评价模板管理和推荐

**方法**：
- `get_personal_templates(teacher, limit=5)` - 获取个人常用评价
- `get_system_templates(tenant, limit=5)` - 获取系统常用评价
- `get_recommended_templates(teacher)` - 获取推荐模板（个人优先）
- `record_comment_usage(teacher, comment_text)` - 记录评价使用
- `update_template_ranking()` - 更新模板排序

**推荐逻辑**：
```python
def get_recommended_templates(teacher):
    personal = get_personal_templates(teacher, limit=5)
    if len(personal) >= 5:
        return personal
    
    system = get_system_templates(teacher.tenant, limit=5-len(personal))
    return personal + system
```

### 评价缓存服务（前端）

#### CommentCacheService (JavaScript)
**功能**：浏览器本地存储评价缓存

**方法**：
- `autosave(file_path, comment_text)` - 每2秒自动保存
- `load(file_path)` - 加载缓存
- `clear(file_path)` - 清除缓存
- `cleanup_expired()` - 清理7天前的缓存

**存储格式**：
```javascript
{
  "cache_key": "comment_cache_{file_path_hash}",
  "data": {
    "comment": "评价内容",
    "timestamp": 1234567890,
    "file_path": "/path/to/file"
  }
}
```

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

### Course模型（课程）
```python
class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('theory', '理论课'),
        ('lab', '实验课'),
        ('practice', '实践课'),
        ('mixed', '理论+实验'),
    ]
    
    tenant = ForeignKey(Tenant)  # 多租户
    teacher = ForeignKey(User)   # 创建教师
    name = CharField(max_length=200)
    course_type = CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='theory'
    )
    description = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Class模型（班级）
```python
class Class(models.Model):
    tenant = ForeignKey(Tenant)
    course = ForeignKey(Course)
    name = CharField(max_length=200)  # 班级名称
    student_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Repository模型（仓库配置）
```python
class Repository(models.Model):
    REPO_TYPE_CHOICES = [
        ('git', 'Git仓库'),
        ('filesystem', '文件系统'),
    ]
    
    tenant = ForeignKey(Tenant)
    teacher = ForeignKey(User)
    class_obj = ForeignKey(Class)  # 关联班级
    name = CharField(max_length=200)
    repo_type = CharField(max_length=20, choices=REPO_TYPE_CHOICES)
    
    # Git仓库方式字段
    git_url = URLField(blank=True, null=True)
    git_branch = CharField(max_length=100, blank=True)
    git_username = CharField(max_length=100, blank=True)
    git_password = CharField(max_length=200, blank=True)  # 加密存储
    
    # 文件系统方式字段
    filesystem_path = CharField(max_length=500, blank=True)
    allocated_space_mb = IntegerField(default=1024)  # 分配空间
    
    description = TextField(blank=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Homework模型（作业批次）
```python
class Homework(models.Model):
    HOMEWORK_TYPE_CHOICES = [
        ('normal', '普通作业'),
        ('lab_report', '实验报告'),
    ]
    
    tenant = ForeignKey(Tenant)
    course = ForeignKey(Course)
    class_obj = ForeignKey(Class)
    folder_name = CharField(max_length=200)
    homework_type = CharField(
        max_length=20,
        choices=HOMEWORK_TYPE_CHOICES,
        default='normal'
    )
    deadline = DateTimeField(blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Submission模型（学生作业提交）
```python
class Submission(models.Model):
    tenant = ForeignKey(Tenant)
    homework = ForeignKey(Homework)
    student = ForeignKey(User)  # 学生用户
    file_path = CharField(max_length=500)
    file_name = CharField(max_length=200)
    file_size = IntegerField()  # 字节
    submitted_at = DateTimeField(auto_now_add=True)
    version = IntegerField(default=1)  # 版本号
```

### GradeTypeConfig模型（评分类型配置）
```python
class GradeTypeConfig(models.Model):
    GRADE_TYPE_CHOICES = [
        ('letter', '字母等级'),
        ('text', '文字等级'),
        ('percentage', '百分制'),
    ]
    
    tenant = ForeignKey(Tenant)
    class_obj = ForeignKey(Class)
    grade_type = CharField(max_length=20, choices=GRADE_TYPE_CHOICES)
    is_locked = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### CommentTemplate模型（评价模板）
```python
class CommentTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ('personal', '个人模板'),
        ('system', '系统模板'),
    ]
    
    tenant = ForeignKey(Tenant)
    teacher = ForeignKey(User, blank=True, null=True)  # 个人模板有teacher
    template_type = CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    comment_text = TextField()
    usage_count = IntegerField(default=0)
    last_used_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['teacher', 'template_type', '-usage_count']),
            Index(fields=['tenant', 'template_type', '-usage_count']),
        ]
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

### 实验报告评价验证

**触发条件**：
- 文件判定为实验报告
- 教师尝试保存评分但未输入评价

**处理流程**：
1. 阻止评分保存
2. 显示错误提示："实验报告必须添加评价"
3. 禁用保存按钮
4. 高亮评价输入框

### 仓库配置错误

**Git仓库连接失败**：
- 验证URL格式
- 测试网络连接
- 验证认证信息
- 显示详细错误信息

**文件系统空间不足**：
- 检查分配空间
- 计算已使用空间
- 显示空间使用情况
- 阻止上传操作

### 文件上传错误

**文件格式不支持**：
- 验证文件扩展名
- 显示支持的格式列表
- 拒绝上传

**文件大小超限**：
- 检查文件大小（最大50MB）
- 显示当前大小和限制
- 拒绝上传

### 百分制评分验证

**分数超出范围**：
- 验证输入值在0-100之间
- 显示错误提示
- 阻止保存

**非数字输入**：
- 验证输入为数字
- 显示错误提示
- 清空输入框

### 日志记录

```python
logger.info("✓ 成功操作")
logger.warning("! 警告信息")
logger.error("✗ 错误信息")
logger.debug("调试信息")
```

**关键操作日志**：
- 课程/班级创建
- 仓库配置
- 评分操作
- 评价保存
- 文件上传
- AI评分请求

## 测试策略

### 单元测试

**核心函数测试**：
1. `find_teacher_signature_cell` - 定位功能
2. `extract_grade_and_comment_from_cell` - 提取功能
3. `write_to_teacher_signature_cell` - 写入功能
4. `is_lab_report_file` - 类型判断

**服务层测试**：
1. `CourseService.create_course` - 课程创建
2. `RepositoryService.generate_directory_name` - 目录名生成和重名处理
3. `RepositoryService.validate_git_connection` - Git连接验证
4. `GradingService.validate_lab_report_comment` - 实验报告评价验证
5. `CommentTemplateService.get_recommended_templates` - 评价模板推荐
6. `FileUploadService.validate_file` - 文件验证

**模型测试**：
1. `Repository` - 仓库配置保存和查询
2. `CommentTemplate` - 评价模板统计和排序
3. `Submission` - 作业提交记录
4. `GradeTypeConfig` - 评分类型配置

### 集成测试

**评分流程**：
1. 手动评分流程（字母/文字/百分制）
2. AI评分流程
3. 实验报告强制评价验证
4. 获取评价功能
5. 撤销评分功能
6. 格式错误处理

**仓库管理流程**：
1. Git仓库配置和验证
2. 文件系统仓库创建和空间分配
3. 目录结构验证
4. 学生作业上传

**评价功能流程**：
1. 评价缓存自动保存
2. 评价缓存恢复
3. 评价模板推荐（个人优先）
4. 评价使用统计更新

### 边界测试

**文档格式**：
1. 没有"教师（签字）"单元格
2. 单元格内容为空
3. 只有签字文本没有评分
4. 有评分但没有评价
5. 文件已被锁定

**评分验证**：
1. 实验报告无评价时保存
2. 百分制输入负数
3. 百分制输入超过100
4. 百分制输入非数字

**仓库配置**：
1. Git URL格式错误
2. Git认证失败
3. 文件系统空间不足
4. 目录名冲突（重名处理）

**文件上传**：
1. 文件大小超过50MB
2. 不支持的文件格式
3. 文件系统空间不足
4. 重复上传（版本管理）

**评价模板**：
1. 个人模板不足5个
2. 系统模板为空
3. 评价内容完全相同
4. 缓存过期（7天）

## 性能优化

### 缓存机制

**服务器端缓存**：
- 目录文件数量缓存
- 课程和班级列表缓存
- 评价模板查询缓存（Redis）
- 避免重复计算

**客户端缓存**：
- 评价内容本地存储（LocalStorage）
- 评价模板列表缓存
- 目录树结构缓存

### 懒加载

**目录树**：
- 按需加载子目录
- 减少初始加载时间
- 虚拟滚动（大量文件时）

**评价模板**：
- 首次打开时加载
- 后续使用缓存

### 数据库优化

**索引策略**：
```python
# CommentTemplate模型
Index(fields=['teacher', 'template_type', '-usage_count'])
Index(fields=['tenant', 'template_type', '-usage_count'])

# Submission模型
Index(fields=['homework', 'student', '-submitted_at'])

# Repository模型
Index(fields=['teacher', 'is_active'])
```

**查询优化**：
- 使用`select_related`预加载外键
- 使用`prefetch_related`预加载多对多关系
- 避免N+1查询问题

### 批量操作优化

**批量评分**：
- 使用事务批量写入
- 显示实时进度
- 错误不中断整体流程

**批量AI评分**：
- 速率限制（每秒2个请求）
- 异步处理
- 队列管理

### 文件操作优化

**大文件处理**：
- 流式读取（避免内存溢出）
- 分块上传
- 进度显示

**Git操作优化**：
- 浅克隆（shallow clone）
- 只拉取需要的分支
- 缓存仓库信息

## 正确性属性

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 课程创建完整性
*For any* valid course data (name, type, description), creating a course should result in a database record containing all specified fields with correct values.
**Validates: Requirements 1.1**

### Property 2: 教师数据隔离
*For any* teacher, querying their course list should only return courses created by that teacher, never courses from other teachers.
**Validates: Requirements 1.4**

### Property 3: 目录名唯一性
*For any* username, calling the directory name generation function multiple times should always return unique directory names (using numeric suffixes when needed).
**Validates: Requirements 1.1.5**

### Property 4: 目录结构验证
*For any* directory path, the validation function should correctly identify whether it follows the "课程/班级/作业批次/学生作业" structure.
**Validates: Requirements 1.2.1**

### Property 5: 文件验证规则
*For any* file, the validation function should accept files within size limit (≤50MB) and supported formats, and reject all others.
**Validates: Requirements 1.4.3**

### Property 6: 文件路径生成规范
*For any* student and homework assignment, the generated file path should follow the format "课程/班级/作业批次/学号_姓名".
**Validates: Requirements 1.4.5**

### Property 7: 百分制分数范围验证
*For any* numeric input, the percentage grade validation should accept values in [0, 100] and reject all values outside this range.
**Validates: Requirements 4.4**

### Property 8: 实验报告强制评价
*For any* lab report file, attempting to save a grade without a comment should be rejected by the system.
**Validates: Requirements 4.5, 5.2**

### Property 9: 评价使用统计累加
*For any* comment text, saving it multiple times should correctly increment the usage count for that comment.
**Validates: Requirements 5.2.1**

### Property 10: 评价模板排序和限制
*For any* teacher, the personal comment template list should be sorted by usage count (descending) and contain at most 5 items.
**Validates: Requirements 5.2.4**

### Property 11: 评价内容去重
*For any* comment text, saving the exact same text multiple times should be recognized as the same comment with cumulative usage count, not create duplicate templates.
**Validates: Requirements 5.2.11**

### Property 12: 实验报告格式检测
*For any* Word document, the format validation function should correctly identify whether it contains the "教师（签字）" cell.
**Validates: Requirements 11.2**

### Property 13: 文件锁定机制
*For any* file containing the "【格式错误-已锁定】" marker, all subsequent grading operations should be rejected.
**Validates: Requirements 11.6**

### Property 14: 缓存避免重复计算
*For any* directory, calling the file count function twice should use cached results on the second call (verifiable through call count or performance).
**Validates: Requirements 14.1**

## 相关文档

- [需求文档](./requirements.md)
- [快速参考](../../docs/SUMMARY.md)
