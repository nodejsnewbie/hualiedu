# 作业评分系统需求文档

## 简介

作业评分系统是一个基于Django的Web应用，用于教师对学生提交的作业进行评分和评价。系统支持两种作业存储方式：Git仓库方式和文件系统方式。Git仓库方式允许教师配置远程仓库地址直接访问作业；文件系统方式为教师分配存储空间，学生可以上传作业文件。系统支持多种文件格式（Word文档、文本文件等），提供手动评分和AI辅助评分功能，支持多租户架构，并能够管理多个仓库、课程、班级和作业批次。

## 术语表

- **System**: 作业评分系统（Homework Grading System）
- **Teacher**: 使用系统进行评分的教师用户
- **Student**: 提交作业的学生用户，在文件系统方式下可以通过系统上传作业
- **Repository**: 作业存储仓库，支持Git仓库方式（配置远程仓库地址）和文件系统方式（系统分配的存储空间）
- **Git Repository Mode**: Git仓库方式，教师配置Git仓库地址和相关参数，系统直接访问仓库内容
- **Filesystem Mode**: 文件系统方式，系统为教师分配存储空间，学生可上传作业文件
- **Course**: 课程，教师创建的课程实体，包含理论课、实验课、实践课和混合课四种类型
- **Class**: 班级，教师所教授的班级，一个课程可以有多个班级
- **Homework**: 作业批次，对应文件系统中的一个目录，表示第几次作业
- **Directory Structure**: 目录结构，统一格式为"课程/班级/作业批次/学生作业文件"
- **Submission**: 学生提交的单个作业文件
- **Grade**: 评分，支持三种评分方式：字母等级（A/B/C/D/E）、文字等级（优秀/良好/中等/及格/不及格）和百分制（0-100分）
- **Comment**: 教师对作业的文字评价
- **Comment Template**: 评价模板，系统记录的常用评价内容，包括个人评价模板和系统评价模板
- **Personal Comment Template**: 个人评价模板，单个教师使用最多的5个评价
- **System Comment Template**: 系统评价模板，全局所有教师使用最多的5个评价
- **Tenant**: 租户，支持多租户隔离
- **Lab Report**: 实验报告，一种特殊的作业类型
- **Batch Grading**: 批量评分，对多个文件同时进行评分操作
- **AI Scoring**: AI评分，使用人工智能模型自动生成评分和评价

## 需求

### 需求 1: 课程和班级创建

**用户故事**: 作为Teacher，我希望能够创建课程和班级，以便组织和管理我的教学工作

#### 验收标准

1. WHEN Teacher创建新课程时，THE System SHALL允许指定课程名称、课程类型（理论课/实验课/实践课/混合课）和描述
2. WHEN Teacher创建班级时，THE System SHALL要求关联到已创建的课程
3. WHEN Teacher创建班级时，THE System SHALL允许指定班级名称和学生人数
4. WHEN Teacher访问课程列表时，THE System SHALL显示该Teacher创建的所有课程
5. WHEN Teacher选择课程时，THE System SHALL显示该课程下的所有班级列表

### 需求 1.1: 仓库方式选择和配置

**用户故事**: 作为Teacher，我希望为每个班级选择作业存储方式，以便灵活管理不同班级的作业

#### 验收标准

1. WHEN Teacher为班级配置仓库时，THE System SHALL提供Git仓库方式和文件系统方式两个选项
2. WHEN Teacher配置仓库时，THE System SHALL允许同时选择Git仓库方式和文件系统方式
3. WHERE Teacher选择Git仓库方式，THE System SHALL要求提供Git仓库URL、分支名称和认证信息
4. WHERE Teacher选择文件系统方式，THE System SHALL自动为该Teacher分配存储空间
5. WHERE 选择文件系统方式，THE System SHALL基于Teacher用户名生成目录名
6. WHERE 基于用户名的目录已存在，THE System SHALL在目录名后添加数字后缀（如username_2）
7. WHEN 仓库配置完成时，THE System SHALL验证配置有效性并保存
8. WHERE Git仓库配置无效（无法连接或认证失败），THE System SHALL显示错误信息并要求重新配置
9. WHERE Teacher同时配置两种方式，THE System SHALL允许Teacher选择主要使用的方式

### 需求 1.2: 仓库目录结构管理

**用户故事**: 作为Teacher，我希望系统强制统一的目录结构，以便规范作业组织方式

#### 验收标准

