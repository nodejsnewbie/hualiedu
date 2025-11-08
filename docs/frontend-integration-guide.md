# 前端集成指南

## 课程类型自动识别

### 功能说明

当用户选择课程时，系统会：
1. 自动调用API获取课程信息
2. 根据课程类型自动设置"实验课"复选框
3. 在课程选择框旁显示类型标签
4. 如果课程不存在，自动创建并识别类型

### 实现代码

#### 1. 课程选择事件处理

```javascript
$('#courseSelect').change(function() {
    const selectedCourse = $(this).val();
    
    if (selectedCourse) {
        // 调用API获取课程信息
        $.ajax({
            url: '/grading/api/course-info/',
            method: 'GET',
            data: {
                course_name: selectedCourse,
                auto_create: true  // 自动创建课程
            },
            success: function(response) {
                if (response.success && response.course) {
                    const courseType = response.course.course_type;
                    const isLab = (courseType === 'lab' || 
                                  courseType === 'practice' || 
                                  courseType === 'mixed');
                    
                    // 自动设置复选框
                    $('#isLabCourse').prop('checked', isLab);
                    
                    // 显示类型标签
                    const typeDisplay = response.course.course_type_display;
                    showCourseTypeBadge(typeDisplay, isLab);
                }
            }
        });
    }
});
```

#### 2. 显示类型标签

```javascript
function showCourseTypeBadge(typeDisplay, isLab) {
    let badge = '';
    if (isLab) {
        badge = '<span class="badge bg-info ms-2">实验课</span>';
    } else {
        badge = '<span class="badge bg-secondary ms-2">理论课</span>';
    }
    
    // 移除旧标签
    $('#courseSelect').next('.course-type-badge').remove();
    // 添加新标签
    $('#courseSelect').after(`<span class="course-type-badge">${badge}</span>`);
}
```

### API响应格式

```json
{
    "success": true,
    "course": {
        "id": 1,
        "name": "Web前端开发",
        "course_type": "lab",
        "course_type_display": "实验课",
        "description": "...",
        "in_database": true,
        "auto_created": false
    }
}
```

### 课程类型映射

| course_type | 显示名称 | 是否为实验课 |
|-------------|----------|--------------|
| theory | 理论课 | 否 |
| lab | 实验课 | 是 |
| practice | 实践课 | 是 |
| mixed | 理论+实验 | 是 |

### UI效果

#### 选择理论课
```
[课程选择框: 数据结构 ▼]
  课程类型：[理论课 ▼]
```

#### 选择实验课
```
[课程选择框: Web前端开发 ▼]
  课程类型：[实验课 ▼]
```

#### 修改课程类型（自动保存）
```
1. 选择课程
2. 在下拉框中选择新的类型
3. 系统自动保存到数据库
4. 显示"✓ 已保存"提示（2秒后消失）
```

### 评分时传递参数

```javascript
// 保存评分时，传递课程信息
$.ajax({
    url: '/grading/add_grade_to_file/',
    method: 'POST',
    data: {
        path: filePath,
        grade: grade,
        course: currentCourse,  // 课程名称
        repo_id: currentRepoId
    }
});
```

系统会根据课程名称自动判断是否为实验报告，使用正确的评分格式。

### 调试信息

在浏览器控制台可以看到：

```
课程类型: 实验课 (lab)
实验课模式: 是
```

### 错误处理

如果API调用失败：
- 复选框仍然可用
- 用户可以手动选择
- 不影响正常评分流程

### 测试步骤

1. 打开评分页面
2. 选择仓库
3. 选择课程（如"Web前端开发"）
4. 观察：
   - 复选框自动勾选
   - 显示"实验课"标签
   - 控制台输出课程类型信息

### 相关文件

- 模板文件：`templates/grading_simple.html`
- API接口：`/grading/api/course-info/`
- 后端视图：`grading/views.py` - `get_course_info_api()`

### 常见问题

