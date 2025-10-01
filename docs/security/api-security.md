# API安全最佳实践

## 概述

本文档描述了在Django项目中管理API密钥的最佳实践，特别是针对火山引擎API密钥的安全管理。

## API密钥管理

### 推荐格式
```bash
# 火山引擎API密钥（UUID格式）
ARK_API_KEY=e7a701b6-3bc7-470a-8d1f-2a289dd015da
ARK_MODEL=deepseek-r1-250528
```

### 环境变量管理
```bash
# .env 文件
ARK_API_KEY=your_api_key_here
ARK_MODEL=deepseek-r1-250528
DEBUG=False
SECRET_KEY=your_secret_key_here
```

### 代码中的处理
```python
import os
import re

# 从环境变量获取API密钥
api_key = os.environ.get("ARK_API_KEY")
if not api_key:
    logger.error("未设置ARK_API_KEY环境变量")
    return None, "API密钥未配置"

# 验证API密钥格式（UUID格式）
uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
if re.match(uuid_pattern, api_key):
    logger.info("API密钥格式正确")
else:
    logger.warning("API密钥格式可能不正确")
```

## 文件权限保护

### 设置严格权限
```bash
# 设置文件权限
chmod 600 .env
chmod 600 .env.backup

# 验证权限
ls -la .env
# 应该显示: -rw-------
```

### 版本控制安全
```bash
# .gitignore 文件
.env
.env.local
.env.production
*.key
*.pem
```

## 部署环境管理

### 生产环境配置
```bash
# 使用环境变量
export ARK_API_KEY=your_production_api_key
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com
```

### Docker部署
```dockerfile
# 在 Dockerfile 中设置环境变量
ENV DEBUG=False
ENV SECRET_KEY=your-production-secret-key
```

## 安全检查清单

### 开发环境
- [ ] API密钥存储在.env文件中
- [ ] .env文件权限设置为600
- [ ] .env文件已添加到.gitignore
- [ ] 代码中没有硬编码的API密钥
- [ ] 使用UUID格式的API密钥

### 生产环境
- [ ] 使用环境变量而不是.env文件
- [ ] DEBUG设置为False
- [ ] 使用HTTPS
- [ ] 配置适当的ALLOWED_HOSTS
- [ ] 定期轮换API密钥

### 监控和日志
- [ ] 记录API调用失败（不记录密钥）
- [ ] 监控API使用量
- [ ] 设置API调用频率限制
- [ ] 记录异常访问模式

## 安全警告

### 永远不要
- 在代码中硬编码API密钥
- 将API密钥提交到版本控制
- 在日志中记录完整的API密钥
- 使用过于宽松的文件权限

### 定期检查
- API密钥的有效性
- 文件权限设置
- 环境变量配置
- 安全日志记录

### 应急响应
- 立即撤销泄露的API密钥
- 生成新的API密钥
- 更新所有环境配置
- 检查是否有未授权的使用

## 故障排除

### API密钥问题
1. **401错误**: 检查API密钥格式和有效性
2. **网络错误**: 检查网络连接和代理设置
3. **权限错误**: 检查API密钥权限范围

### 环境配置问题
1. **变量未加载**: 检查.env文件格式
2. **路径问题**: 确保.env文件在正确位置
3. **权限问题**: 检查文件读取权限

## 获取API密钥

### 火山引擎API密钥
1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 创建或选择项目
3. 开通 Ark 服务
4. 在 API 密钥管理中创建密钥
5. 将密钥添加到环境变量中

### 密钥管理建议
- 为不同环境使用不同密钥
- 定期轮换密钥
- 限制密钥权限范围
- 监控密钥使用情况
