# 华立教育作业批改系统

## 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 2. 初始化数据
```bash
# 扫描课程
python manage.py scan_courses

# 导入作业批次
python manage.py import_homeworks

# 更新课程类型
python manage.py update_course_types
```

### 3. 启动服务
```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/grading/

## 核心功能

### 作业批改
- 支持Word文档在线预览和批改
- 自动识别作业类型（普通作业/实验报告）
- 实验报告评分写入表格，普通作业写入段落
- 支持AI辅助评分和教师评价
- 自动跳转到下一个文件

### 作业类型系统
- **自动判断**：数据库查询 → 课程类型 → 关键词匹配
- **手动设置**：点击作业批次标签可修改类型
- **差异化处理**：
  - 实验报告：评分写入"教师（签字）"表格
  - 普通作业：评分以段落形式添加

### 仓库管理
- Git仓库自动同步
- 支持多仓库管理
- 文件变更自动检测

## 管理命令

```bash
# 扫描课程目录
python manage.py scan_courses

# 导入作业批次
python manage.py import_homeworks

# 更新课程类型
python manage.py update_course_types
```

## 项目结构

```
huali-edu/
├── grading/              # 批改应用
│   ├── models.py        # 数据模型
│   ├── views.py         # 视图逻辑
│   ├── urls.py          # 路由配置
│   ├── management/      # 管理命令
│   └── static/          # 静态资源
├── templates/           # 模板文件
├── docs/               # 文档
└── manage.py           # Django管理脚本
```

## 数据库模型

### Course（课程）
- name: 课程名称
- course_type: 课程类型（theory/lab）

### Homework（作业批次）
- course: 关联课程
- folder_name: 作业文件夹名
- homework_type: 作业类型（normal/lab_report）

### Repository（仓库）
- name: 仓库名称
- path: 仓库路径
- remote_url: 远程地址

## 故障排除

### 作业类型判断不准确
```bash
# 重新导入作业批次
python manage.py import_homeworks
```

### 实验报告评分失败
- 检查文档是否包含"教师（签字）"表格
- 查看后台日志了解详细错误

### 文档损坏
```bash
# 在作业仓库目录下恢复文件
cd /path/to/homework/repo
git restore .
```

## 已知问题

详见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

## 团队协作

详见 [TEAM_COLLABORATION.md](TEAM_COLLABORATION.md)
