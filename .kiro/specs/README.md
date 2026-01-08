# 作业评分系统规范文档

> **完整的系统功能规范和实现计划**

## 概述

作业评分系统是一个基于 Django 的多租户教育平台，支持作业管理、智能评分和成绩管理。

## 功能模块

### 1. 核心评分系统
**目录**: `homework-grading-system/`

**功能**：
- 课程和班级管理
- 作业批次管理  
- 手动评分和 AI 评分
- 评价模板管理
- 批量操作
- 实验报告特殊处理

**状态**: ✅ 已完成

**文档**：
- [需求文档](homework-grading-system/requirements.md)
- [设计文档](homework-grading-system/design.md)
- [任务清单](homework-grading-system/tasks.md)

### 2. 作业管理（存储抽象层）
**目录**: `assignment-management-refactor/`

**功能**：
- Git 仓库方式支持
- 文件系统方式支持
- 统一的存储接口（StorageAdapter）
- 学生作业上传
- 远程仓库直接访问

**状态**: ✅ 已完成

**文档**：
- [需求文档](assignment-management-refactor/requirements.md)
- [设计文档](assignment-management-refactor/design.md)
- [任务清单](assignment-management-refactor/tasks.md)

### 3. 成绩登分册写入
**目录**: `grade-registry-writer/`

**功能**：
- 作业评分系统场景
- 工具箱模块场景
- 自动姓名匹配
- Excel 成绩写入
- 批量成绩录入

**状态**: ✅ 已完成

**文档**：
- [需求文档](grade-registry-writer/requirements.md)
- [设计文档](grade-registry-writer/design.md)
- [任务清单](grade-registry-writer/tasks.md)
- [功能说明](grade-registry-writer/README.md)

### 4. 学期自动管理
**目录**: `auto-semester-creation/`

**功能**：
- 学期模板系统
- 自动学期检测
- 学期状态管理
- 日期范围计算

**状态**: ✅ 已完成

**文档**：
- [需求文档](auto-semester-creation/requirements.md)
- [设计文档](auto-semester-creation/design.md)
- [任务清单](auto-semester-creation/tasks.md)

## 模块关系

```
作业评分系统
├── 核心评分系统 (homework-grading-system)
│   ├── 课程管理
│   ├── 班级管理
│   ├── 评分功能
│   └── 评价管理
│
├── 作业管理 (assignment-management-refactor)
│   ├── 存储抽象层
│   ├── Git 适配器
│   ├── 文件系统适配器
│   └── 学生上传
│
├── 成绩登分册 (grade-registry-writer)
│   ├── 成绩提取
│   ├── 姓名匹配
│   └── Excel 写入
│
└── 学期管理 (auto-semester-creation)
    ├── 学期模板
    ├── 自动检测
    └── 状态管理
```

## 技术栈

- **后端**: Django 4.2.20, Python 3.13
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI 服务**: Volcengine Ark SDK
- **文档处理**: python-docx, openpyxl, pandas
- **版本控制**: GitPython
- **测试**: Hypothesis (属性测试)

## 开发规范

所有模块遵循统一的开发规范：

- **需求格式**: EARS (Easy Approach to Requirements Syntax)
- **设计模式**: 服务层 + 适配器模式
- **测试策略**: 单元测试 + 属性测试 + 集成测试
- **代码规范**: Black + isort + flake8

详见：
- [技术栈](../steering/tech.md)
- [项目结构](../steering/structure.md)
- [Django 模式](../steering/django-patterns.md)
- [Python 规范](../steering/python-conventions.md)

## 相关文档

- [开发指南](../../docs/DEVELOPMENT.md)
- [用户手册](../../docs/USER_MANUAL.md)
- [快速入门](../../QUICKSTART_UV.md)

## 规范说明

### 需求文档 (requirements.md)
使用 EARS 格式编写，包含：
- 简介和术语表
- 用户故事
- 验收标准（WHEN/WHERE/THE System SHALL）

### 设计文档 (design.md)
包含：
- 架构设计
- 数据模型
- 接口设计
- 关键算法

### 任务清单 (tasks.md)
包含：
- 实现计划
- 任务状态（✓ 已完成 / 进行中 / 待完成）
- 需求追溯

## 维护指南

### 添加新功能

1. 在对应模块的 `requirements.md` 中添加需求
2. 在 `design.md` 中添加设计方案
3. 在 `tasks.md` 中添加实现任务
4. 实现功能并编写测试
5. 更新任务状态为 ✓

### 创建新模块

1. 在 `.kiro/specs/` 下创建新目录
2. 创建 `requirements.md`, `design.md`, `tasks.md`
3. 在本 README 中添加模块说明
4. 更新模块关系图

---

**创建日期**: 2024-12-02  
**最后更新**: 2024-12-02  
**维护者**: HualiEdu Team
