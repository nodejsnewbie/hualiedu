# 多租户系统

## 系统架构

### 核心概念
- **租户 (Tenant)**: 独立的组织或机构
- **用户配置文件 (UserProfile)**: 扩展Django User模型
- **租户配置 (TenantConfig)**: 租户级别的配置参数
- **全局配置 (GlobalConfig)**: 系统级配置参数

### 权限层级
- **超级管理员**: 管理所有租户和全局配置
- **租户管理员**: 管理自己租户内的用户和配置
- **普通用户**: 使用租户内的功能

## 数据模型

### Tenant (租户)
```python
class Tenant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### UserProfile (用户配置文件)
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    repo_base_dir = models.CharField(max_length=500, blank=True)
    is_tenant_admin = models.BooleanField(default=False)
```

## 核心功能

### 1. 租户隔离
- 数据完全隔离
- 用户只能访问自己租户的资源
- 配置按租户分离

### 2. 权限管理
- 三级权限体系
- 装饰器级别的权限检查
- 自动权限验证

### 3. 配置管理
- 全局配置：系统级参数
- 租户配置：租户级参数
- 用户配置：用户级参数

## 使用指南

### 创建租户
1. 超级管理员登录系统
2. 访问租户管理页面
3. 创建新租户
4. 配置租户参数

### 用户管理
1. 租户管理员登录
2. 访问用户管理页面
3. 添加/删除用户
4. 设置用户权限

### 配置管理
1. 设置租户级配置
2. 管理用户基础目录
3. 配置API密钥等参数

## 部署配置

### 中间件配置
```python
MIDDLEWARE = [
    # ... 其他中间件
    "grading.middleware.MultiTenantMiddleware",
]
```

### 数据库迁移
```bash
python manage.py makemigrations grading
python manage.py migrate
```

### 初始化
1. 创建超级管理员
2. 设置全局默认配置
3. 创建初始租户

## 安全特性

### 数据隔离
- 数据库级别的租户隔离
- 中间件自动注入租户信息
- 视图层权限验证

### 权限控制
- 装饰器级别的权限检查
- 租户管理员权限验证
- 超级管理员权限验证

### 配置安全
- 敏感配置加密存储
- 租户级配置隔离
- 用户级配置隔离