1. WHEN System访问仓库时，THE System SHALL验证目录结构符合"课程/班级/作业批次/学生作业"格式
2. WHERE 仓库为文件系统方式，THE System SHALL自动创建课程和班级目录
3. WHEN Teacher创建作业批次时，THE System SHALL在对应班级目录下创建作业批次目录
4. WHERE 目录结构不符合规范，THE System SHALL显示警告信息并提供修复建议
5. WHEN Teacher浏览仓库时，THE System SHALL以树形结构展示完整的目录层级

### 需求 1.3: 多仓库管理

**用户故事**: 作为Teacher，我希望能够管理多个仓库，以便为不同课程或班级使用不同的存储方式

#### 验收标准

1. WHEN Teacher访问仓库管理页面时，THE System SHALL显示该Teacher配置的所有仓库列表
2. WHEN 显示仓库列表时，THE System SHALL标识每个仓库的类型（Git或文件系统）
3. WHEN Teacher选择仓库时，THE System SHALL加载该仓库下的课程和班级目录结构
4. WHEN Teacher删除仓库配置时，THE System SHALL警告数据不会被删除，仅移除配置
5. WHERE 仓库为文件系统方式，THE System SHALL显示已使用空间和剩余空间信息


### 需求 1.4: 学生作业上传

**用户故事**: 作为Student，我希望能够上传作业文件，以便提交给教师评分

#### 验收标准

1. WHERE 仓库为文件系统方式，THE System SHALL为Student提供作业上传功能
2. WHEN Student访问上传页面时，THE System SHALL显示该Student所属班级的作业批次列表
3. WHEN Student选择作业批次并上传文件时，THE System SHALL验证文件格式和大小
4. WHERE 文件格式不支持或大小超过限制，THE System SHALL拒绝上传并显示错误信息
5. WHEN 文件上传成功时，THE System SHALL将文件保存到"课程/班级/作业批次/学号_姓名"路径
6. WHERE Student已上传作业，THE System SHALL允许覆盖上传并保留历史版本
7. WHERE 仓库为Git方式，THE System SHALL不提供上传功能（学生通过Git提交）

### 需求 2: 课程和作业管理

**用户故事**: 作为Teacher，我希望系统能够识别课程类型并管理作业批次，以便针对不同类型的课程采用合适的评分方式

#### 验收标准

1. WHEN Teacher选择课程目录时，THE System SHALL自动检测课程类型（理论课、实验课、实践课或混合课）
2. WHEN 课程不存在于数据库时，THE System SHALL根据课程名称关键词自动创建课程记录
3. WHEN Teacher修改课程类型时，THE System SHALL保存更新并在2秒内显示保存成功提示
4. WHEN Teacher浏览课程目录时，THE System SHALL显示该课程下的所有作业批次文件夹
5. WHERE 作业批次存在于数据库，THE System SHALL显示作业类型标识（普通作业或实验报告）

### 需求 2.1: 作业类型自动判断

**用户故事**: 作为开发者，我希望系统能够自动判断作业是否为实验报告，以便采用正确的评分写入格式

#### 验收标准

1. WHEN 系统需要判断作业类型时，THE System SHALL优先查询数据库中的Homework记录
2. WHERE 数据库中存在作业批次记录，THE System SHALL使用记录中的homework_type字段判断
3. WHERE 数据库中不存在作业批次记录，THE System SHALL查询Course表获取课程类型
4. WHERE 课程类型为lab/practice/mixed，THE System SHALL默认判定为实验报告
5. WHERE 课程类型为theory，THE System SHALL默认判定为普通作业
6. WHERE 课程不存在于数据库，THE System SHALL从文件路径中提取课程名和作业文件夹名
7. WHERE 成功提取路径信息，THE System SHALL递归调用作业批次查询
8. WHERE 路径提取失败，THE System SHALL根据课程名称关键词判断（包含"实验"、"lab"等关键词为实验报告）
9. WHERE 所有方法都失败，THE System SHALL默认判定为普通作业

### 需求 2.2: 作业批次类型配置

**用户故事**: 作为Teacher，我希望能够为每个作业批次单独设置类型，以便在同一课程下有不同类型的作业

#### 验收标准

1. WHEN Teacher创建作业批次时，THE System SHALL允许选择作业类型（普通作业或实验报告）
2. WHERE 课程类型为实验课，THE System SHALL默认选择实验报告类型
3. WHERE 课程类型为理论课，THE System SHALL默认选择普通作业类型
4. WHEN Teacher修改作业批次类型时，THE System SHALL保存更新
5. WHERE 作业批次已有评分记录，THE System SHALL警告类型修改可能影响已有评分格式

