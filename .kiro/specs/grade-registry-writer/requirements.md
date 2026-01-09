# 作业成绩写入成绩登分册需求文档

## 简介

作业成绩写入功能允许教师将作业成绩文件自动写入到成绩登分册Excel文件中。系统支持两种使用场景：

1. **作业评分系统场景**：在作业评分系统中，教师对某次作业进行批量登分。系统遍历该次作业目录下的所有已评分文档，根据文件名提取学生姓名，在班级目录的成绩登分册中找到对应学生，根据作业批次（从目录名提取）写入到对应列。

2. **工具箱模块场景**：在工具箱模块中，教师选择仓库中某个课程的某个班级目录。该目录包含成绩登分册和多个作业成绩文件。系统根据每个成绩文件的文件名判断作业批次，提取学生姓名和成绩，写入到登分册的对应位置。

## 术语表

- **System**: 作业成绩写入系统（Grade Registry Writer System）
- **Teacher**: 使用系统写入成绩的教师用户
- **Class Directory**: 班级目录，包含作业成绩文件和成绩登分册文件的目录
- **Homework Directory**: 作业目录，包含某次作业的所有学生提交文件的目录
- **Grade File**: 作业成绩文件，包含学生作业评分的Word文档
- **Grade Registry**: 成绩登分册，记录所有学生各次作业成绩的Excel文件
- **Homework Number**: 作业次数，标识第几次作业（如第1次、第2次）
- **Repository**: 用户仓库，存储班级目录的Git仓库或本地目录
- **Student Name**: 学生姓名，用于匹配成绩文件和登分册中的学生记录
- **Grade Column**: 成绩列，登分册中对应某次作业的列
- **Grading System**: 作业评分系统，用于批改和管理作业的系统模块
- **Toolbox Module**: 工具箱模块，提供各种辅助工具的系统模块

## 需求

### 需求 1: 使用场景识别

**用户故事**: 作为System，我需要识别当前的使用场景，以便采用正确的处理逻辑

#### 验收标准

1. WHEN Teacher从Grading System调用成绩写入功能时，THE System SHALL识别为作业评分系统场景
2. WHEN Teacher从Toolbox Module调用成绩写入功能时，THE System SHALL识别为工具箱模块场景
3. WHERE 场景为作业评分系统，THE System SHALL接收作业目录路径和班级目录路径作为参数
4. WHERE 场景为工具箱模块，THE System SHALL接收班级目录路径作为参数
5. WHEN 场景识别完成时，THE System SHALL根据场景选择相应的处理流程

### 需求 2: 作业评分系统场景处理

**用户故事**: 作为Teacher，我希望在作业评分系统中对某次作业进行批量登分，以便快速完成成绩录入

#### 验收标准

1. WHEN Teacher在Grading System中选择某次作业进行登分时，THE System SHALL获取该作业目录路径
2. WHEN System处理作业目录时，THE System SHALL从目录名中提取作业批次（如"第1次作业"提取为1）
3. WHEN System扫描作业目录时，THE System SHALL遍历所有已评分的Word文档
4. WHEN System处理每个文档时，THE System SHALL从文件名提取学生姓名
5. WHEN System提取成绩后，THE System SHALL在班级目录的成绩登分册中查找对应学生
6. WHEN System写入成绩时，THE System SHALL根据作业批次定位到登分册的对应列
7. WHERE 班级目录路径未提供，THE System SHALL根据作业所属课程自动定位班级目录

### 需求 3: 工具箱模块场景处理

**用户故事**: 作为Teacher，我希望在工具箱模块中选择班级目录进行成绩写入，以便处理多次作业的成绩

#### 验收标准

1. WHEN Teacher在Toolbox Module中访问成绩写入功能时，THE System SHALL显示用户仓库的目录树结构
2. WHEN Teacher选择班级目录时，THE System SHALL验证该目录包含成绩登分册文件
3. WHERE 目录不包含成绩登分册文件，THE System SHALL显示错误提示"未找到成绩登分册文件"
4. WHEN System扫描班级目录时，THE System SHALL识别所有作业成绩Excel文件
5. WHEN System处理每个成绩Excel文件时，THE System SHALL从文件名提取作业批次
6. WHEN System打开Excel文件时，THE System SHALL读取所有学生的姓名和成绩
7. WHEN System处理每个学生记录时，THE System SHALL在登分册中查找对应学生行
8. WHEN System写入成绩时，THE System SHALL根据作业批次定位到登分册的对应列
9. WHERE 无法从文件名提取作业批次，THE System SHALL记录警告并跳过该文件

