# 缓存和性能优化文档

> **最后更新**: 2025-11-19  
> **版本**: 1.0

## 概述

系统实现了完整的缓存管理和性能优化机制，包括多层缓存、性能监控、阈值检查等功能。

---

## 缓存架构

### 缓存层次

```
┌─────────────────────────────────────┐
│     应用层 (Views/Services)          │
├─────────────────────────────────────┤
│     缓存管理层 (CacheManager)        │
├─────────────────────────────────────┤
│     Django Cache Framework          │
├─────────────────────────────────────┤
│     缓存后端 (Redis/Memcached)       │
└─────────────────────────────────────┘
```

### 缓存类型

| 缓存类型 | 用途 | 过期时间 | 键前缀 |
|---------|------|---------|--------|
| 文件数量缓存 | 目录文件统计 | 5分钟 | `file_count` |
| 目录树缓存 | 目录结构 | 10分钟 | `dir_tree` |
| 文件内容缓存 | 文件内容 | 3分钟 | `file_content` |
| 文件元数据缓存 | 文件信息 | 5分钟 | `file_metadata` |

---

## 核心组件

### 1. CacheManager 类

**位置**: `grading/cache_manager.py`

**功能**:
- 统一的缓存管理接口
- 多租户缓存隔离
- 性能阈值检查
- 缓存统计和监控

**初始化**:
```python
from grading.cache_manager import CacheManager, get_cache_manager

# 方式1: 从请求对象创建
cache_manager = get_cache_manager(request)

# 方式2: 手动指定用户和租户
cache_manager = CacheManager(user_id=1, tenant_id=1)
```

### 2. 缓存键命名规则

**格式**: `{prefix}:{tenant_id}:{user_id}:{identifier}`

**示例**:
```
file_count:tenant_1:user_5:/path/to/directory
dir_tree:tenant_1:user_5:/path/to/root
file_content:tenant_1:user_5:/path/to/file.docx
```

**优点**:
- 租户隔离：不同租户的缓存互不干扰
- 用户隔离：不同用户的缓存独立管理
- 易于批量清除：支持按租户或用户清除

---

## 使用指南

### 文件数量缓存

**场景**: 统计目录中的文件数量

**使用方法**:
```python
# 在视图中使用
from grading.cache_manager import get_cache_manager

def my_view(request):
    cache_manager = get_cache_manager(request)
    
    # 获取缓存的文件数量
    count = cache_manager.get_file_count("/path/to/dir")
    
    if count is None:
        # 缓存未命中，计算文件数量
        count = calculate_file_count("/path/to/dir")
        # 设置缓存
        cache_manager.set_file_count("/path/to/dir", count)
    
    return count
```

**便捷函数**:
```python
# views.py 中已封装的函数
file_count = get_directory_file_count_cached(
    dir_path="/path/to/dir",
    base_dir="/base",
    request=request
)
```

### 目录树缓存

**场景**: 缓存目录树结构，避免重复遍历

**使用方法**:
```python
cache_manager = get_cache_manager(request)

# 获取缓存的目录树
tree = cache_manager.get_dir_tree("/path/to/dir")

if tree is None:
    # 构建目录树
    tree = build_directory_tree("/path/to/dir")
    # 设置缓存
    cache_manager.set_dir_tree("/path/to/dir", tree)
```

### 文件内容缓存

**场景**: 缓存文件内容，减少磁盘I/O

**使用方法**:
```python
cache_manager = get_cache_manager(request)

# 获取缓存的文件内容
cached = cache_manager.get_file_content("/path/to/file.docx")

if cached is None:
    # 读取文件
    content = read_file_content("/path/to/file.docx")
    content_type = "text/html"
    # 设置缓存
    cache_manager.set_file_content("/path/to/file.docx", content, content_type)
else:
    content, content_type = cached
```

### 清除缓存

**场景1: 清除特定缓存**
```python
cache_manager = get_cache_manager(request)

# 清除特定目录的文件数量缓存
cache_manager.clear_file_count("/path/to/dir")

# 清除特定目录的目录树缓存
cache_manager.clear_dir_tree("/path/to/dir")
```

**场景2: 清除用户所有缓存**
```python
cache_manager = get_cache_manager(request)
cache_manager.clear_user_cache()
```

**场景3: 清除租户所有缓存**
```python
cache_manager = get_cache_manager(request)
cache_manager.clear_tenant_cache()
```

**场景4: 清除所有缓存（管理员）**
```python
from grading.cache_manager import clear_all_cache
clear_all_cache()
```

---

## 性能优化

### 1. 性能阈值