### 需求 2.3: 作业类型标签显示

**用户故事**: 作为Teacher，我希望在目录树中看到每个作业文件夹的类型标签，以便快速识别作业类型

#### 验收标准

1. WHEN 目录树加载完成时，THE System SHALL为每个作业文件夹添加类型标签
2. WHERE 作业类型为实验报告，THE System SHALL显示蓝色"实验报告"标签
3. WHERE 作业类型为普通作业，THE System SHALL显示灰色"普通作业"标签
4. WHEN Teacher点击类型标签时，THE System SHALL打开类型修改对话框
5. WHEN Teacher在对话框中选择新类型时，THE System SHALL自动保存更改
6. WHEN 类型保存成功时，THE System SHALL在1秒内显示"已保存"提示
7. WHEN 类型保存成功后，THE System SHALL自动更新标签显示
8. WHERE homework-type-labels.js未加载，THE System SHALL在控制台记录警告信息

### 需求 3: 文件浏览和内容显示

**用户故事**: 作为Teacher，我希望能够浏览作业文件并查看内容，以便进行评分

#### 验收标准

1. WHEN Teacher选择课程后，THE System SHALL以树形结构显示该课程下的所有目录和文件
2. WHEN Teacher点击文件时，THE System SHALL在右侧面板显示文件内容
3. WHERE 文件为Word文档（.docx），THE System SHALL将文档内容转换为HTML格式显示
4. WHERE 文件为文本文件，THE System SHALL在预格式化区域显示文本内容
5. WHERE 文件为Excel文件，THE System SHALL将表格内容转换为HTML表格显示
6. WHEN 文件加载失败时，THE System SHALL显示错误提示信息

### 需求 4: 手动评分功能

**用户故事**: 作为Teacher，我希望能够为作业文件打分，以便记录学生的成绩

#### 验收标准

1. WHEN Teacher查看文件时，THE System SHALL提供三种评分方式：字母评分（A/B/C/D/E）、文字评分（优秀/良好/中等/及格/不及格）和百分制（0-100分）
2. WHEN Teacher切换评分方式时，THE System SHALL立即更新评分界面的显示状态
3. WHERE Teacher选择百分制，THE System SHALL提供数字输入框允许输入0-100的分数
4. WHERE Teacher输入的分数超出0-100范围，THE System SHALL显示错误提示并拒绝保存
5. WHERE 文件为实验报告且Teacher未输入评价，THE System SHALL阻止评分保存并提示必须添加评价
6. WHEN Teacher选择评分等级或输入分数后点击确定时，THE System SHALL验证实验报告是否有评价
7. WHERE 验证通过，THE System SHALL将评分写入文件并保存
8. WHERE 文件为Word文档且为实验报告，THE System SHALL查找包含"教师（签字）："的单元格
9. WHERE 找到"教师（签字）："单元格，THE System SHALL清除该单元格中"教师（签字）："之前的所有内容
10. WHERE 清除旧内容后，THE System SHALL在该单元格中按顺序写入评分（第一行）和评价（第二行）
11. WHERE 文件为Word文档且为普通作业，THE System SHALL在文档末尾添加"老师评分："标记和评分
12. WHERE 文件已有评分，THE System SHALL在加载时自动识别并显示现有评分
13. WHEN Teacher点击撤销按钮时，THE System SHALL从文件中移除评分标记

### 需求 5: 教师评价功能

**用户故事**: 作为Teacher，我希望能够为作业添加文字评价，以便给学生提供详细反馈

#### 验收标准

1. WHEN Teacher点击教师评价按钮时，THE System SHALL打开评价输入对话框
2. WHERE 文件为实验报告，THE System SHALL要求Teacher必须输入评价内容
3. WHERE 文件为实验报告且Teacher未输入评价，THE System SHALL禁用保存按钮并显示提示信息
4. WHEN Teacher输入评价内容后点击保存时，THE System SHALL将评价写入文件
5. WHERE 文件为实验报告Word文档，THE System SHALL查找包含"教师（签字）："的单元格
6. WHERE 找到"教师（签字）："单元格，THE System SHALL清除该单元格中"教师（签字）："之前的所有内容
7. WHERE 清除旧内容后，THE System SHALL在该单元格中按顺序写入评分（第一行）和评价（第二行）
8. WHERE 文件为普通作业Word文档，THE System SHALL在评分后添加评价内容
9. WHERE 文件已有评价，THE System SHALL在对话框中显示历史评价记录
10. WHEN 评价保存成功时，THE System SHALL显示成功提示并关闭对话框
11. WHEN Teacher输入评价时，THE System SHALL自动缓存评价内容
12. WHERE 评价对话框意外关闭，THE System SHALL在重新打开时恢复缓存的评价内容