### 需求 4: 班级目录和成绩登分册定位

**用户故事**: 作为System，我需要准确定位班级目录和成绩登分册文件，以便正确写入成绩

#### 验收标准

1. WHERE 场景为作业评分系统，THE System SHALL根据作业所属课程和班级信息定位班级目录
2. WHERE 场景为工具箱模块，THE System SHALL使用Teacher选择的目录作为班级目录
3. WHEN System定位班级目录后，THE System SHALL在该目录中查找成绩登分册文件
4. WHERE 文件名包含"成绩登分册"、"登分册"或"grade_registry"，THE System SHALL判定为成绩登分册文件
5. WHERE 找到多个匹配文件，THE System SHALL选择最近修改的文件
6. WHERE 未找到成绩登分册文件，THE System SHALL返回错误"未找到成绩登分册文件"

### 需求 5: 文件路径验证

**用户故事**: 作为系统，我需要确保作业成绩文件和成绩登分册文件都在用户仓库的同一班级目录中，以便保证数据安全性

#### 验收标准

1. WHEN System处理文件时，THE System SHALL验证所有文件路径都在用户仓库基础目录内
2. WHERE 文件路径包含路径遍历字符（如"../"），THE System SHALL拒绝处理并返回错误
3. WHERE 作业成绩文件不在班级目录内，THE System SHALL拒绝处理该文件
4. WHERE 成绩登分册文件不在班级目录内，THE System SHALL拒绝处理并返回错误
5. WHEN 验证失败时，THE System SHALL记录安全日志包含用户ID和尝试访问的路径

### 需求 6: 作业成绩文件识别

**用户故事**: 作为系统，我需要自动识别作业成绩文件，以便提取成绩数据

#### 验收标准

1. WHERE 场景为作业评分系统，THE System SHALL扫描作业目录下的所有Word文档文件（.docx格式）
2. WHERE 场景为作业评分系统，THE System SHALL验证Word文档是否包含评分标记
3. WHERE Word文档包含"老师评分："或"教师（签字）："标记，THE System SHALL判定为作业成绩文件
4. WHERE Word文档不包含评分标记，THE System SHALL跳过该文件
5. WHERE 场景为工具箱模块，THE System SHALL扫描班级目录下的所有Excel文件（.xlsx或.xls格式）
6. WHERE Excel文件名包含"成绩"或"grade"关键字且不是成绩登分册，THE System SHALL判定为作业成绩文件
7. WHERE Excel文件是成绩登分册，THE System SHALL跳过该文件

### 需求 7: 作业批次识别

**用户故事**: 作为系统，我需要识别每个作业成绩文件对应的作业批次，以便写入登分册的正确列

#### 验收标准

1. WHERE 场景为作业评分系统，THE System SHALL从作业目录名中提取作业批次
2. WHERE 作业目录名包含"第X次作业"或"作业X"模式，THE System SHALL提取数字X作为作业批次
3. WHERE 场景为工具箱模块，THE System SHALL从每个成绩文件的文件名中提取作业批次
4. WHERE 文件名包含"第X次作业"或"作业X"模式，THE System SHALL提取数字X作为作业批次
5. WHERE 文件名包含"homework_X"或"hw_X"模式，THE System SHALL提取数字X作为作业批次
6. WHERE 无法识别作业批次，THE System SHALL记录警告并跳过该文件

### 需求 8: 成绩登分册文件识别

**用户故事**: 作为系统，我需要在班级目录中找到成绩登分册文件，以便写入成绩数据

#### 验收标准

1. WHEN System扫描班级目录时，THE System SHALL查找Excel文件（.xlsx或.xls格式）
2. WHERE 文件名包含"成绩登分册"、"登分册"或"grade_registry"，THE System SHALL判定为成绩登分册文件
3. WHERE 找到多个匹配文件，THE System SHALL选择最近修改的文件
4. WHERE 未找到匹配文件，THE System SHALL返回错误"未找到成绩登分册文件"
5. WHEN 找到成绩登分册文件时，THE System SHALL验证文件格式是否正确

### 需求 9: 成绩登分册格式验证

**用户故事**: 作为系统，我需要验证成绩登分册的格式，以便确保能够正确写入成绩

