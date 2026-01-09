# Requirements Document

## Introduction

本文档描述作业管理功能的重构需求。当前系统中的"仓库管理"功能对教师用户来说过于技术化，包含了不必要的 Git 同步等操作。本次重构将简化教师用户的操作流程，将"仓库管理"重命名为"作业管理"，并优化作业提交方式的配置流程。

**系统定位：** 作业评分系统本质上是一个统一的客户端，它同时支持 Git 仓库和文件系统两种存储方式，为教师提供统一的界面来批量处理和评分学生作业，而无需关心底层的存储技术细节。

## Glossary

- **Assignment Management System (AMS)**: 作业管理系统，教师用来配置和管理学生作业提交方式的系统
- **Teacher User**: 教师用户，使用系统进行作业管理和评分的用户
- **Student User**: 学生用户，提交作业的用户
- **Submission Method**: 作业提交方式，包括 Git 仓库和文件系统两种方式
- **Git Repository**: Git 仓库方式，学生通过 Git 仓库提交作业
- **Filesystem**: 文件系统方式，学生通过文件上传提交作业
- **Course**: 课程，如"数据结构"
- **Class**: 班级，如"计算机1班"
- **Assignment Number**: 作业次数，如"第一次作业"、"第二次作业"
- **Repository Sync**: 仓库同步操作，从 Git 远程仓库拉取最新代码的操作
- **Assignment Directory**: 作业目录，存储学生作业文件的目录结构

## Requirements

### Requirement 1

**User Story:** 作为教师用户，我希望看到"作业管理"而不是"仓库管理"，这样我能更清楚地理解这个功能的用途。

#### Acceptance Criteria

1. WHEN 教师用户访问系统 THEN AMS SHALL 在导航菜单中显示"作业管理"而不是"仓库管理"
2. WHEN 教师用户进入作业管理页面 THEN AMS SHALL 显示页面标题为"作业管理"
3. WHEN 教师用户查看管理界面 THEN AMS SHALL 使用"作业"相关术语而不是"仓库"术语
4. WHEN 教师用户查看帮助文档 THEN AMS SHALL 提供面向教师的作业管理说明

### Requirement 2

**User Story:** 作为教师用户，我希望能够简单地配置学生作业提交方式，而不需要了解 Git 等技术细节。

#### Acceptance Criteria

1. WHEN 教师用户创建新作业配置 THEN AMS SHALL 提供两个清晰的选项："Git 仓库"和"文件上传"
2. WHEN 教师用户选择提交方式 THEN AMS SHALL 只显示该方式相关的配置字段
3. WHEN 教师用户选择"文件上传"方式 THEN AMS SHALL 要求输入课程名称、班级名称和作业次数
4. WHEN 教师用户选择"Git 仓库"方式 THEN AMS SHALL 要求输入 Git 仓库 URL 和分支名称
5. WHEN 教师用户保存配置 THEN AMS SHALL 验证所有必填字段已填写

### Requirement 3

**User Story:** 作为教师用户，我希望系统直接从远程仓库读取作业信息，而不需要同步到本地。

#### Acceptance Criteria

1. WHEN 教师用户查看作业列表 THEN AMS SHALL NOT 显示"同步"按钮或类似的 Git 操作按钮
2. WHEN 教师用户选择某个课程 THEN AMS SHALL 直接从远程 Git 仓库读取该课程的目录结构
3. WHEN AMS 读取远程仓库 THEN AMS SHALL 列出该课程下的所有作业目录和学生提交情况
4. WHEN 教师用户打开学生作业进行评分 THEN AMS SHALL 直接从远程仓库获取作业文件内容
5. WHEN 远程仓库访问失败 THEN AMS SHALL 向教师用户显示友好的错误消息而不是技术错误信息
6. WHEN AMS 访问远程仓库 THEN AMS SHALL NOT 将仓库内容克隆或同步到本地文件系统

### Requirement 4

**User Story:** 作为教师用户，当我选择文件上传方式时，我希望系统自动创建合理的目录结构来组织学生作业。

#### Acceptance Criteria

1. WHEN 教师用户配置文件上传方式作业 THEN AMS SHALL 根据课程名称和班级名称生成基础目录路径
2. WHEN 学生提交作业 THEN AMS SHALL 将作业文件存储在格式为 `<课程名称>/<班级名称>/<作业次数>/` 的目录结构中
3. WHEN 学生上传作业文件 THEN AMS SHALL 要求文件名包含学生姓名以便区分不同学生的作业
4. WHEN 学生提交作业且作业次数目录不存在 THEN AMS SHALL 允许学生创建新的作业次数目录
5. WHEN 教师用户访问作业目录 THEN AMS SHALL 显示清晰的目录层级结构和所有学生的作业文件
6. WHEN 目录不存在 THEN AMS SHALL 自动创建所需的目录结构
7. WHEN 目录路径包含特殊字符 THEN AMS SHALL 进行适当的转义或替换以确保文件系统兼容性
8. WHEN 多个学生上传同名文件 THEN AMS SHALL 通过文件名中的学生姓名区分不同学生的作业

### Requirement 5

**User Story:** 作为教师用户，我希望能够查看和管理我创建的所有作业配置。

