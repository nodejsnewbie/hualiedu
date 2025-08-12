# 多租户系统实现文档

## 🏗️ 系统架构

### 核心概念

1. **租户 (Tenant)**: 独立的组织或机构，拥有自己的用户、配置和数据
2. **用户配置文件 (UserProfile)**: 扩展Django User模型，关联用户到特定租户
3. **租户配置 (TenantConfig)**: 每个租户的独立配置参数
4. **全局配置 (GlobalConfig)**: 超级管理员管理的系统级配置

### 权限层级

- **超级管理员**: 管理所有租户，配置全局参数
- **租户管理员**: 管理自己租户内的用户和配置
- **普通用户**: 使用租户内的功能

## 📊 数据库模型

### 1. Tenant (租户)
```python
class Tenant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. UserProfile (用户配置文件)
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    repo_base_dir = models.CharField(max_length=500, blank=True)
    is_tenant_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3. GlobalConfig (全局配置)
```python
class GlobalConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 4. TenantConfig (租户配置)
```python
class TenantConfig(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 🔧 中间件和装饰器

### MultiTenantMiddleware
- 自动为用户创建默认租户和配置文件
- 在请求中注入租户信息
- 处理租户隔离

### 权限装饰器
- `@require_superuser`: 要求超级用户权限
- `@require_tenant_admin`: 要求租户管理员权限

## 🌐 URL路由

### 超级管理员路由
```
/super-admin/                    # 超级管理员仪表板
/super-admin/tenants/            # 租户管理
/super-admin/tenants/create/     # 创建租户
/super-admin/tenants/update/     # 更新租户
```

### 租户管理员路由
```
/tenant-admin/                   # 租户管理员仪表板
/tenant-admin/users/             # 用户管理
/tenant-admin/users/add/         # 添加用户
/tenant-admin/users/update/      # 更新用户
/tenant-admin/users/remove/      # 移除用户
/tenant-admin/config/            # 配置管理
/tenant-admin/config/update/     # 更新配置
```

## 🎯 核心功能

### 1. 租户隔离
- 每个租户的数据完全隔离
- 用户只能访问自己租户的资源
- 评分类型配置按租户隔离

### 2. 动态基础目录
- 每个用户/租户可以配置自己的仓库基础目录
- 支持用户级和租户级配置
- 自动回退到全局默认配置

### 3. 权限管理
- 超级管理员：管理所有租户
- 租户管理员：管理自己租户的用户和配置
- 普通用户：使用租户功能

### 4. 配置管理
- 全局配置：系统级参数
- 租户配置：租户级参数
- 用户配置：用户级参数

## 🚀 使用指南

### 1. 创建租户
```python
# 通过超级管理员界面创建
# 或通过API创建
tenant = Tenant.objects.create(
    name="新租户",
    description="租户描述",
    is_active=True
)
```

### 2. 添加用户到租户
```python
# 通过租户管理员界面添加
# 或通过API添加
profile = UserProfile.objects.create(
    user=user,
    tenant=tenant,
    repo_base_dir="~/jobs/tenant1",
    is_tenant_admin=True
)
```

### 3. 配置租户参数
```python
# 设置租户配置
TenantConfig.set_value(tenant, "api_key", "your-api-key", "API密钥")
```

### 4. 获取用户配置
```python
# 在视图中获取用户租户信息
tenant = request.tenant
profile = request.user_profile
base_dir = profile.get_repo_base_dir()
```

## 🔒 安全特性

### 1. 数据隔离
- 数据库级别的租户隔离
- 中间件自动注入租户信息
- 视图层权限验证

### 2. 权限控制
- 装饰器级别的权限检查
- 租户管理员权限验证
- 超级管理员权限验证

### 3. 配置安全
- 敏感配置加密存储
- 租户级配置隔离
- 用户级配置隔离

## 📈 扩展性

### 1. 新租户类型
- 可以轻松添加新的租户类型
- 支持租户级别的功能开关
- 支持租户级别的计费

### 2. 新功能模块
- 评分系统已支持多租户
- 可以扩展其他功能模块
- 支持租户级别的自定义

### 3. 性能优化
- 支持租户级别的缓存
- 支持租户级别的数据库分片
- 支持租户级别的CDN配置

## 🧪 测试

### 运行测试脚本
```bash
python test_multi_tenant.py
```

### 测试内容
1. 租户创建和管理
2. 用户配置文件创建
3. 租户隔离验证
4. 配置管理测试
5. 权限验证测试

## 📝 部署注意事项

### 1. 数据库迁移
```bash
python manage.py makemigrations grading
python manage.py migrate
```

### 2. 中间件配置
确保在 `settings.py` 中添加了多租户中间件：
```python
MIDDLEWARE = [
    # ... 其他中间件
    "grading.middleware.MultiTenantMiddleware",
]
```

### 3. 初始配置
- 创建超级管理员用户
- 设置全局默认配置
- 创建初始租户

## 🔄 迁移指南

### 从单租户到多租户
1. 备份现有数据
2. 运行数据库迁移
3. 创建默认租户
4. 迁移现有用户到租户
5. 测试功能完整性

### 数据迁移脚本
```python
# 示例：迁移现有用户到默认租户
default_tenant = Tenant.objects.get_or_create(name="默认租户")[0]
for user in User.objects.all():
    UserProfile.objects.get_or_create(
        user=user,
        defaults={'tenant': default_tenant}
    )
```

## 🎉 总结

多租户系统已成功实现，具备以下特性：

✅ **完整的租户隔离** - 数据、配置、权限完全隔离
✅ **灵活的权限管理** - 超级管理员、租户管理员、普通用户三级权限
✅ **动态配置系统** - 支持全局、租户、用户三级配置
✅ **自动用户管理** - 中间件自动创建用户配置文件
✅ **评分系统集成** - 评分类型配置支持多租户
✅ **完整的管理界面** - 超级管理员和租户管理员仪表板
✅ **安全可靠** - 多层权限验证和数据隔离

系统已准备好支持多租户部署，可以满足不同组织的独立需求。