### 需求 5.1: 评价缓存功能

**用户故事**: 作为Teacher，我希望系统能够缓存我输入的评价内容，以便在意外情况下不丢失评价

#### 验收标准

1. WHEN Teacher在评价输入框中输入内容时，THE System SHALL每隔2秒自动缓存评价内容到浏览器本地存储
2. WHERE 评价对话框被意外关闭或浏览器崩溃，THE System SHALL保留缓存的评价内容
3. WHEN Teacher重新打开同一文件的评价对话框时，THE System SHALL检查是否存在缓存的评价
4. WHERE 存在缓存的评价且与文件中已保存的评价不同，THE System SHALL提示Teacher是否恢复缓存内容
5. WHEN Teacher选择恢复缓存时，THE System SHALL将缓存内容填充到评价输入框
6. WHEN 评价成功保存到文件后，THE System SHALL清除该文件对应的评价缓存
7. WHERE 缓存数据超过7天，THE System SHALL自动清理过期缓存
8. WHEN Teacher切换到不同文件时，THE System SHALL为每个文件维护独立的评价缓存

### 需求 5.2: 评价模板功能

**用户故事**: 作为Teacher，我希望系统能够记录和推荐常用评价，以便快速输入重复的评价内容

#### 验收标准

1. WHEN Teacher成功保存评价时，THE System SHALL统计该Teacher使用该评价内容的次数
2. WHEN System统计评价使用次数时，THE System SHALL维护该Teacher个人使用最多的5个评价列表
3. WHEN Teacher打开评价对话框时，THE System SHALL在输入框上方显示个人常用评价模板
4. WHEN 显示个人常用评价时，THE System SHALL按使用次数降序排列前5个评价
5. WHEN Teacher点击个人评价模板时，THE System SHALL将该评价内容填充到输入框
6. WHEN System统计全局评价时，THE System SHALL维护全局使用最多的5个评价列表
7. WHEN 显示评价模板时，THE System SHALL先显示个人评价模板，再显示系统评价模板
8. WHERE 个人评价模板不足5个，THE System SHALL用系统评价模板补充显示
9. WHERE 个人评价模板已有5个，THE System SHALL不显示系统评价模板
10. WHEN Teacher使用评价模板时，THE System SHALL允许Teacher编辑后再保存
11. WHERE 评价内容完全相同，THE System SHALL视为同一评价并累加使用次数
12. WHEN 评价使用次数更新时，THE System SHALL实时更新个人和系统评价模板排序

### 需求 6: AI评分功能

**用户故事**: 作为Teacher，我希望使用AI辅助评分，以便提高评分效率

#### 验收标准

1. WHEN Teacher点击AI评分按钮时，THE System SHALL读取文件内容并发送到AI服务
2. WHEN AI服务返回评分结果时，THE System SHALL在对话框中显示建议评分和评价
3. WHERE 文件为实验报告，THE System SHALL确保AI返回结果包含评价内容
4. WHERE AI返回的实验报告结果缺少评价，THE System SHALL显示错误并要求重新生成
5. WHEN Teacher确认AI评分时，THE System SHALL判断文件是否为实验报告
6. WHERE 文件为实验报告，THE System SHALL查找包含"教师（签字）："的单元格
7. WHERE 找到"教师（签字）："单元格，THE System SHALL清除该单元格中"教师（签字）："之前的所有内容
8. WHERE 清除旧内容后，THE System SHALL在该单元格中按顺序写入AI评分（第一行）和AI评价（第二行）
9. WHERE 文件为普通作业，THE System SHALL在文档末尾添加评分和评价
10. WHERE 文件已有评分，THE System SHALL禁用AI评分按钮
11. WHEN AI评分请求失败时，THE System SHALL显示错误信息并允许重试
12. WHERE 系统检测到频繁请求，THE System SHALL实施速率限制（每秒最多2个请求）

### 需求 7: 批量评分功能

**用户故事**: 作为Teacher，我希望能够批量处理多个作业文件，以便快速完成评分工作

#### 验收标准