| 阈值类型 | 数值 | 说明 |
|---------|------|------|
| 文件数量警告 | 500 | 超过此值显示警告 |
| 批量操作建议 | 200 | 建议分批处理的阈值 |
| 最大文件大小 | 50MB | 单文件大小限制 |

### 2. 性能检查

**文件数量检查**:
```python
cache_manager = get_cache_manager(request)

# 检查文件数量是否超过阈值
result = cache_manager.check_file_count_threshold(file_count=350)

if result["warning"]:
    print(result["message"])      # "文件数量较多（350个），处理可能需要较长时间"
    print(result["suggestion"])   # "建议分批处理或在非高峰时段操作"
```

**文件大小检查**:
```python
cache_manager = get_cache_manager(request)

# 检查文件大小
result = cache_manager.check_file_size("/path/to/large_file.docx")

if result["error"]:
    print(result["message"])  # "文件过大（55.00MB），超过限制（50.00MB）"
```

### 3. 缓存统计

**获取缓存统计信息**:
```python
cache_manager = get_cache_manager(request)
stats = cache_manager.get_cache_stats()

print(stats)
# {
#     "user_id": 1,
#     "tenant_id": 1,
#     "cache_backend": "django.core.cache.backends.redis.RedisCache",
#     "timeouts": {
#         "file_count": 300,
#         "dir_tree": 600,
#         "file_content": 180,
#         "file_metadata": 300
#     },
#     "thresholds": {
#         "max_files_warning": 500,
#         "max_files_batch": 200,
#         "max_file_size_mb": 50.0
#     }
# }
```

---

## 管理命令

### clear_cache 命令

**用法**:
```bash
# 清除所有缓存
conda run -n py313 python manage.py clear_cache

# 清除特定类型的缓存
conda run -n py313 python manage.py clear_cache --type file_count
conda run -n py313 python manage.py clear_cache --type dir_tree
conda run -n py313 python manage.py clear_cache --type file_content
conda run -n py313 python manage.py clear_cache --type file_metadata

# 清除指定用户的缓存
conda run -n py313 python manage.py clear_cache --user 1

# 清除指定租户的缓存
conda run -n py313 python manage.py clear_cache --tenant 1
```

**输出示例**:
```
清除所有缓存...
✓ 已清除所有缓存

缓存配置信息:
  缓存后端: django.core.cache.backends.redis.RedisCache
  超时设置:
    - file_count: 300秒
    - dir_tree: 600秒
    - file_content: 180秒
    - file_metadata: 300秒
  性能阈值:
    - max_files_warning: 500
    - max_files_batch: 200
    - max_file_size_mb: 50.0
```

---

## API接口

### 1. 获取缓存统计

**端点**: `GET /grading/api/cache/stats/`

**权限**: 需要管理员权限

**响应**:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "tenant_id": 1,
    "cache_backend": "django.core.cache.backends.redis.RedisCache",
    "timeouts": {
      "file_count": 300,
      "dir_tree": 600,
      "file_content": 180,
      "file_metadata": 300
    },
    "thresholds": {
      "max_files_warning": 500,
      "max_files_batch": 200,
      "max_file_size_mb": 50.0
    }
  }
}
```

### 2. 清除缓存

**端点**: `POST /grading/api/cache/clear/`

**权限**: 需要管理员权限

**参数**:
- `type`: 缓存类型 (`all`/`file_count`/`dir_tree`/`file_content`/`file_metadata`)
- `scope`: 清除范围 (`all`/`user`/`tenant`)

**请求示例**:
```javascript
$.ajax({
    url: '/grading/api/cache/clear/',
    method: 'POST',
    data: {
        type: 'file_count',
        scope: 'user'
    },
    success: function(response) {
        console.log(response.message);  // "已清除文件数量缓存"
    }
});
```

**响应**:
```json
{
  "success": true,
  "message": "已清除文件数量缓存"
}
```

---

## 配置

### Django Settings

**缓存后端配置** (`settings.py`):
```python
# 推荐使用Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'huali_edu',
        'TIMEOUT': 300,  # 默认5分钟
    }
}

# 或使用Memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# 开发环境可使用本地内存缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### 自定义配置

**修改缓存超时时间**:
```python
# grading/cache_manager.py
class CacheManager:
    # 修改这些常量
    TIMEOUT_FILE_COUNT = 600  # 改为10分钟
    TIMEOUT_DIR_TREE = 1200   # 改为20分钟
```

**修改性能阈值**:
```python
# grading/cache_manager.py
class CacheManager:
    # 修改这些常量
    MAX_FILES_WARNING = 1000  # 改为1000个文件
    MAX_FILES_BATCH = 500     # 改为500个文件
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 改为100MB
```

