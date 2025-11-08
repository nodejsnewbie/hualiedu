# 作业评分功能

## 功能概述

作业评分系统提供了完整的作业批改和评分管理功能，支持多种文件格式、多种评分类型、AI辅助评分以及批量登分等功能。

## 核心功能

### 1. 文件浏览与预览

#### 支持的文件格式
- **Word文档** (.docx)：使用 mammoth 或 python-docx 转换为HTML预览
- **文本文件** (.txt)：直接显示文本内容
- **PDF文件** (.pdf)：支持预览

#### 目录树结构
- 基于仓库的三级目录结构：仓库 → 课程 → 作业
- 支持文件数量统计和缓存
- 过滤隐藏文件和目录（以 `.` 开头）

### 2. 评分管理

#### 评分类型
系统支持三种评分类型，可按班级配置：

1. **字母等级** (letter)：A/B/C/D/E
2. **文本等级** (text)：优秀/良好/中等/及格/不及格
3. **数字等级** (numeric)：90-100/80-89/70-79/60-69/0-59

#### 评分类型管理
- 每个班级可独立配置评分类型
- 支持评分类型锁定，防止误修改
- 支持评分类型转换，自动转换班级内所有已评分文件

#### 实验报告识别

系统通过以下方式自动识别实验报告：

1. **课程类型判断**（优先级最高）：从数据库查询课程的 `course_type` 字段
   - `lab`：实验课 → 实验报告
   - `practice`：实践课 → 实验报告
   - `mixed`：理论+实验 → 实验报告
   - `theory`：理论课 → 普通作业

2. **课程名称关键词判断**（备用方法）：如果数据库查询失败，检查课程名称是否包含以下关键词
   - "实验"
   - "lab"
   - "experiment"
   - "实训"
   - "practice"

3. **手动指定**：前端可以通过 `is_lab_report` 参数明确指定（优先级最高）

4. **自动判断**：如果未指定 `is_lab_report`，系统会根据文件路径提取课程名称，然后按上述方法判断

#### 评分操作

**添加评分**：将评分写入文件

1. **实验报告**（课程名称包含实验相关关键词）：写入表格特定位置
   - 查找包含"教师（签字）："的单元格（可能是合并单元格）
   - 只清空"教师（签字）："之前的内容，保留"教师（签字）："及其后面的内容
   - 写入格式：
     - 第一行：评分等级（如"A"，居中、加粗、14号字）
     - 第二行：对应评分的一句话评价（左对齐、11号字）
     - 第三行：保留的"教师（签字）：时间： 年 月 日"文本（左对齐、10号字）
   - 如果没有提供评价，系统会根据评分自动生成相应的评价

2. **普通作业**：
   - Word文档：在文档末尾添加新段落，格式：`老师评分：[等级]`
   - 文本文件：在文件末尾追加新行，格式：`老师评分：[等级]`

**删除评分**：移除文件中的评分标记
- 删除所有以"老师评分："、"评定分数："开头的段落或行
- 删除所有包含评价关键词的段落或行

**查看评分**：读取文件中的评分信息
- 支持从段落中读取（普通作业）
- 支持从表格中读取（实验报告和旧格式）
  - "评定分数"格式：读取下一个单元格
  - "教师（签字）"格式：读取该单元格的第一行

### 3. 教师评语

#### 评语管理
- 支持为每个作业添加教师评语
- 评语与评分一起保存在文件中
- 格式：`老师评分：[等级]` 和 `教师评语：[评语内容]`

#### 评语操作
- **保存评语**：`save_teacher_comment`
- **获取评语**：`get_teacher_comment`
- 支持Word和文本文件格式

### 4. AI辅助评分

#### 单文件AI评分
- 自动读取文件内容
- 调用AI模型进行评分
- 自动将评分写入文件
- 防止重复评分（已有评分的文件会跳过）

#### 批量AI评分
支持三种批量评分模式：

1. **整个仓库**：对仓库下所有作业进行评分
2. **指定班级**：对某个班级的所有作业进行评分
3. **指定作业**：对某个作业目录下的所有文件进行评分

#### AI评分流程
```
1. 检查文件是否已有评分
2. 读取文件内容
3. 调用AI模型评分
4. 解析AI返回的评分和评语
5. 将评分写入文件
6. 返回评分结果
```

#### 限流机制
- 请求队列管理
- 每秒最多2个请求
- 请求历史记录追踪

### 5. 批量登分

#### 功能特性
- 自动扫描仓库中的所有已评分作业
- 提取学生姓名和评分信息
- 自动写入Excel成绩登记表
- 支持多班级仓库和单班级仓库