1. WHEN Teacher点击批量评分按钮时，THE System SHALL打开批量评分页面
2. WHEN Teacher选择目录后，THE System SHALL显示该目录下所有待评分文件列表
3. WHEN Teacher选择统一评分等级或分数时，THE System SHALL对所有选中文件应用相同评分
4. WHERE Teacher选择百分制批量评分，THE System SHALL允许输入统一分数值
5. WHEN 批量评分执行时，THE System SHALL显示进度条和当前处理文件信息
6. WHEN 批量评分完成时，THE System SHALL显示成功和失败文件的统计信息
7. WHERE 某个文件处理失败，THE System SHALL记录错误信息但继续处理其他文件

### 需求 8: 批量AI评分功能

**用户故事**: 作为Teacher，我希望能够批量使用AI评分，以便高效处理大量作业

#### 验收标准

1. WHEN Teacher点击批量AI评分按钮时，THE System SHALL打开批量AI评分页面
2. WHEN Teacher选择目录并启动批量AI评分时，THE System SHALL依次处理每个文件
3. WHEN 处理每个文件时，THE System SHALL遵守API速率限制（每秒最多2个请求）
4. WHEN AI评分完成时，THE System SHALL自动将评分和评价写入文件
5. WHEN 批量AI评分执行时，THE System SHALL实时显示处理进度和状态
6. WHERE 某个文件AI评分失败，THE System SHALL跳过该文件并继续处理下一个文件
7. WHEN 批量AI评分完成时，THE System SHALL显示处理结果摘要

### 需求 9: 文件导航功能

**用户故事**: 作为Teacher，我希望能够快速在文件之间切换，以便连续评分

#### 验收标准

1. WHEN Teacher查看文件时，THE System SHALL显示当前文件在目录中的位置（如"3/10"）
2. WHEN Teacher点击上一个按钮时，THE System SHALL加载同目录中的前一个文件
3. WHEN Teacher点击下一个按钮时，THE System SHALL加载同目录中的后一个文件
4. WHERE 当前文件是第一个文件，THE System SHALL禁用上一个按钮
5. WHERE 当前文件是最后一个文件，THE System SHALL禁用下一个按钮
6. WHEN 切换文件时，THE System SHALL保持当前选择的评分方式

### 需求 10: 评分类型配置

**用户故事**: 作为Teacher，我希望系统能够记住每个班级的评分类型偏好，以便保持评分一致性

#### 验收标准

1. WHEN Teacher首次为某个班级评分时，THE System SHALL记录使用的评分类型（字母/文字/百分制）
2. WHEN Teacher再次为同一班级评分时，THE System SHALL自动应用之前使用的评分类型
3. WHERE 评分类型已锁定，THE System SHALL不允许更改评分类型
4. WHEN Teacher尝试更改已锁定的评分类型时，THE System SHALL显示警告信息
5. WHERE 班级没有评分类型配置，THE System SHALL使用默认的字母评分方式
6. WHERE Teacher使用百分制评分，THE System SHALL在文件中记录具体分数值

### 需求 11: 实验报告格式验证

**用户故事**: 作为Teacher，我希望系统能够验证实验报告格式，以便确保学生使用正确的模板

#### 验收标准

1. WHEN System识别文件为实验报告时，THE System SHALL使用统一的定位函数查找"教师（签字）"单元格
2. WHERE 实验报告缺少"教师（签字）"单元格，THE System SHALL判定为格式错误
3. WHERE 判定为格式错误，THE System SHALL自动将评分改为D
4. WHERE 判定为格式错误，THE System SHALL自动将评价设置为"【格式错误-已锁定】请按要求的格式写实验报告，此评分不可修改"
5. WHERE 判定为格式错误，THE System SHALL按普通作业方式写入评分和评价（文档末尾段落）
6. WHERE 文件包含"【格式错误-已锁定】"标记，THE System SHALL拒绝任何后续的评分修改操作
7. WHERE 文件被锁定，THE System SHALL在界面上显示锁定警告信息
8. WHEN Teacher查看被锁定的文件时，THE System SHALL显示红色警告提示框
9. WHEN Teacher尝试修改被锁定文件的评分时，THE System SHALL禁用所有评分按钮

### 需求 12: 多租户支持

**用户故事**: 作为系统管理员，我希望系统支持多租户架构，以便不同机构独立使用系统

#### 验收标准