#### 验收标准

1. WHEN System打开成绩登分册时，THE System SHALL验证文件包含"姓名"列
2. WHERE 文件不包含"姓名"列，THE System SHALL返回错误"成绩登分册格式错误：缺少姓名列"
3. WHEN System验证列结构时，THE System SHALL识别作业成绩列的命名模式
4. WHERE 列名包含"第X次作业"或"作业X"，THE System SHALL识别为作业成绩列
5. WHERE 缺少对应作业次数的列，THE System SHALL自动创建新列

### 需求 10: 学生姓名匹配

**用户故事**: 作为系统，我需要将作业成绩文件中的学生姓名与登分册中的学生记录匹配，以便写入正确的行

#### 验收标准

1. WHEN System处理作业成绩文件时，THE System SHALL从文件名中提取学生姓名
2. WHERE 文件名格式为"姓名_作业X.docx"，THE System SHALL提取下划线前的部分作为姓名
3. WHERE 文件名格式为"作业X_姓名.docx"，THE System SHALL提取下划线后的部分作为姓名
4. WHEN System提取姓名后，THE System SHALL在登分册的"姓名"列中查找匹配记录
5. WHERE 找到完全匹配的姓名，THE System SHALL使用该行写入成绩
6. WHERE 未找到完全匹配，THE System SHALL尝试模糊匹配（去除空格和特殊字符）
7. WHERE 模糊匹配找到唯一结果，THE System SHALL使用该行写入成绩
8. WHERE 找到多个匹配或未找到匹配，THE System SHALL记录错误并跳过该文件

### 需求 11: 成绩提取

**用户故事**: 作为系统，我需要从作业成绩文件中提取评分，以便写入登分册

#### 验收标准

1. WHEN System读取作业成绩文件时，THE System SHALL判断文件是否为实验报告
2. WHERE 文件为实验报告，THE System SHALL在"教师（签字）："单元格中查找评分
3. WHERE 文件为普通作业，THE System SHALL在文档末尾查找"老师评分："标记后的评分
4. WHERE 找到评分，THE System SHALL提取评分等级（A/B/C/D/E或优秀/良好/中等/及格/不及格）
5. WHERE 未找到评分，THE System SHALL记录警告并跳过该文件
6. WHERE 评分格式无效，THE System SHALL记录错误并跳过该文件

### 需求 12: 成绩写入

**用户故事**: 作为系统，我需要将提取的成绩写入登分册的对应位置，以便更新学生成绩记录

#### 验收标准

1. WHEN System确定学生行和作业列后，THE System SHALL定位到对应的单元格
2. WHERE 单元格为空，THE System SHALL直接写入成绩
3. WHERE 单元格已有成绩，THE System SHALL比较新旧成绩
4. WHERE 新旧成绩相同，THE System SHALL跳过写入
5. WHERE 新旧成绩不同，THE System SHALL覆盖旧成绩并记录日志
6. WHEN 写入成绩后，THE System SHALL保存Excel文件

### 需求 13: 批量处理

**用户故事**: 作为Teacher，我希望系统能够自动遍历班级目录中的所有作业成绩文件，以便一次性完成所有成绩的写入

#### 验收标准

1. WHEN Teacher启动成绩写入时，THE System SHALL扫描班级目录获取所有作业成绩文件列表
2. WHEN System处理文件列表时，THE System SHALL按文件名排序确保处理顺序一致
3. WHEN System处理每个文件时，THE System SHALL显示当前处理进度（如"处理中：5/20"）
4. WHERE 某个文件处理失败，THE System SHALL记录错误但继续处理下一个文件
5. WHEN 所有文件处理完成时，THE System SHALL显示处理结果摘要

### 需求 14: 处理结果报告

**用户故事**: 作为Teacher，我希望看到详细的处理结果报告，以便了解哪些成绩已写入、哪些失败

#### 验收标准

1. WHEN 批量处理完成时，THE System SHALL生成处理结果报告
2. WHERE 有成功写入的记录，THE System SHALL显示成功数量和学生姓名列表
3. WHERE 有失败的记录，THE System SHALL显示失败数量、文件名和失败原因
4. WHERE 有跳过的文件，THE System SHALL显示跳过数量和原因（如"已有相同成绩"）
5. WHEN Teacher查看报告时，THE System SHALL提供下载详细日志的选项

### 需求 15: 错误处理

