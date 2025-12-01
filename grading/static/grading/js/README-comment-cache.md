# 评价缓存服务 (CommentCacheService)

## 概述

评价缓存服务是一个前端JavaScript类，用于自动保存教师输入的评价内容到浏览器本地存储，防止意外情况下评价内容丢失。

## 功能特性

### 1. 自动保存 (需求 5.1.1)
- 每隔2秒自动将评价内容保存到浏览器本地存储
- 为每个文件维护独立的缓存

### 2. 缓存加载 (需求 5.1.3, 5.1.4, 5.1.5)
- 重新打开评价对话框时自动检查缓存
- 如果缓存与已保存内容不同，提示用户是否恢复
- 支持恢复缓存内容到输入框

### 3. 缓存清除 (需求 5.1.6)
- 评价成功保存后自动清除缓存
- 支持手动清除指定文件的缓存

### 4. 过期清理 (需求 5.1.7)
- 自动清理7天前的过期缓存
- 启动时自动执行清理
- 支持手动触发清理

### 5. 独立文件缓存 (需求 5.1.8)
- 每个文件的评价缓存独立存储
- 使用文件路径哈希作为缓存键

## 使用方法

### 初始化

服务在页面加载时自动初始化，创建全局实例：

```javascript
window.commentCacheService = new CommentCacheService();
```

### API 方法

#### autosave(filePath, commentText)
启动自动保存，2秒后将内容保存到本地存储。

```javascript
// 在输入框的 input 事件中调用
$('#teacherCommentText').on('input', function() {
    const commentText = $(this).val();
    window.commentCacheService.autosave(currentFilePath, commentText);
});
```

#### load(filePath)
加载指定文件的缓存数据。

```javascript
const cacheData = window.commentCacheService.load(filePath);
if (cacheData) {
    console.log('缓存内容:', cacheData.comment);
    console.log('缓存时间:', new Date(cacheData.timestamp));
}
```

返回值：
```javascript
{
    comment: "评价内容",
    timestamp: 1234567890,
    file_path: "/path/to/file"
}
```

#### clear(filePath)
清除指定文件的缓存。

```javascript
// 评价保存成功后清除缓存
window.commentCacheService.clear(currentFilePath);
```

#### cleanupExpired()
清理所有过期缓存（7天前）。

```javascript
// 手动触发清理
window.commentCacheService.cleanupExpired();
```

#### stopAutosave()
停止当前的自动保存定时器。

```javascript
// 模态框关闭时停止自动保存
$('#teacherCommentModal').on('hide.bs.modal', function() {
    window.commentCacheService.stopAutosave();
});
```

#### hasCache(filePath)
检查指定文件是否有缓存。

```javascript
if (window.commentCacheService.hasCache(filePath)) {
    console.log('该文件有缓存');
}
```

#### getAllCachedFiles()
获取所有缓存的文件列表。

```javascript
const files = window.commentCacheService.getAllCachedFiles();
files.forEach(file => {
    console.log('文件:', file.filePath);
    console.log('内容:', file.comment);
    console.log('时间:', new Date(file.timestamp));
});
```

## 集成示例

### 在 grading.js 中的集成

```javascript
// 1. 评价输入框自动保存
$(document).on('input', '#teacherCommentText', function() {
    const commentText = $(this).val();
    if (currentFilePath && window.commentCacheService) {
        window.commentCacheService.autosave(currentFilePath, commentText);
    }
});

// 2. 加载评价时检查缓存
function loadTeacherComment(filePath) {
    $.ajax({
        url: '/grading/get_teacher_comment/',
        success: function(response) {
            const savedComment = response.comment || '';
            
            // 检查缓存
            const cachedData = window.commentCacheService.load(filePath);
            
            if (cachedData && cachedData.comment !== savedComment) {
                // 提示用户是否恢复缓存
                if (confirm('检测到未保存的评价内容，是否恢复？')) {
                    $('#teacherCommentText').val(cachedData.comment);
                } else {
                    $('#teacherCommentText').val(savedComment);
                    window.commentCacheService.clear(filePath);
                }
            } else {
                $('#teacherCommentText').val(savedComment);
            }
        }
    });
}

// 3. 保存成功后清除缓存
function saveTeacherComment() {
    $.ajax({
        url: '/grading/save_teacher_comment/',
        success: function(response) {
            if (response.success) {
                // 清除缓存
                window.commentCacheService.clear(currentFilePath);
            }
        }
    });
}

// 4. 模态框关闭时停止自动保存
$('#teacherCommentModal').on('hide.bs.modal', function() {
    window.commentCacheService.stopAutosave();
});
```

## 测试

使用测试页面验证功能：

1. 在浏览器中打开 `test-comment-cache.html`
2. 测试各项功能：
   - 自动保存
   - 加载缓存
   - 清除缓存
   - 清理过期缓存
   - 查看所有缓存

## 技术细节

### 存储格式

缓存数据存储在 `localStorage` 中，格式如下：

```javascript
// 键名格式
"comment_cache_<hash>"

// 值格式
{
    "comment": "评价内容",
    "timestamp": 1234567890,
    "file_path": "/path/to/file"
}
```

### 哈希算法

使用简单的字符串哈希算法生成缓存键，避免路径过长导致的存储问题。

### 过期策略

- 缓存有效期：7天
- 清理时机：
  - 服务初始化时
  - 手动调用 `cleanupExpired()`
  - 加载缓存时检查过期

### 存储空间管理

如果 `localStorage` 空间不足（QuotaExceededError），会自动清理过期缓存后重试。

## 浏览器兼容性

- 支持所有现代浏览器（Chrome, Firefox, Safari, Edge）
- 需要浏览器支持 `localStorage` API
- 需要浏览器支持 ES6 类语法

## 注意事项

1. **隐私模式**：在浏览器隐私模式下，`localStorage` 可能不可用或在会话结束后清除
2. **存储限制**：`localStorage` 通常有 5-10MB 的存储限制
3. **跨域限制**：缓存数据仅在同一域名下可访问
4. **数据持久性**：用户清除浏览器数据会删除所有缓存

## 需求映射

| 需求编号 | 需求描述 | 实现方法 |
|---------|---------|---------|
| 5.1.1 | 每隔2秒自动缓存评价内容 | `autosave()` 方法 |
| 5.1.2 | 评价对话框意外关闭保留缓存 | 缓存持久化到 localStorage |
| 5.1.3 | 重新打开时检查缓存 | `load()` 方法 |
| 5.1.4 | 缓存与已保存内容不同时提示 | 在 `loadTeacherComment()` 中比较 |
| 5.1.5 | 恢复缓存内容 | 填充到输入框 |
| 5.1.6 | 保存成功后清除缓存 | `clear()` 方法 |
| 5.1.7 | 清理7天前的过期缓存 | `cleanupExpired()` 方法 |
| 5.1.8 | 为每个文件维护独立缓存 | 使用文件路径哈希作为键 |

## 维护和扩展

### 添加新功能

如需添加新功能，可以扩展 `CommentCacheService` 类：

```javascript
class CommentCacheService {
    // ... 现有方法 ...
    
    // 新方法示例
    exportCache() {
        const files = this.getAllCachedFiles();
        return JSON.stringify(files, null, 2);
    }
}
```

### 调试

启用详细日志：

```javascript
// 在浏览器控制台中
localStorage.setItem('debug_comment_cache', 'true');
```

## 相关文件

- `comment-cache-service.js` - 服务实现
- `grading.js` - 集成代码
- `grading.html` - 模板文件
- `test-comment-cache.html` - 测试页面
