# 作业评分系统实现计划

## 第一阶段：数据模型和基础架构

- [x] 1. 更新数据模型
  - 更新Course模型，添加teacher字段和description字段
  - 创建Class模型（班级）
  - 更新Repository模型，支持Git和文件系统两种方式
  - 更新Homework模型，添加class_obj字段
  - 创建Submission模型（学生作业提交）
  - 更新GradeTypeConfig模型，支持百分制
  - 创建CommentTemplate模型（评价模板）
  - _需求: 1.1, 1.2, 1.3, 1.1.1-1.1.9, 1.4.1-1.4.7, 4.1-4.5, 5.2.1-5.2.12_

- [x] 1.1 编写数据模型单元测试
  - 测试Course模型的创建和查询
  - 测试Class模型的课程关联
  - 测试Repository模型的两种方式配置
  - 测试CommentTemplate模型的统计和排序
  - **Property 1: 课程创建完整性**
  - **Validates: Requirements 1.1**

- [x] 2. 创建数据库迁移
  - 生成迁移文件
  - 执行迁移
  - 验证数据库结构
  - _需求: 所有数据模型相关需求_

## 第二阶段：课程和班级管理

- [x] 3. 实现课程管理服务
  - 创建CourseService类
  - 实现create_course方法
  - 实现list_courses方法（教师数据隔离）
  - 实现update_course_type方法
  - _需求: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3.1 编写课程管理服务测试
  - 测试课程创建功能
  - 测试教师数据隔离
  - **Property 2: 教师数据隔离**
  - **Validates: Requirements 1.4**

- [x] 4. 实现班级管理服务
  - 创建ClassService类
  - 实现create_class方法（验证课程关联）
  - 实现list_classes方法
  - 实现get_class_students方法
  - _需求: 1.2, 1.3, 1.5_

- [x] 4.1 编写班级管理服务测试
  - 测试班级创建和课程关联
  - 测试班级列表查询

- [x] 5. 创建课程和班级管理视图
  - 创建课程创建页面和视图
  - 创建班级创建页面和视图
  - 创建课程列表页面
  - 创建班级列表页面
  - 添加URL路由
  - _需求: 1.1-1.5_

## 第三阶段：仓库管理

- [x] 6. 实现仓库管理服务
  - 创建RepositoryService类
  - 实现create_git_repository方法
  - 实现create_filesystem_repository方法
  - 实现generate_directory_name方法（处理重名）
  - 实现validate_git_connection方法
  - 实现validate_directory_structure方法
  - 实现list_repositories方法
  - _需求: 1.1.1-1.1.9, 1.2.1-1.2.5, 1.3.1-1.3.5_

- [x] 6.1 编写仓库管理服务测试
  - 测试Git仓库配置和验证
  - 测试文件系统仓库创建
  - 测试目录名生成和重名处理
  - 测试目录结构验证
  - **Property 3: 目录名唯一性**
  - **Validates: Requirements 1.1.5**
  - **Property 4: 目录结构验证**
  - **Validates: Requirements 1.2.1**

- [x] 7. 创建仓库管理视图
  - 创建仓库配置页面（支持两种方式）
  - 创建仓库列表页面
  - 实现Git连接验证接口
  - 实现目录结构验证接口
  - 添加URL路由
  - _需求: 1.1.1-1.1.9, 1.2.1-1.2.5, 1.3.1-1.3.5_

## 第四阶段：学生作业上传

- [x] 8. 实现文件上传服务
  - 创建FileUploadService类
  - 实现upload_submission方法
  - 实现validate_file方法（格式和大小验证）
  - 实现save_file方法
  - 实现create_submission_record方法
  - _需求: 1.4.1-1.4.7_

- [x] 8.1 编写文件上传服务测试
  - 测试文件格式验证
  - 测试文件大小验证
  - 测试文件路径生成
  - **Property 5: 文件验证规则**
  - **Validates: Requirements 1.4.3**
  - **Property 6: 文件路径生成规范**
  - **Validates: Requirements 1.4.5**

- [x] 9. 创建学生作业上传视图
  - 创建作业上传页面（仅文件系统方式）
  - 实现文件上传接口
  - 实现上传进度显示
  - 实现版本管理（覆盖上传）
  - 添加URL路由
  - _需求: 1.4.1-1.4.7_

## 第五阶段：评分功能增强

- [x] 10. 更新评分服务支持百分制
  - 更新GradingService类
  - 添加百分制评分支持
  - 实现百分制输入验证（0-100）
  - 更新评分写入逻辑（支持三种方式）
  - _需求: 4.1-4.5_

- [x] 10.1 编写百分制评分测试
  - 测试百分制输入验证
  - 测试分数范围检查
  - **Property 7: 百分制分数范围验证**
  - **Validates: Requirements 4.4**

- [x] 11. 实现实验报告强制评价验证
  - 更新GradingService.validate_lab_report_comment方法
  - 在评分保存前验证实验报告是否有评价
  - 实现前端验证（禁用保存按钮）
  - 实现后端验证（阻止保存）
  - _需求: 4.5, 4.6, 4.7, 5.2, 5.3_

