# 项目开发规范

## 前端资源使用规范

### 1. 禁止使用CDN
- 所有前端资源（如JavaScript、CSS、字体文件等）必须使用本地文件
- 禁止使用任何CDN链接加载资源
- 所有第三方库必须下载到本地并放置在 `static/vendor/` 目录下
- 使用Django的 `{% static %}` 标签引用静态资源

### 2. 静态资源组织
- 第三方库文件应放置在 `static/vendor/` 目录下
- 项目自定义的静态资源应放置在 `static/` 目录下的相应子目录中
- 保持目录结构清晰，便于维护

### 3. 资源引用方式
```html
<!-- 正确的方式 -->
<link href="{% static 'grading/vendor/bootstrap/bootstrap.min.css' %}" rel="stylesheet">
<script src="{% static 'grading/vendor/jquery/jquery.min.js' %}"></script>

<!-- 错误的方式 -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
```

### 4. 资源更新
- 定期检查第三方库的更新
- 更新时下载新版本到本地，替换旧文件
- 确保更新后的资源与项目兼容

## 其他开发规范

### 1. 代码风格
- 遵循PEP 8规范
- 使用4个空格缩进
- 每行代码不超过79个字符
- 使用有意义的变量名和函数名

### 2. 文档规范
- 为所有函数和类编写文档字符串
- 保持README文件更新
- 记录重要的配置变更

### 3. 测试规范
- 为所有新功能编写单元测试
- 测试覆盖率应保持在80%以上
- 在提交代码前运行所有测试

### 4. 版本控制
- 使用有意义的提交信息
- 遵循语义化版本控制
- 定期创建版本标签

### 5. 安全规范
- 避免在代码中硬编码敏感信息
- 使用环境变量存储配置信息
- 定期更新依赖包以修复安全漏洞 