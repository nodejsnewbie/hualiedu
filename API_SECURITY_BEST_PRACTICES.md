# API密钥安全最佳实践

## 🔐 概述

本文档描述了在Django项目中管理API密钥的最佳实践，特别是针对火山引擎API密钥的安全管理。

## 📋 最佳实践清单

### 1. **API密钥格式**

#### ✅ 推荐做法
```bash
# 火山引擎API密钥（UUID格式）
ARK_API_KEY=e7a701b6-3bc7-470a-8d1f-2a289dd015da
```

#### ❌ 不推荐做法
```bash
# 不必要的base64编码
ARK_API_KEY=base64_encoded_key_here
```

**原因**：
- 火山引擎API密钥本身就是UUID格式
- 不需要额外的编码/解码步骤
- 减少出错的可能性

### 2. **环境变量管理**

#### ✅ 推荐做法
```bash
# .env 文件
ARK_API_KEY=e7a701b6-3bc7-470a-8d1f-2a289dd015da
ARK_MODEL=deepseek-r1-250528
DEBUG=False
```

#### ❌ 不推荐做法
```python
# 硬编码在代码中
api_key = "e7a701b6-3bc7-470a-8d1f-2a289dd015da"
```

### 3. **文件权限保护**

#### ✅ 推荐做法
```bash
# 设置严格的文件权限
chmod 600 .env
chmod 600 .env.backup

# 验证权限
ls -la .env
# 应该显示: -rw-------@
```

#### ❌ 不推荐做法
```bash
# 过于宽松的权限
chmod 644 .env  # 其他用户可以读取
```

### 4. **代码中的处理**

#### ✅ 推荐做法
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
    logger.info("API密钥格式正确（UUID格式）")
else:
    logger.warning("API密钥格式可能不正确")
```

#### ❌ 不推荐做法
```python
# 尝试解码base64（不必要的复杂性）
try:
    decoded_key = base64.b64decode(api_key).decode("utf-8")
    api_key = decoded_key
except:
    pass
```

### 5. **版本控制安全**

#### ✅ 推荐做法
```bash
# .gitignore 文件
.env
.env.local
.env.production
*.key
*.pem
```

#### ❌ 不推荐做法
```bash
# 提交敏感文件到版本控制
git add .env
git commit -m "Add API keys"
```

### 6. **部署环境管理**

#### ✅ 推荐做法
```bash
# 生产环境使用环境变量
export ARK_API_KEY=your_production_api_key
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com
```

#### ❌ 不推荐做法
```bash
# 在代码中硬编码生产环境配置
DEBUG = True  # 生产环境应该是False
```

## 🔒 安全检查清单

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

## 🚨 安全警告

### 1. **永远不要**
- 在代码中硬编码API密钥
- 将API密钥提交到版本控制
- 在日志中记录完整的API密钥
- 使用过于宽松的文件权限

### 2. **定期检查**
- API密钥的有效性
- 文件权限设置
- 环境变量配置
- 安全日志记录

### 3. **应急响应**
- 立即撤销泄露的API密钥
- 生成新的API密钥
- 更新所有环境配置
- 检查是否有未授权的使用

## 📚 参考资料

- [Django安全文档](https://docs.djangoproject.com/en/stable/topics/security/)
- [火山引擎API文档](https://www.volcengine.com/docs/82379)
- [OWASP安全指南](https://owasp.org/www-project-top-ten/)

## 🔄 更新日志

- **2025-08-12**: 初始版本，包含基本的安全最佳实践
- **2025-08-12**: 添加文件权限和部署环境管理
- **2025-08-12**: 优化API密钥格式验证