#### 成绩登记表格式
```
| 序号 | 学号 | 姓名 | 第1次作业 | 第2次作业 | ... |
|------|------|------|-----------|-----------|-----|
| 1    |      | 张三 | A         | B         | ... |
| 2    |      | 李四 | B         | A         | ... |
```

#### 处理逻辑
1. 查找仓库根目录下的成绩登记表（`平时成绩登记表-*.xlsx`）
2. 遍历所有 `.docx` 文件
3. 从文件名提取学生姓名
4. 从文件内容提取评分
5. 根据作业目录名确定作业次数
6. 将评分写入对应单元格

## 数据模型

### Repository（仓库）
```python
- owner: 仓库所有者
- name: 仓库名称
- path: 仓库路径
- url: Git仓库URL
- repo_type: 仓库类型（local/git）
- branch: 默认分支
```

### Submission（提交）
```python
- repository: 关联仓库
- file_path: 文件路径
- file_name: 文件名
- grade: 评分
- comment: 评语
- submitted_at: 提交时间
- graded_at: 评分时间
```

### Course（课程）
```python
- semester: 所属学期
- teacher: 授课教师
- name: 课程名称
- course_type: 课程类型（theory/lab/practice/mixed）
- description: 课程描述
- location: 上课地点
- class_name: 班级名称
```

### GradeTypeConfig（评分类型配置）
```python
- tenant: 所属租户
- class_identifier: 班级标识
- grade_type: 评分类型（letter/text/numeric）
- is_locked: 是否锁定
```

## API接口

### 文件操作

#### 获取课程列表
```
GET /grading/get_courses_list/
参数：repo_id
返回：课程列表（第一级目录）
```

#### 获取目录树
```
GET /grading/get_directory_tree/
参数：repo_id, course, path
返回：目录树结构（JSON）
```

#### 获取文件内容
```
POST /grading/get_file_content/
参数：path, repo_id, course
返回：文件内容（HTML或文本）+ 评分信息
```

### 评分操作

#### 保存评分
```
POST /grading/save_grade/
参数：path, grade, repo_id, course
返回：操作结果
```

#### 添加评分到文件
```
POST /grading/add_grade_to_file/
参数：
  - path: 文件路径
  - grade: 评分等级
  - course: 课程名称（可选，用于自动识别实验报告）
  - is_lab_report: 是否为实验报告（可选，默认根据course自动判断）
返回：操作结果
```

#### 删除评分
```
POST /grading/remove_grade/
参数：path
返回：操作结果
```

#### 获取文件评分信息
```
POST /grading/get_file_grade_info/
参数：path
返回：{has_grade, grade, comment}
```

### 教师评语

#### 保存教师评语
```
POST /grading/save_teacher_comment/
参数：
  - file_path: 文件路径
  - comment: 评语内容
  - course: 课程名称（可选，用于自动识别实验报告）
返回：操作结果
```

#### 获取教师评语
```
POST /grading/get_teacher_comment/
参数：file_path
返回：{success, comment}
```

### AI评分

#### 单文件AI评分
```
POST /grading/ai_score/
参数：path, repo_id
返回：{status, score, grade, comment}
```

#### 批量AI评分
```
POST /grading/batch_ai_score/
参数：path
返回：{status, message, results[]}
```

#### 高级批量AI评分
```
POST /grading/batch-ai-score/
参数：scoring_type, repository, class, homework
返回：{status, message, results[]}
```

### 批量登分

#### 批量登分
```
POST /grading/batch-grade/api/
参数：repository_path
返回：{status, message}
```

### 评分类型管理

#### 获取评分类型配置
```
GET /grading/get-grade-type-config/
参数：class_identifier
返回：{grade_type, is_locked}
```

#### 更改评分类型
```
POST /grading/change-grade-type/
参数：class_identifier, new_grade_type
返回：{success, message, converted_count}
```

## 使用流程

### 基本评分流程

1. **选择仓库**
   - 在评分页面选择要评分的仓库
   - 系统加载仓库的课程列表

2. **浏览作业**
   - 选择课程
   - 浏览作业目录
   - 点击文件查看内容

3. **评分**
   - 查看作业内容
   - 选择评分等级
   - 可选：添加教师评语
   - 点击"保存评分"

4. **批量登分**
   - 完成所有评分后
   - 进入批量登分页面
   - 选择仓库
   - 点击"开始登分"
   - 系统自动生成成绩表

### AI辅助评分流程

1. **单个文件AI评分**
   - 打开文件
   - 点击"AI评分"按钮
   - 系统自动评分并保存

2. **批量AI评分**
   - 选择评分范围（仓库/班级/作业）
   - 点击"批量AI评分"
   - 系统自动处理所有文件
   - 查看评分结果报告

## 权限控制

### 用户权限
- 需要登录（`@login_required`）
- 需要staff权限（`@require_staff_user`）
- 仓库所有者权限验证