#### Acceptance Criteria

1. WHEN 教师用户访问作业管理页面 THEN AMS SHALL 显示该教师创建的所有作业配置列表
2. WHEN 显示作业列表 THEN AMS SHALL 包含作业名称、提交方式、关联课程、班级和创建时间
3. WHEN 教师用户点击作业配置 THEN AMS SHALL 允许查看和编辑配置详情
4. WHEN 教师用户编辑作业配置 THEN AMS SHALL 保留已提交的学生作业数据
5. WHEN 教师用户删除作业配置 THEN AMS SHALL 提示确认并说明对已提交作业的影响

### Requirement 6

**User Story:** 作为教师用户，我希望系统界面简洁明了，只显示我需要的功能。

#### Acceptance Criteria

1. WHEN 教师用户查看作业管理界面 THEN AMS SHALL NOT 显示 Git 相关的技术操作按钮（如"克隆"、"拉取"、"推送"、"同步"）
2. WHEN 教师用户查看作业详情 THEN AMS SHALL 只显示作业名称、提交方式、关联信息和状态
3. WHEN 教师用户需要技术支持 THEN AMS SHALL 提供"帮助"链接而不是暴露技术细节
4. WHEN 作业配置为 Git 方式 THEN AMS SHALL 直接从远程仓库读取内容而不显示任何本地同步操作
5. WHEN 教师用户查看 Git 仓库作业 THEN AMS SHALL 显示远程仓库的实时状态而不是本地缓存

### Requirement 7

**User Story:** 作为教师用户，我希望能够为不同的课程和班级创建独立的作业配置。

#### Acceptance Criteria

1. WHEN 教师用户创建作业配置 THEN AMS SHALL 允许选择或创建课程
2. WHEN 教师用户选择课程后 THEN AMS SHALL 允许选择或创建班级
3. WHEN 教师用户为同一课程的不同班级创建作业 THEN AMS SHALL 为每个班级维护独立的作业目录
4. WHEN 教师用户查看作业列表 THEN AMS SHALL 支持按课程和班级筛选
5. WHEN 教师用户管理多个课程 THEN AMS SHALL 清晰地区分不同课程的作业

### Requirement 8

**User Story:** 作为教师用户，我希望系统能够验证我的配置输入，避免常见错误。

#### Acceptance Criteria

1. WHEN 教师用户输入课程名称 THEN AMS SHALL 验证名称不为空且不包含非法字符
2. WHEN 教师用户输入班级名称 THEN AMS SHALL 验证名称不为空且不包含非法字符
3. WHEN 教师用户输入作业次数 THEN AMS SHALL 验证格式正确（如"第一次作业"、"第1次作业"）
4. WHEN 教师用户输入 Git URL THEN AMS SHALL 验证 URL 格式正确且可访问
5. WHEN 教师用户保存配置前 THEN AMS SHALL 检查是否存在重复的作业配置
6. WHEN 验证失败 THEN AMS SHALL 显示清晰的错误消息和修正建议

### Requirement 9

**User Story:** 作为学生用户，我希望能够方便地提交作业，只需点击一个按钮就能创建新的作业目录。

#### Acceptance Criteria

1. WHEN 学生用户访问作业提交页面 THEN AMS SHALL 显示该学生所在班级的课程列表
2. WHEN 学生用户选择课程 THEN AMS SHALL 显示现有的作业次数目录列表和"创建新作业"按钮
3. WHEN 学生用户点击"创建新作业"按钮 THEN AMS SHALL 根据当前已有的作业次数自动生成下一个作业目录名称（如已有"第一次作业"则创建"第二次作业"）
4. WHEN 系统自动生成作业目录名称 THEN AMS SHALL 遵循统一的命名规范（如"第N次作业"）
5. WHEN 学生用户上传作业文件 THEN AMS SHALL 自动在文件名中添加或验证学生姓名
6. WHEN 学生用户上传文件 THEN AMS SHALL 支持常见文档格式（docx、pdf、zip 等）
7. WHEN 学生用户重复上传同一作业 THEN AMS SHALL 覆盖之前的文件
8. WHEN 学生用户创建新作业目录 THEN AMS SHALL 立即显示该目录并允许上传文件

### Requirement 10

**User Story:** 作为系统架构师，我希望系统采用远程仓库直接访问模式，避免本地存储占用和同步延迟问题。

#### Acceptance Criteria

1. WHEN AMS 需要访问 Git 仓库内容 THEN AMS SHALL 使用 Git API 或命令直接读取远程仓库
2. WHEN AMS 读取远程仓库目录 THEN AMS SHALL 使用 Git ls-tree 或等效 API 获取目录结构
3. WHEN AMS 读取远程仓库文件 THEN AMS SHALL 使用 Git show 或等效 API 获取文件内容
4. WHEN AMS 缓存远程仓库数据 THEN AMS SHALL 使用内存缓存而不是文件系统缓存
5. WHEN 缓存过期 THEN AMS SHALL 自动从远程仓库重新获取最新数据
6. WHEN 多个教师同时访问同一仓库 THEN AMS SHALL 共享缓存以提高性能
7. WHEN 远程仓库需要认证 THEN AMS SHALL 安全地存储和使用认证凭据
