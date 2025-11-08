# 仓库同步功能

## 功能概述

自动同步 Git 仓库，支持本地修改的自动提交和推送。

## 功能特性

### 自动处理本地更改
- 检测未提交的更改
- 自动添加所有更改（`git add -A`）
- 自动提交（提交信息："自动提交：同步前保存本地更改"）
- 自动推送到远程仓库（`git push`）
- 拉取远程更新（`git pull`）

### 同步流程

1. **检查本地状态**
   ```bash
   git status --porcelain
   ```

2. **如果有未提交更改**
   ```bash
   git add -A
   git commit -m "自动提交：同步前保存本地更改"
   git push
   ```

3. **拉取远程更新**
   ```bash
   git pull
   ```

## 使用方法

### 在管理界面
1. 进入"仓库管理"页面
2. 找到需要同步的仓库
3. 点击"同步"按钮

### API调用
```python
POST /grading/sync-repository/
{
    "repository_id": 1
}
```

## 错误处理

- `git add` 失败：返回错误信息
- `git commit` 失败：返回错误信息
- `git push` 失败：返回错误信息
- `git pull` 失败：返回错误信息

## 日志记录

所有同步操作都会记录日志：
- 检测到未提交更改
- 自动提交成功
- 推送成功
- 同步成功/失败

## 相关代码

- `grading/utils.py` - `GitHandler.pull_repo()`
- `grading/views.py` - `sync_repository_view()`