### 文件操作权限
- 读取权限验证
- 写入权限验证
- 路径安全检查（防止目录遍历攻击）

## 安全特性

### 路径验证
```python
def validate_file_path(file_path, base_dir, request, repo_id, course):
    # 1. 检查路径是否在基础目录内
    # 2. 检查文件是否存在
    # 3. 检查文件读取权限
    # 4. 检查用户仓库权限
```

### 文件类型验证
- 仅支持特定文件扩展名
- MIME类型检查
- 文件大小限制

## 错误处理

### 常见错误
- 文件不存在
- 无权限访问
- 文件格式不支持
- 评分类型不匹配
- AI服务不可用

### 错误响应格式
```json
{
    "status": "error",
    "message": "错误描述"
}
```

## 日志记录

系统记录以下操作日志：
- 文件访问
- 评分操作
- AI评分请求
- 批量登分操作
- 错误和异常

## 性能优化

### 缓存机制
- 目录文件数量缓存
- 学生列表缓存（批量登分）

### 批量处理
- 批量AI评分使用队列
- 限流机制防止API过载

## 相关代码文件

### 核心视图
- `grading/views.py`：主要视图函数
  - `grading_page`：评分页面
  - `get_file_content`：获取文件内容
  - `save_grade`：保存评分
  - `write_grade_to_lab_report`：实验报告评分写入
  - `update_lab_report_comment`：更新实验报告评价
  - `is_lab_report_file`：综合判断是否为实验报告
  - `get_course_type_from_name`：根据课程名称获取课程类型
  - `is_lab_course_by_name`：根据课程名称判断是否为实验课程（备用）
  - `ai_score_view`：AI评分
  - `batch_grade_registration`：批量登分

### 工具模块
- `grading/grade_type_manager.py`：评分类型管理
- `grading/grade_registration.py`：批量登分逻辑
- `grading/utils.py`：文件处理工具

### 模型
- `grading/models.py`：数据模型定义
  - `Repository`：仓库模型
  - `Submission`：提交模型
  - `GradeTypeConfig`：评分类型配置

### 前端模板
- `templates/grading_simple.html`：评分页面模板
- `templates/batch_grade_page.html`：批量登分页面

## 数据库迁移

### 添加课程类型字段

在Course模型中添加了 `course_type` 字段，需要执行数据库迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

### 字段说明
- `course_type`：课程类型字段
  - `theory`：理论课（默认值）
  - `lab`：实验课
  - `practice`：实践课
  - `mixed`：理论+实验

### 数据迁移建议
对于已有的课程数据，建议：
1. 根据课程名称批量更新课程类型
2. 或者在管理后台逐个设置课程类型

## 配置说明

### 全局配置
```python
# 仓库基础目录
GlobalConfig.set_value('default_repo_base_dir', '~/jobs')

# AI评分限流
API_RATE_LIMIT = 2  # 每秒最多2个请求
```

### 评分类型配置
```python
# 为班级配置评分类型
config = GradeTypeConfig.objects.create(
    class_identifier='计算机1班',
    grade_type='letter',  # letter/text/numeric
    is_locked=False
)
```

## 扩展功能

### 自定义评分类型
可以通过修改 `GRADE_CONVERSION_MAPS` 添加新的评分类型和转换规则。

### 自定义AI评分模型
可以替换 `_perform_ai_scoring_for_file` 函数中的AI模型调用。

### 自定义成绩表格式
可以修改 `GradeRegistration` 类中的表格生成逻辑。

### 自定义评价模板
可以修改 `generate_random_comment` 函数中的评价模板，为不同评分等级添加更多评价选项。

## 故障排查

### 评分无法保存
1. 检查文件权限
2. 检查文件格式是否支持
3. 查看日志文件

### 实验报告评分写入失败
1. 检查文档中是否包含"教师（签字）"单元格
2. 检查表格格式是否正确
3. 确认"教师（签字）"文本在单元格中的位置
4. 查看详细日志了解具体错误
5. 注意：系统会自动保留"教师（签字）："及其后面的内容

### AI评分失败
1. 检查AI服务是否可用
2. 检查API限流设置
3. 查看错误日志

### 批量登分失败
1. 检查成绩登记表是否存在
2. 检查文件命名格式
3. 检查评分是否已写入文件

## 最佳实践

1. **评分前备份**：建议在批量评分前备份仓库
2. **统一评分类型**：同一班级使用统一的评分类型
3. **及时锁定**：评分开始后锁定评分类型
4. **定期登分**：完成一批作业后及时登分
5. **检查结果**：批量操作后检查结果报告
6. **实验报告格式**：确保实验报告模板包含"教师（签字）"单元格
7. **合并单元格处理**：系统自动处理合并单元格，无需特殊操作