- [x] 11.1 编写实验报告评价验证测试
  - 测试实验报告无评价时的阻止逻辑
  - 测试普通作业可选评价
  - **Property 8: 实验报告强制评价**
  - **Validates: Requirements 4.5, 5.2**

- [x] 12. 更新评分界面
  - 添加百分制评分选项
  - 添加百分制输入框和验证
  - 更新评分方式切换逻辑
  - 实现实验报告评价必填提示
  - _需求: 4.1-4.7_

## 第六阶段：评价缓存和模板

- [x] 13. 实现评价缓存服务（前端）
  - 创建CommentCacheService JavaScript类
  - 实现autosave方法（每2秒自动保存）
  - 实现load方法（加载缓存）
  - 实现clear方法（清除缓存）
  - 实现cleanup_expired方法（清理7天前缓存）
  - _需求: 5.1.1-5.1.8_

- [x] 13.1 编写评价缓存功能测试
  - 测试自动保存功能
  - 测试缓存恢复功能
  - 测试过期清理功能

- [x] 14. 实现评价模板服务
  - 创建CommentTemplateService类
  - 实现get_personal_templates方法
  - 实现get_system_templates方法
  - 实现get_recommended_templates方法（个人优先）
  - 实现record_comment_usage方法
  - 实现update_template_ranking方法
  - _需求: 5.2.1-5.2.12_

- [x] 14.1 编写评价模板服务测试
  - 测试评价使用统计
  - 测试模板排序和限制
  - 测试评价内容去重
  - **Property 9: 评价使用统计累加**
  - **Validates: Requirements 5.2.1**
  - **Property 10: 评价模板排序和限制**
  - **Validates: Requirements 5.2.4**
  - **Property 11: 评价内容去重**
  - **Validates: Requirements 5.2.11**

- [x] 15. 创建评价模板视图和接口
  - 创建获取推荐模板API
  - 创建记录评价使用API
  - 更新评价对话框UI（显示模板）
  - 实现模板点击填充功能
  - _需求: 5.2.1-5.2.12_

- [x] 16. 集成评价缓存和模板到评价功能
  - 在评价对话框中集成缓存服务
  - 在评价对话框中显示推荐模板
  - 实现评价保存时的统计更新
  - 实现缓存清除逻辑
  - _需求: 5.1.1-5.1.8, 5.2.1-5.2.12_

## 第七阶段：批量操作更新

- [x] 17. 更新批量评分功能
  - 更新批量评分支持百分制
  - 更新批量评分验证实验报告评价
  - 更新进度显示
  - _需求: 7.1-7.7_

- [x] 18. 更新批量AI评分功能
  - 更新批量AI评分确保实验报告有评价
  - 验证AI返回结果的完整性
  - 更新错误处理
  - _需求: 8.1-8.7, 6.3, 6.4_

## 第八阶段：现有功能维护

- [x] 19. 保持现有核心功能
  - 验证统一函数（find_teacher_signature_cell等）仍然正常工作
  - 验证作业类型判断逻辑
  - 验证格式错误锁定机制
  - 验证文件导航功能
  - _需求: 11.1-11.9, 9.1-9.6_

- [x] 19.1 编写格式验证和锁定测试
  - 测试实验报告格式检测
  - 测试文件锁定机制
  - **Property 12: 实验报告格式检测**
  - **Validates: Requirements 11.2**
  - **Property 13: 文件锁定机制**
  - **Validates: Requirements 11.6**

## 第九阶段：性能优化和缓存

- [x] 20. 实现缓存优化
  - 实现目录文件数量缓存
  - 实现评价模板查询缓存（Redis）
  - 实现课程和班级列表缓存
  - 添加缓存失效逻辑
  - _需求: 14.1-14.9_

- [x] 20.1 编写缓存功能测试
  - 测试缓存避免重复计算
  - 测试缓存失效逻辑
  - **Property 14: 缓存避免重复计算**
  - **Validates: Requirements 14.1**

- [x] 21. 实现数据库优化
  - 添加CommentTemplate模型索引
  - 添加Submission模型索引
  - 添加Repository模型索引
  - 优化查询使用select_related和prefetch_related
  - _需求: 14.1-14.9_

## 第十阶段：测试和文档

- [x] 22. 编写集成测试
  - 测试完整的课程创建到评分流程
  - 测试Git仓库方式的完整流程
  - 测试文件系统方式的完整流程
  - 测试评价缓存和模板的完整流程
  - 测试批量操作流程

- [x] 23. 编写端到端测试
  - 测试教师创建课程和班级
  - 测试学生上传作业
  - 测试教师评分（三种方式）
  - 测试评价模板推荐
  - 测试批量评分和AI评分

- [x] 24. 更新文档
  - 更新README.md
  - 更新API文档
  - 更新用户手册
  - 更新部署文档
  - _需求: 所有需求_

## 第十一阶段：最终验收

- [x] 25. 最终检查点
  - 确保所有测试通过
  - 确认所有需求已实现
  - 验证性能指标
  - 进行安全审计
  - _需求: 所有需求_