**用户故事**: 作为系统，我需要妥善处理各种错误情况，以便保证数据完整性和用户体验

#### 验收标准

1. WHERE Excel文件被其他程序占用，THE System SHALL返回错误"成绩登分册文件被占用，请关闭后重试"
2. WHERE Word文档损坏无法读取，THE System SHALL记录错误并跳过该文件
3. WHERE 磁盘空间不足，THE System SHALL返回错误"磁盘空间不足，无法保存文件"
4. WHERE 文件权限不足，THE System SHALL返回错误"无权限访问文件"
5. WHEN 发生未预期错误时，THE System SHALL记录完整错误堆栈并显示友好错误信息

### 需求 16: 事务性保证

**用户故事**: 作为系统，我需要确保成绩写入的原子性，以便在出错时不会产生部分更新

#### 验收标准

1. WHEN System开始写入成绩时，THE System SHALL创建登分册文件的备份
2. WHERE 写入过程中发生错误，THE System SHALL从备份恢复原文件
3. WHERE 所有成绩写入成功，THE System SHALL删除备份文件
4. WHEN System保存Excel文件时，THE System SHALL验证文件完整性
5. WHERE 文件完整性验证失败，THE System SHALL从备份恢复并返回错误

### 需求 17: 日志记录

**用户故事**: 作为系统管理员，我希望系统记录详细的操作日志，以便审计和问题排查

#### 验收标准

1. WHEN Teacher启动成绩写入时，THE System SHALL记录操作日志包含用户ID、班级目录和时间戳
2. WHEN System处理每个文件时，THE System SHALL记录文件路径、学生姓名、作业次数和成绩
3. WHERE 发生错误时，THE System SHALL记录错误类型、错误消息和堆栈信息
4. WHEN 成绩被覆盖时，THE System SHALL记录旧成绩和新成绩
5. WHEN 处理完成时，THE System SHALL记录总处理数量、成功数量和失败数量

### 需求 18: 权限控制

**用户故事**: 作为系统，我需要验证用户权限，以便确保只有授权用户能够写入成绩

#### 验收标准

1. WHEN 用户访问成绩写入功能时，THE System SHALL验证用户已登录
2. WHERE 用户未登录，THE System SHALL重定向到登录页面
3. WHEN 用户选择班级目录时，THE System SHALL验证该目录属于用户的仓库
4. WHERE 目录不属于用户仓库，THE System SHALL返回403禁止访问错误
5. WHEN 用户执行写入操作时，THE System SHALL验证用户具有教师角色

### 需求 19: 性能优化

**用户故事**: 作为Teacher，我希望系统能够快速处理大量文件，以便提高工作效率

#### 验收标准

1. WHEN System处理少于50个文件时，THE System SHALL在30秒内完成处理
2. WHEN System处理50-200个文件时，THE System SHALL在2分钟内完成处理
3. WHERE 文件数量超过200个，THE System SHALL显示警告并建议分批处理
4. WHEN System读取Excel文件时，THE System SHALL使用只读模式提高性能
5. WHEN System写入Excel文件时，THE System SHALL批量写入所有更改后一次性保存

### 需求 20: 用户界面

**用户故事**: 作为Teacher，我希望有清晰的用户界面，以便轻松使用成绩写入功能

#### 验收标准

1. WHEN Teacher访问成绩写入页面时，THE System SHALL显示目录选择器和操作按钮
2. WHEN Teacher选择班级目录后，THE System SHALL显示预览信息包含文件数量和登分册名称
3. WHEN Teacher点击"开始写入"按钮时，THE System SHALL显示确认对话框
4. WHEN 处理进行中时，THE System SHALL显示进度条和当前处理的文件名
5. WHEN 处理完成时，THE System SHALL显示结果摘要和详细报告链接

### 需求 21: 多租户支持

**用户故事**: 作为系统，我需要支持多租户架构，以便不同机构独立使用功能

#### 验收标准

1. WHEN 用户执行成绩写入时，THE System SHALL自动关联到用户所属租户
2. WHEN System访问文件时，THE System SHALL只访问当前租户的仓库目录
3. WHERE 用户尝试访问其他租户的文件，THE System SHALL拒绝访问并返回错误
4. WHEN System记录日志时，THE System SHALL包含租户ID信息
5. WHERE 用户为租户管理员，THE System SHALL允许查看租户内所有用户的操作日志
