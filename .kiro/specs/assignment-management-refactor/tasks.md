# Implementation Plan

- [x] 1. 创建存储抽象层和适配器
- [x] 1.1 创建 StorageAdapter 抽象基类
  - 定义统一的接口方法（list_directory, read_file, write_file, create_directory等）
  - 添加类型注解和文档字符串
  - _Requirements: 10.1_

- [x] 1.2 实现 GitStorageAdapter
  - 实现 Git 远程命令封装（ls-tree, show）
  - 添加认证 URL 构建逻辑
  - 实现输出解析方法
  - 集成缓存机制
  - _Requirements: 3.2, 3.4, 10.2, 10.3_

- [x] 1.3 编写 GitStorageAdapter 属性测试





  - **Property 2: 远程仓库目录读取**
  - **Validates: Requirements 3.2, 3.6**

- [x] 1.4 编写 GitStorageAdapter 属性测试




  - **Property 3: 远程仓库文件读取**
  - **Validates: Requirements 3.4**

- [x] 1.5 编写 GitStorageAdapter 属性测试






  - **Property 5: 无本地克隆约束**
  - **Validates: Requirements 3.6**

- [x] 1.6 实现 FileSystemStorageAdapter
  - 实现本地文件系统操作
  - 添加路径验证和安全检查
  - 实现目录自动创建
  - _Requirements: 4.1, 4.2, 4.6_

- [x] 1.7 编写 FileSystemStorageAdapter 单元测试




  - 测试路径验证
  - 测试文件读写
  - 测试目录创建
  - _Requirements: 4.1, 4.2, 4.6_

- [x] 2. 实现工具类和辅助功能



- [x] 2.1 实现 PathValidator 路径验证工具







  - 实现路径清理方法（sanitize_name）
  - 实现路径安全验证（validate_path）
  - 实现作业次数名称生成（generate_assignment_number_name）
  - _Requirements: 4.7, 8.1, 8.2, 8.3, 9.3, 9.4_


- [x] 2.2 编写 PathValidator 属性测试






  - **Property 10: 路径特殊字符处理**
  - **Validates: Requirements 4.7**

- [x] 2.3 编写 PathValidator 属性测试






  - **Property 15: 课程名称验证**
  - **Validates: Requirements 8.1**

- [x] 2.4 编写 PathValidator 属性测试






  - **Property 16: 班级名称验证**
  - **Validates: Requirements 8.2**

- [x] 2.5 编写 PathValidator 属性测试







  - **Property 17: 作业次数格式验证**
  - **Validates: Requirements 8.3**

- [x] 2.6 编写 PathValidator 属性测试






  - **Property 21: 作业次数自动递增**
  - **Validates: Requirements 9.3**

- [x] 2.7 编写 PathValidator 属性测试






  - **Property 22: 作业命名规范一致性**
  - **Validates: Requirements 9.4**

- [x] 2.8 实现 CredentialEncryption 凭据加密工具





  - 实现加密和解密方法
  - 配置加密密钥管理
  - _Requirements: 10.7_

- [x] 2.9 编写 CredentialEncryption 属性测试






  - **Property 30: 凭据安全存储**
  - **Validates: Requirements 10.7**

- [x] 2.10 实现 CacheManager 缓存管理器




  - 实现缓存键生成
  - 实现目录和文件缓存方法
  - 实现缓存失效逻辑
  - _Requirements: 10.4, 10.5, 10.6_
- [x] 2.11 编写 CacheManager 属性测试



- [x] 2.11 编写 CacheManager 属性测试



  - **Property 27: 内存缓存约束**
  - **Validates: Requirements 10.4**

- [x] 2.12 编写 CacheManager 属性测试







  - **Property 28: 缓存自动刷新**
  - **Validates: Requirements 10.5**

- [x] 2.13 编写 CacheManager 属性测试







  - **Property 29: 缓存共享**
  - **Validates: Requirements 10.6**



- [x] 3. 创建 Assignment 模型和数据库迁移




- [x] 3.1 创建 Assignment 模型






  - 定义所有字段（owner, tenant, course, class_obj, storage_type等）
  - 添加索引和约束
  - 实现模型方法
  - _Requirements: 2.1, 7.1, 7.2_

- [x] 3.2 创建数据库迁移







  - 生成迁移文件
  - 应用迁移
  - _Requirements: 所有_