1. WHEN 用户登录时，THE System SHALL根据用户配置确定所属租户
2. WHEN 用户访问数据时，THE System SHALL只显示该用户租户下的数据
3. WHEN 创建新记录时，THE System SHALL自动关联到用户所属租户
4. WHERE 用户为租户管理员，THE System SHALL允许管理租户配置
5. WHERE 用户为超级管理员，THE System SHALL允许访问全局配置

### 需求 13: 权限控制

**用户故事**: 作为系统管理员，我希望控制用户访问权限，以便保护数据安全

#### 验收标准

1. WHEN 未认证用户访问评分页面时，THE System SHALL重定向到登录页面
2. WHEN 非教师用户尝试访问评分功能时，THE System SHALL返回403禁止访问错误
3. WHEN 用户访问文件时，THE System SHALL验证文件路径在允许的基础目录内
4. WHERE 文件路径包含路径遍历攻击（如"../"），THE System SHALL拒绝访问
5. WHEN 用户尝试修改文件时，THE System SHALL验证用户具有写入权限

### 需求 14: 缓存和性能优化

**用户故事**: 作为Teacher，我希望系统响应快速，以便提高工作效率

#### 验收标准

1. WHEN System统计目录文件数量时，THE System SHALL缓存结果以避免重复计算
2. WHEN 目录树加载时，THE System SHALL使用懒加载方式按需加载子目录
3. WHEN 文件内容显示时，THE System SHALL在2秒内完成加载和渲染
4. WHERE 缓存数据存在，THE System SHALL优先使用缓存数据
5. WHEN 用户刷新页面时，THE System SHALL清除相关缓存
6. WHEN 目录树首次加载时，THE System SHALL在3秒内显示根目录结构
7. WHERE 单个文件大小超过50MB，THE System SHALL显示警告信息并限制预览功能
8. WHERE 批量操作涉及超过500个文件，THE System SHALL显示警告并要求用户确认
9. WHEN 缓存命中时，THE System SHALL在500毫秒内返回结果

### 需求 15: 获取教师评价功能

**用户故事**: 作为Teacher，我希望能够查看文件中已有的评价，以便了解之前的评价内容

#### 验收标准

1. WHEN Teacher请求获取评价时，THE System SHALL判断文件是否为实验报告
2. WHERE 文件为实验报告，THE System SHALL使用统一定位函数查找"教师（签字）"单元格
3. WHERE 找到单元格，THE System SHALL使用统一提取函数获取评价内容（第二行）
4. WHERE 文件为普通作业，THE System SHALL在段落中查找以"教师评价："、"AI评价："或"评价："开头的内容
5. WHERE 找到评价，THE System SHALL返回评价内容
6. WHERE 未找到评价，THE System SHALL返回"暂无评价"
7. WHERE 评价内容超过1000个字符，THE System SHALL截断并显示"...查看更多"链接

### 需求 16: 撤销评分功能

**用户故事**: 作为Teacher，我希望能够撤销已打的分数，以便纠正错误

#### 验收标准

1. WHEN Teacher点击撤销按钮时，THE System SHALL判断文件是否为实验报告
2. WHERE 文件为实验报告，THE System SHALL使用统一定位函数查找"教师（签字）"单元格
3. WHERE 找到单元格，THE System SHALL使用统一提取函数获取签字文本
4. WHERE 获取签字文本后，THE System SHALL清空单元格所有内容
5. WHERE 清空后，THE System SHALL只写入签字文本（保留"教师（签字）："及之后的内容）
6. WHERE 文件为普通作业，THE System SHALL删除所有评分和评价段落
7. WHEN 撤销成功时，THE System SHALL显示成功提示信息

### 需求 17: 错误处理和日志

**用户故事**: 作为系统管理员，我希望系统能够妥善处理错误并记录日志，以便排查问题

#### 验收标准

1. WHEN 系统发生错误时，THE System SHALL向用户显示友好的错误提示信息
2. WHEN 文件操作失败时，THE System SHALL记录详细的错误日志
3. WHEN API请求失败时，THE System SHALL返回包含错误代码和消息的JSON响应
4. WHERE 错误可恢复，THE System SHALL提供重试选项
5. WHEN 关键操作执行时，THE System SHALL记录操作日志包含用户、时间和操作内容
6. WHERE 网络连接中断，THE System SHALL在5秒后自动重试最多3次
7. WHERE 文件损坏无法读取，THE System SHALL记录错误并跳过该文件
8. WHEN 并发编辑冲突发生时，THE System SHALL提示用户刷新页面重新加载最新内容
