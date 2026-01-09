# 作业成绩写入成绩登分册实施计划

- [x] 1. 更新工具类以支持两种场景
  - 更新GradeFileProcessor类支持两种场景的文件处理
  - 保持RegistryManager类和NameMatcher类不变
  - _需求: 2, 3, 6, 7, 10, 11_

- [x] 1.1 更新GradeFileProcessor类支持两种场景
  - 更新`grading/grade_registry_writer.py`文件
  - 重命名`extract_homework_number()`为`extract_homework_number_from_path()`用于作业评分系统场景
  - 新增`extract_homework_number_from_filename()`方法用于工具箱模块场景
  - 重命名`extract_grade()`为`extract_grade_from_word()`用于作业评分系统场景
  - 新增`extract_grades_from_excel()`方法从Excel文件提取所有学生成绩（工具箱模块场景）
  - 保持`extract_student_name()`和`is_lab_report()`方法不变
  - _需求: 2, 3, 6, 7, 11_

- [x] 1.2 实现RegistryManager类
  - 在`grading/grade_registry_writer.py`中实现RegistryManager类
  - 实现`load()`方法使用openpyxl加载Excel文件
  - 实现`validate_format()`方法验证登分册格式（检查"姓名"列）
  - 实现`find_student_row()`方法查找学生行
  - 实现`find_or_create_homework_column()`方法查找或创建作业列
  - 实现`write_grade()`方法写入成绩到指定单元格
  - 实现`save()`方法保存Excel文件
  - 实现`create_backup()`和`restore_from_backup()`方法
  - _需求: 5, 6, 9, 13_

- [x] 1.3 实现NameMatcher类
  - 在`grading/grade_registry_writer.py`中实现NameMatcher类
  - 实现`exact_match()`方法进行精确姓名匹配
  - 实现`fuzzy_match()`方法进行模糊匹配（去除空格和特殊字符）
  - 实现`normalize_name()`方法规范化姓名
  - 处理多个匹配和无匹配的情况
  - _需求: 7_

- [x] 2. 创建服务层支持两种场景
  - 实现GradeRegistryWriterService类协调整个写入流程
  - 实现场景识别和路由逻辑
  - 实现两种场景的不同处理流程
  - 实现错误处理和事务管理
  - _需求: 1, 2, 3, 5, 13, 15, 16_

- [x] 2.1 实现GradeRegistryWriterService基础结构
  - 在`grading/services/grade_registry_writer_service.py`创建服务类
  - 实现`__init__()`方法初始化用户、租户和场景信息
  - 定义场景常量：SCENARIO_GRADING_SYSTEM和SCENARIO_TOOLBOX
  - 添加日志记录器
  - _需求: 1, 17_

- [x] 2.2 实现作业评分系统场景处理
  - 实现`process_grading_system_scenario()`方法
  - 从作业目录名提取作业批次
  - 扫描作业目录下的Word文档
  - 对每个文件提取学生姓名和成绩
  - 在班级目录的登分册中写入成绩
  - _需求: 2, 6, 7, 10, 11, 12_

- [x] 2.3 实现工具箱模块场景处理
  - 实现`process_toolbox_scenario()`方法
  - 扫描班级目录下的Excel成绩文件
  - 对每个Excel文件从文件名提取作业批次
  - 从Excel表格中读取所有学生的姓名和成绩
  - 在登分册中写入所有学生的成绩
  - _需求: 3, 6, 7, 10, 11, 12_

- [x] 2.4 实现通用方法和错误处理
  - 实现`find_grade_registry()`方法查找成绩登分册文件
  - 实现错误处理和事务管理
  - 在写入前创建Excel备份
  - 捕获并记录所有异常
  - 单个文件失败时继续处理其他文件
  - 保存失败时从备份恢复
  - 生成详细的处理报告
  - _需求: 4, 8, 15, 16_

- [x] 3. 创建视图和URL路由支持两种场景
  - 实现工具箱模块场景的视图函数
  - 实现作业评分系统场景的视图函数
  - 添加URL路由配置
  - 实现权限验证和路径安全检查
  - _需求: 1, 2, 3, 5, 18_

- [x] 3.1 实现工具箱模块场景视图
  - 在`grading/views.py`中添加`grade_registry_writer_view()`函数
  - 添加`@login_required`装饰器
  - 添加`@require_http_methods(["POST"])`装饰器
  - 处理POST请求获取class_directory和repository_id参数
  - 验证用户对仓库的访问权限
  - 调用服务层处理工具箱场景
  - 返回JSON响应包含处理结果
  - _需求: 3, 5, 18_

- [x] 3.2 实现作业评分系统场景视图
  - 在`grading/views.py`中添加`batch_grade_to_registry()`函数
  - 添加`@login_required`装饰器
  - 添加`@require_http_methods(["POST"])`装饰器
  - 根据homework_id获取作业对象
  - 从作业对象获取作业目录和班级目录
  - 调用服务层处理作业评分系统场景
  - 返回JSON响应包含处理结果
  - _需求: 2, 5, 18_