- [x] 3.3 编写 Assignment 模型单元测试
  - 测试字段验证
  - 测试模型方法
  - 测试约束
  - _Requirements: 2.1, 7.1, 7.2_


- [x] 4. 实现 AssignmentManagementService 业务逻辑



- [x] 4.1 实现 create_assignment 方法


  - 实现输入验证
  - 实现作业配置创建
  - 实现文件系统目录创建
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1_


- [x] 4.2 编写 create_assignment 属性测试



  - **Property 1: 表单验证完整性**
  - **Validates: Requirements 2.5**
-

- [x] 4.3 编写 create_assignment 属性测试


  - **Property 6: 目录路径生成规则**
  - **Validates: Requirements 4.1**

- [x] 4.4 编写 create_assignment 属性测试




  - **Property 18: Git URL 验证**
  - **Validates: Requirements 8.4**

- [x] 4.5 编写 create_assignment 属性测试




  - **Property 19: 作业配置唯一性**
  - **Validates: Requirements 8.5**


- [x] 4.6 实现 get_assignment_structure 方法


  - 实现目录结构获取
  - 实现错误处理和友好消息
  - _Requirements: 3.2, 3.3, 3.5_

- [x] 4.7 编写 get_assignment_structure 属性测试






  - **Property 4: 错误消息友好性**
  - **Validates: Requirements 3.5**


- [x] 4.8 实现 list_assignments 方法




  - 实现作业列表查询
  - 实现教师隔离过滤
  - 实现课程和班级筛选
  - _Requirements: 5.1, 7.4_


- [x] 4.9 编写 list_assignments 属性测试





  - **Property 12: 教师作业列表隔离**
  - **Validates: Requirements 5.1**

- [x] 4.10 实现 update_assignment 方法




  - 实现作业配置更新
  - 实现数据完整性保护
  - _Requirements: 5.3, 5.4_
-

- [x] 4.11 编写 update_assignment 属性测试





  - **Property 13: 编辑保留数据完整性**
  - **Validates: Requirements 5.4**


- [x] 4.12 实现 delete_assignment 方法


  - 实现删除确认逻辑
  - 实现级联删除处理
  - _Requirements: 5.5_

- [-] 5. 实现学生作业提交功能



- [x] 5.1 实现学生作业提交服务






  - 实现课程列表获取（按学生班级过滤）
  - 实现作业次数目录列表
  - 实现文件上传处理
  - _Requirements: 9.1, 9.2, 9.5, 9.6, 9.7_


- [x] 5.2 编写学生作业提交属性测试









  - **Property 20: 学生课程列表隔离**
  - **Validates: Requirements 9.1**


- [x] 5.3 编写文件名处理属性测试






  - **Property 8: 文件名学生姓名验证**
  - **Validates: Requirements 4.3**


- [x] 5.4 编写文件名处理属性测试








  - **Property 11: 文件名唯一性**
  - **Validates: Requirements 4.8**
-

- [-] 5.5 编写文件名处理属性测试






  - **Property 23: 文件名自动处理**
  - **Validates: Requirements 9.5**

- [x] 5.6 编写文件格式验证属性测试








  - **Property 24: 文件格式验证**
  - **Validates: Requirements 9.6**

- [x] 5.7 编写文件覆盖属性测试









  - **Property 25: 文件覆盖规则**
  - **Validates: Requirements 9.7**

- [x] 5.8 实现作业次数目录创建





  - 实现自动命名逻辑
  - 实现目录创建
  - _Requirements: 4.4, 9.3, 9.4, 9.8_


- [x] 5.9 编写目录创建属性测试








  - **Property 9: 作业目录自动创建**
  - **Validates: Requirements 4.4, 4.6**


- [x] 5.10 实现文件存储路径处理





  - 实现路径生成
  - 实现班级目录隔离
  - _Requirements: 4.2, 7.3_

- [x] 5.11 编写文件存储属性测试









  - **Property 7: 文件存储路径规则**
  - **Validates: Requirements 4.2**
-

- [x] 5.12 编写班级隔离属性测试







  - **Property 14: 班级目录隔离**
  - **Validates: Requirements 7.3**


- [x] 6. 更新视图和 URL 路由






