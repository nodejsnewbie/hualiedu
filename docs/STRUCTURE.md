# 文档结构说明

## 📁 目录结构

```
docs/
├── README.md                    # 文档索引和导航
├── STRUCTURE.md                 # 文档结构说明（本文件）
├── environment.md               # 环境配置指南
├── testing.md                   # 测试指南
├── optimization.md              # 项目优化记录
├── project_requirements.md      # 项目需求分析
├── project_rules.md            # 项目开发规范
├── features/                   # 功能特性文档
│   ├── ai-scoring.md           # AI评分功能
│   ├── multi-tenant.md         # 多租户系统
│   └── calendar.md             # 校历功能
├── security/                   # 安全相关文档
│   └── api-security.md         # API安全最佳实践
└── reports/                    # 报告和记录
    └── BATCH_SCORING_REPORT.md # 批量评分执行报告
```

## 📋 文档分类

### 🚀 快速开始类
- `environment.md` - 环境配置，新用户必读
- `testing.md` - 测试框架，开发者必读

### 🔧 功能特性类
- `features/ai-scoring.md` - AI评分功能详细说明
- `features/multi-tenant.md` - 多租户系统架构
- `features/calendar.md` - 校历和课程管理

### 🔒 安全指南类
- `security/api-security.md` - API密钥管理和安全配置

### 📊 项目管理类
- `project_requirements.md` - 需求分析和技术栈
- `project_rules.md` - 开发规范和代码标准
- `optimization.md` - 技术改进和优化建议

### 📈 报告记录类
- `reports/BATCH_SCORING_REPORT.md` - 功能执行报告

## 🎯 文档使用指南

### 按角色阅读

#### 新用户
1. [环境配置指南](environment.md)
2. [AI评分功能](features/ai-scoring.md)
3. [校历功能](features/calendar.md)

#### 开发者
1. [项目开发规范](project_rules.md)
2. [测试指南](testing.md)
3. [项目优化记录](optimization.md)

#### 系统管理员
1. [API安全最佳实践](security/api-security.md)
2. [多租户系统](features/multi-tenant.md)
3. [环境配置指南](environment.md)

#### 项目经理
1. [项目需求分析](project_requirements.md)
2. [项目开发规范](project_rules.md)
3. [报告和记录](reports/)

### 按功能阅读

#### 评分系统
- [AI评分功能](features/ai-scoring.md)
- [批量评分报告](reports/BATCH_SCORING_REPORT.md)

#### 系统架构
- [多租户系统](features/multi-tenant.md)
- [项目需求分析](project_requirements.md)

#### 部署运维
- [环境配置指南](environment.md)
- [API安全最佳实践](security/api-security.md)

## 📝 文档维护规范

### 文档命名
- 使用小写字母和连字符
- 功能文档放在对应子目录
- 保持文件名简洁明了

### 内容组织
- 每个文档包含目录结构
- 使用清晰的标题层级
- 提供代码示例和配置样例
- 包含故障排除部分

### 更新维护
- 功能变更时及时更新文档
- 保持文档与代码同步
- 定期检查链接有效性
- 记录重要的变更历史

## 🔗 文档关联

### 相互引用
- 文档间使用相对路径链接
- 主README指向详细文档
- 功能文档间相互引用

### 外部链接
- 官方文档和API参考
- 第三方服务文档
- 相关技术资料

## 📊 文档统计

- 总文档数量: 12个
- 功能文档: 3个
- 配置文档: 2个
- 安全文档: 1个
- 管理文档: 3个
- 报告文档: 1个
- 索引文档: 2个

## 🎉 整理成果

### 优化前问题
- 文档分散在根目录和docs目录
- 内容重复，缺乏统一结构
- 文档间缺乏关联和导航
- 功能文档混杂在一起

### 优化后改进
- ✅ 统一的目录结构
- ✅ 按功能分类组织
- ✅ 清晰的文档导航
- ✅ 消除重复内容
- ✅ 完善的索引系统
- ✅ 规范的命名约定
