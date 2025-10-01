# 仓库管理功能

## 功能概述

仓库管理功能允许每个用户管理自己的代码仓库和作业目录，支持本地目录和Git仓库两种类型，实现了个人化的作业评分环境。

## 核心特性

### 1. 用户级仓库管理
- 每个用户可以创建和管理自己的仓库
- 支持本地目录和Git仓库两种类型
- 仓库数据完全隔离，用户只能访问自己的仓库

### 2. 仓库类型支持

#### 本地目录
- 适用于本地存储的作业文件
- 直接指定相对路径即可
- 适合单机部署环境

#### Git仓库
- 支持远程Git仓库克隆和同步
- 自动管理分支切换
- 支持定期同步更新

### 3. 集成评分系统
- 评分页面自动加载用户仓库列表
- 选择仓库后动态加载文件树
- 无缝集成AI评分和批量评分功能

## 使用指南

### 创建仓库

1. **访问仓库管理页面**
   - 点击导航栏"仓库管理"
   - 或从首页点击"📁 仓库管理"

2. **添加本地目录仓库**
   ```
   仓库名称: my-homework
   仓库类型: 本地目录
   本地路径: homework/2024-spring
   描述: 2024年春季学期作业
   ```

3. **添加Git仓库**
   ```
   仓库名称: student-projects
   仓库类型: Git仓库
   Git仓库URL: https://github.com/user/student-projects.git
   默认分支: main
   描述: 学生项目仓库
   ```

### 管理仓库

#### 编辑仓库信息
- 点击仓库卡片上的"编辑"按钮
- 修改仓库名称、路径、描述等信息
- 注意：仓库类型创建后不可更改

#### 同步Git仓库
- 对于Git仓库，点击"同步"按钮
- 首次同步会克隆整个仓库
- 后续同步会拉取最新更改

#### 删除仓库
- 点击"删除"按钮进行软删除
- 仓库数据不会立即删除，只是标记为非激活状态
- 可以通过管理员恢复

### 在评分系统中使用

1. **选择仓库**
   - 进入作业评分页面
   - 在左侧"仓库选择"下拉框中选择要评分的仓库
   - 系统会自动加载该仓库的文件树

2. **文件操作**
   - 选择仓库后可以浏览文件目录
   - 点击文件进行查看和评分
   - 支持AI评分和手动评分

3. **批量操作**
   - 批量登分和批量AI评分功能会基于选择的仓库进行
   - 可以对整个仓库或特定目录进行批量处理

## 数据模型

### Repository模型字段

```python
class Repository(models.Model):
    owner = models.ForeignKey(User)           # 仓库所有者
    tenant = models.ForeignKey(Tenant)        # 所属租户
    name = models.CharField(max_length=255)   # 仓库名称
    path = models.CharField(max_length=500)   # 本地路径
    url = models.URLField(blank=True)         # Git仓库URL
    branch = models.CharField(default='main') # 默认分支
    description = models.TextField(blank=True) # 描述
    repo_type = models.CharField(             # 仓库类型
        choices=[('local', '本地目录'), ('git', 'Git仓库')]
    )
    is_active = models.BooleanField(default=True)    # 是否激活
    last_sync = models.DateTimeField(null=True)      # 最后同步时间
```

### 权限控制
- 用户只能管理自己创建的仓库
- 仓库名称在用户范围内唯一
- 支持多租户隔离

## API接口

### 获取仓库列表
```
GET /grading/api/repositories/
```

### 添加仓库
```
POST /grading/add-repository/
```

### 更新仓库
```
POST /grading/update-repository/
```

### 删除仓库
```
POST /grading/delete-repository/
```

### 同步仓库
```
POST /grading/sync-repository/
```

## 技术实现

### 前端功能
- 响应式仓库管理界面
- AJAX异步操作
- 实时状态更新
- 表单验证和错误处理

### 后端功能
- Django ORM数据管理
- Git操作集成
- 文件系统安全验证
- 多租户支持

### 安全特性
- 路径安全验证
- 用户权限检查
- 仓库隔离
- 操作日志记录

## 配置要求

### 环境变量
```bash
# 用户基础目录（可选）
USER_BASE_DIR=~/repositories

# Git配置（如需要）
GIT_USER_NAME=your_name
GIT_USER_EMAIL=your_email@example.com
```

### 系统依赖
- Git（用于Git仓库功能）
- 文件系统读写权限
- 网络访问（用于远程仓库）

## 最佳实践

### 仓库组织
1. **按学期组织**
   ```
   2024-spring-homework/
   ├── class1/
   ├── class2/
   └── assignments/
   ```

2. **按课程组织**
   ```
   python-course/
   ├── homework1/
   ├── homework2/
   └── projects/
   ```

### 命名规范
- 使用有意义的仓库名称
- 避免特殊字符和空格
- 建议使用小写字母和连字符

### 同步策略
- 定期同步Git仓库获取最新内容
- 在评分前确保仓库是最新状态
- 备份重要的评分数据

## 故障排除

### 常见问题

1. **仓库路径不存在**
   - 检查路径配置是否正确
   - 确保有相应目录的访问权限

2. **Git同步失败**
   - 检查网络连接
   - 验证Git仓库URL是否正确
   - 确保有仓库访问权限

3. **文件加载失败**
   - 检查仓库是否已激活
   - 验证文件路径权限
   - 查看系统日志获取详细错误信息

### 日志查看
```bash
# 查看仓库操作日志
tail -f logs/app.log | grep repository

# 查看Git操作日志
tail -f logs/app.log | grep git
```

## 未来扩展

### 计划功能
- 仓库模板支持
- 批量仓库导入
- 仓库统计分析
- 自动化同步任务
- 仓库共享功能

### 集成计划
- CI/CD集成
- 代码质量检查
- 自动化测试
- 性能监控