- [x] 3.3 实现路径验证
  - 使用现有的`validate_file_path()`函数验证目录路径
  - 确保路径在用户仓库范围内
  - 检查路径遍历攻击（../ 等）
  - 验证目录存在且可访问
  - _需求: 5_

- [x] 3.4 添加URL路由
  - 在`grading/urls.py`中添加工具箱模块路由
  - 路径: `/grade-registry-writer/`，名称: `grade_registry_writer`
  - 在`grading/urls.py`中添加作业评分系统路由
  - 路径: `/homework/<int:homework_id>/batch-grade-to-registry/`，名称: `batch_grade_to_registry`
  - _需求: 1, 2, 3_

- [x] 4. 创建前端界面
  - 创建工具箱模块的目录选择界面
  - 在作业评分系统中添加"登分"按钮
  - 实现进度显示和结果报告展示
  - _需求: 20_

- [x] 4.1 创建工具箱模块HTML模板
  - 创建`grading/templates/grade_registry_writer.html`
  - 添加目录树选择器（复用现有的目录树组件）
  - 添加"开始写入"按钮
  - 添加进度条显示区域
  - 添加结果报告显示区域
  - _需求: 20_

- [x] 4.2 在作业评分系统中添加登分按钮
  - 在作业列表或详情页面添加"登分"按钮
  - 按钮点击时调用`batch_grade_to_registry` API
  - 显示处理进度和结果
  - _需求: 20_

- [x] 4.3 实现JavaScript交互
  - 创建`grading/static/grading/js/grade_registry_writer.js`
  - 实现工具箱模块的目录选择和提交逻辑
  - 实现作业评分系统的登分按钮点击事件
  - 发送AJAX请求到对应的后端API
  - 实现进度显示更新
  - 实现结果报告渲染
  - _需求: 20_

- [x] 4.4 添加样式
  - 在`grading/static/grading/css/custom.css`中添加样式
  - 美化进度条和结果报告显示
  - 添加成功/失败状态的颜色标识
  - _需求: 20_

- [x] 5. 添加日志和监控
  - 配置日志记录器
  - 记录关键操作日志
  - 记录错误和异常
  - 实现操作审计
  - _需求: 17_

- [x] 5.1 配置日志
  - 在服务类和工具类中添加logger
  - 记录场景类型和处理开始
  - 记录目录扫描和文件识别
  - 记录每个文件的处理状态
  - 记录成绩写入操作
  - 记录所有错误和异常堆栈
  - _需求: 17_

- [x] 5.2 实现操作审计
  - 记录用户ID、租户ID和时间戳
  - 记录场景类型（作业评分系统或工具箱模块）
  - 记录目录路径和作业批次
  - 记录处理的文件数量和学生数量
  - 记录成绩覆盖情况（旧值和新值）
  - _需求: 17_

- [-] 6. 编写文档和测试
  - 编写功能使用文档
  - 创建单元测试
  - 创建集成测试
  - 准备测试数据
  - _需求: 所有_

- [x] 6.1 编写单元测试
  - 创建`grading/tests/test_grade_registry_writer.py`
  - 测试GradeFileProcessor的所有方法（包括两种场景）
  - 测试RegistryManager的所有方法
  - 测试NameMatcher的所有方法
  - 测试各种边界情况和错误场景
  - _需求: 所有_

- [x] 6.2 编写集成测试
  - 测试作业评分系统场景的完整流程
  - 测试工具箱模块场景的完整流程
  - 测试错误恢复机制
  - 测试备份和恢复功能
  - 准备测试用的Word文档和Excel文件
  - _需求: 所有_

- [x] 6.3 编写使用文档
  - 在`docs/`目录创建功能说明文档
  - 说明两种使用场景的区别
  - 说明文件命名规范（Word和Excel）
  - 说明登分册和成绩文件的格式要求
  - 提供常见问题解答
  - _需求: 所有_

- [x] 7. 性能优化和安全加固
  - 实现性能优化措施
  - 加强安全检查
  - 添加并发控制
  - 优化大文件处理
  - _需求: 5, 18, 19_

- [x] 7.1 性能优化
  - 实现批量读取文件列表
  - 优化Excel读写操作（使用read_only和write_only模式）
  - 添加文件数量限制（超过500个文件警告）
  - 缓存学生列表避免重复查询
  - 工具箱场景下批量处理Excel文件中的学生记录
  - _需求: 19_

- [x] 7.2 安全加固
  - 强化路径验证逻辑
  - 添加文件大小检查
  - 验证Excel文件完整性
  - 添加租户隔离检查
  - 记录所有安全相关事件
  - _需求: 5, 18, 21_

- [x] 7.3 添加并发控制
  - 检测Excel文件是否被占用
  - 添加文件锁机制
  - 处理并发写入冲突
  - _需求: 15_