- [x] 6.1 创建作业管理视图



  - 实现作业列表视图（assignment_list_view）
  - 实现作业创建视图（assignment_create_view）
  - 实现作业编辑视图（assignment_edit_view）
  - 实现作业删除视图（assignment_delete_view）
  - _Requirements: 1.1, 1.2, 5.1, 5.2, 5.3, 5.5_



- [x] 6.2 编写视图单元测试




  - 测试权限检查
  - 测试表单处理
  - 测试响应格式
  - _Requirements: 5.1, 5.2, 5.3, 5.5_



- [x] 6.3 创建作业结构 API 视图



  - 实现目录结构获取 API（get_assignment_structure_api）
  - 实现文件内容获取 API（get_assignment_file_api）
  - _Requirements: 3.2, 3.3, 3.4_




- [x] 6.4 编写 API 视图单元测试




  - 测试 JSON 响应
  - 测试错误处理

  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 6.5 创建学生作业提交视图




  - 实现作业提交页面视图（student_submission_view）
  - 实现文件上传 API（upload_assignment_file_api）
  - 实现作业目录创建 API（create_assignment_directory_api）

  - _Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.8_


- [x] 6.6 编写学生提交视图单元测试




  - 测试文件上传
  - 测试目录创建

  - 测试权限检查
  - _Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.8_


- [x] 6.7 更新 URL 路由




  - 重命名路由（repository → assignment）
  - 移除同步相关路由
  - 添加新的 API 路由
  - _Requirements: 1.1, 6.1_



- [-] 7. 更新模板和前端代码





- [x] 7.1 更新作业管理模板



  - 重命名模板文件（repository_*.html → assignment_*.html）
  - 更新术语（仓库 → 作业）
  - 移除同步按钮和相关UI
  - 添加提交方式选择器
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 6.1_






- [x] 7.2 创建作业配置表单模板




  - 实现动态字段显示（Git/文件上传）
  - 实现课程和班级选择器
  - 实现表单验证提示
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 7.2, 8.6_

- [x] 7.3 更新评分界面模板



  - 移除同步相关UI
  - 添加加载指示器
  - 优化文件预览
  - _Requirements: 3.4, 6.1, 6.2, 6.3, 6.4, 6.5_



- [x] 7.4 创建学生作业提交模板



  - 实现课程选择界面
  - 实现作业次数列表显示
  - 实现"创建新作业"按钮
  - 实现文件上传界面
  - _Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.8_


- [x] 7.5 更新 JavaScript 代码




  - 重命名 API 调用
  - 实现动态表单字段切换
  - 实现文件上传进度显示
  - 实现错误消息显示
  - _Requirements: 2.2, 3.5, 9.5, 9.6_






- [x] 7.6 编写前端集成测试






  - 测试表单交互
  - 测试文件上传
  - 测试错误提示


  - _Requirements: 2.2, 9.5, 9.6_


- [x] 8. 更新 Django Admin 配置






- [x] 8.1 更新 Assignment Admin


  - 重命名 Admin 类（RepositoryAdmin → AssignmentAdmin）

  - 更新 list_display 字段
  - 移除同步相关操作
  - 添加课程和班级筛选器
  - _Requirements: 1.1, 1.3, 5.1, 5.2, 7.4_

- [x] 8.2 更新 Admin 表单


  - 实现动态字段显示
  - 添加密码加密处理
  - _Requirements: 2.2, 10.7_


- [x] 8.3 编写 Admin 单元测试





  - 测试列表显示
  - 测试筛选器
  - 测试表单验证


  - _Requirements: 5.1, 5.2, 7.4_

- [x] 9. 更新文档和帮助信息



- [x] 9.1 更新用户文档


  - 更新术语说明
  - 添加作业管理指南
  - 添加学生提交指南
  - _Requirements: 1.4_


- [x] 9.2 更新 API 文档


  - 更新 API 端点说明
  - 添加请求/响应示例
  - _Requirements: 所有_

- [x] 9.3 更新代码注释


  - 更新模型注释
  - 更新服务注释
  - 更新视图注释
  - _Requirements: 所有_

- [x] 10. Checkpoint - 确保所有测试通过


  - 运行所有单元测试
  - 运行所有属性测试
  - 运行集成测试
  - 修复发现的问题
  - 确保所有测试通过，如有问题请询问用户