---

## 最佳实践

### 1. 何时使用缓存

✅ **应该使用缓存的场景**:
- 频繁访问的目录文件统计
- 目录树结构（短时间内多次访问）
- 文件内容（同一文件被多次查看）
- 计算成本高的操作结果

❌ **不应该使用缓存的场景**:
- 实时性要求高的数据
- 频繁变化的数据
- 一次性访问的数据
- 用户特定的敏感数据

### 2. 缓存失效策略

**主动失效**:
```python
# 文件修改后清除相关缓存
def update_file(file_path):
    # 更新文件
    save_file(file_path)
    
    # 清除缓存
    cache_manager = get_cache_manager(request)
    cache_manager.clear_file_content(file_path)
    cache_manager.clear_file_metadata(file_path)
```

**定时失效**:
- 依赖缓存超时时间自动失效
- 适合数据变化不频繁的场景

**手动刷新**:
```python
# 用户刷新页面时清除缓存
if request.GET.get('refresh') == 'true':
    cache_manager = get_cache_manager(request)
    cache_manager.clear_user_cache()
```

### 3. 性能监控

**记录缓存命中率**:
```python
import logging

logger = logging.getLogger(__name__)

def get_with_stats(cache_manager, key):
    value = cache_manager.get_file_count(key)
    if value is not None:
        logger.info(f"缓存命中: {key}")
    else:
        logger.info(f"缓存未命中: {key}")
    return value
```

**监控慢查询**:
```python
import time

start_time = time.time()
result = expensive_operation()
duration = time.time() - start_time

if duration > 2.0:  # 超过2秒
    logger.warning(f"慢查询: {duration:.2f}秒")
```

### 4. 多租户隔离

**确保缓存隔离**:
```python
# ✅ 正确：使用get_cache_manager自动处理租户隔离
cache_manager = get_cache_manager(request)
cache_manager.set_file_count(path, count)

# ❌ 错误：直接使用Django cache可能导致租户数据泄露
from django.core.cache import cache
cache.set(path, count)  # 没有租户隔离！
```

---

## 故障排查

### 问题1: 缓存不生效

**症状**: 数据总是重新计算，缓存似乎不工作

**排查步骤**:
1. 检查缓存后端配置
   ```bash
   conda run -n py313 python manage.py shell
   >>> from django.core.cache import cache
   >>> cache.set('test', 'value', 60)
   >>> cache.get('test')
   'value'
   ```

2. 检查缓存键是否正确
   ```python
   cache_manager = get_cache_manager(request)
   key = cache_manager._make_key("file_count", "/path")
   print(key)  # 应该包含租户和用户信息
   ```

3. 检查缓存是否被意外清除
   ```python
   # 查看日志
   tail -f logs/app.log | grep "缓存清除"
   ```

### 问题2: 缓存数据过期

**症状**: 看到的是旧数据

**解决方案**:
```python
# 手动清除缓存
cache_manager = get_cache_manager(request)
cache_manager.clear_file_count("/path/to/dir")

# 或使用管理命令
conda run -n py313 python manage.py clear_cache --type file_count
```

### 问题3: 内存占用过高

**症状**: 缓存占用大量内存

**解决方案**:
1. 减少缓存超时时间
2. 限制缓存的数据大小
3. 定期清理缓存
4. 使用Redis等外部缓存后端

---

## 性能指标

### 目标性能

| 操作 | 目标时间 | 实际性能 |
|------|---------|---------|
| 目录文件统计（缓存命中） | < 100ms | ~50ms |
| 目录文件统计（缓存未命中） | < 2s | ~1.5s |
| 目录树加载（缓存命中） | < 200ms | ~100ms |
| 目录树加载（缓存未命中） | < 3s | ~2s |
| 文件内容加载（缓存命中） | < 100ms | ~50ms |
| 文件内容加载（缓存未命中） | < 2s | ~1s |

### 缓存命中率

**目标**: > 80%

**监控方法**:
```python
# 在日志中统计
grep "缓存命中" logs/app.log | wc -l
grep "缓存未命中" logs/app.log | wc -l
```

---

## 相关文档

- [Django缓存框架文档](https://docs.djangoproject.com/en/4.2/topics/cache/)
- [Redis文档](https://redis.io/documentation)
- [性能优化最佳实践](./PERFORMANCE_BEST_PRACTICES.md)

---

**文档版本**: 1.0  
**最后更新**: 2025-11-19  
**维护者**: 开发团队