#### Q1: 复选框没有自动勾选？

**检查步骤**：
1. 打开浏览器控制台
2. 查看是否有API调用错误
3. 检查课程是否在数据库中
4. 检查课程类型设置

#### Q2: 显示的类型不正确？

**解决方案**：
```bash
# 在Django Shell中检查
python manage.py shell
>>> from grading.models import Course
>>> c = Course.objects.get(name='Web前端开发')
>>> print(c.course_type)
>>> c.course_type = 'lab'
>>> c.save()
```

#### Q3: 新课程没有自动创建？

**可能原因**：
- 没有可用的学期
- 没有可用的教师用户
- API参数 `auto_create=false`

**解决方案**：
```bash
# 创建学期
python manage.py shell -c "from grading.models import Semester; from datetime import date; Semester.objects.create(name='2025年秋季学期', start_date=date(2025,9,1), end_date=date(2026,1,15), is_active=True)"
```

### 扩展功能

#### 显示更多课程信息

```javascript
success: function(response) {
    if (response.success && response.course) {
        // 显示课程描述
        if (response.course.description) {
            $('#courseDescription').text(response.course.description);
        }
        
        // 显示是否自动创建
        if (response.course.auto_created) {
            showNotification('课程已自动创建', 'info');
        }
    }
}
```

#### 根据课程类型调整UI

```javascript
if (isLab) {
    // 实验课UI
    $('.lab-report-options').show();
    $('.normal-homework-options').hide();
} else {
    // 理论课UI
    $('.lab-report-options').hide();
    $('.normal-homework-options').show();
}
```

### 最佳实践

1. **总是传递课程名称**：评分时传递 `course` 参数
2. **启用自动创建**：使用 `auto_create=true`
3. **显示用户反馈**：显示课程类型标签
4. **错误处理**：API失败时允许手动选择
5. **调试信息**：在控制台输出关键信息

### 相关文档

- [快速开始指南](quick-start-guide.md)
- [作业管理指南](homework-management-guide.md)
- [功能文档](features/homework-grading.md)


## 修改课程类型

### 功能说明

用户可以在前端直接修改课程类型，无需访问Django Admin。

### 使用步骤

1. **选择课程**
   - 系统自动加载当前课程类型
   - 课程类型显示在课程选择框下方

2. **修改类型**（可选）
   - 在下拉框中选择新的类型：
     - 理论课
     - 实验课
     - 实践课
     - 理论+实验
   - 系统自动保存到数据库
   - 显示"✓ 已保存"提示

### API接口

```
POST /grading/api/update-course-type/

参数：
- course_name: 课程名称
- course_type: 课程类型 (theory/lab/practice/mixed)

响应：
{
    "success": true,
    "message": "课程类型已更新",
    "course": {
        "id": 1,
        "name": "Web前端开发",
        "course_type": "lab",
        "course_type_display": "实验课",
        "old_type": "theory"
    }
}
```

### 实现代码

```javascript
$('#saveCourseTypeBtn').click(function() {
    const selectedCourse = $('#courseSelect').val();
    const courseType = $('#courseTypeSelect').val();
    
    $.ajax({
        url: '/grading/api/update-course-type/',
        method: 'POST',
        data: {
            course_name: selectedCourse,
            course_type: courseType,
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        success: function(response) {
            if (response.success) {
                alert('课程类型已保存：' + response.course.course_type_display);
            }
        }
    });
});
```

### 权限要求

- 需要登录
- 需要staff权限

### 自动效果

修改课程类型后：
- 立即生效
- 影响后续评分格式
- 无需刷新页面

### 使用场景

1. **初次设置**：新课程自动创建后，调整类型
2. **类型错误**：自动识别错误时，手动修正
3. **课程变更**：课程性质改变时，更新类型

### 注意事项

- 修改会影响所有使用该课程的评分
- 建议在学期开始时设置好
- 已评分的作业不会自动转换格式
