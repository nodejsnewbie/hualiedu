# 环境配置说明

本项目配置为自动运行在 `py313` conda环境中。以下是几种自动环境切换的方法：

## 方法1: 使用direnv（推荐）

1. 安装direnv：
   ```bash
   # macOS
   brew install direnv

   # 添加到shell配置文件 (~/.zshrc 或 ~/.bashrc)
   eval "$(direnv hook zsh)"  # 对于zsh
   # 或
   eval "$(direnv hook bash)" # 对于bash
   ```

2. 在项目目录中允许direnv：
   ```bash
   direnv allow
   ```

3. 每次进入项目目录时会自动激活py313环境

## 方法2: 使用autoenv

1. 安装autoenv：
   ```bash
   # macOS
   brew install autoenv

   # 添加到shell配置文件
   source $(brew --prefix autoenv)/activate.sh
   ```

2. 每次进入项目目录时会自动激活py313环境

## 方法3: 使用conda-project

1. 安装conda-project：
   ```bash
   conda install conda-project
   ```

2. 使用项目命令：
   ```bash
   conda project run        # 运行默认服务
   conda project run test   # 运行测试
   ```

## 方法4: VS Code自动配置

VS Code已配置为自动使用py313环境：
- 打开终端时自动激活py313环境
- Python解释器指向py313环境
- 测试和调试使用py313环境

## 手动激活（备用方案）

如果自动方法不工作，可以手动激活：

```bash
# 创建环境（如果不存在）
conda env create -f environment.yml

# 激活环境
conda activate py313

# 验证环境
python --version  # 应该显示Python 3.13.x
```

## 验证环境

运行以下命令验证环境配置正确：

```bash
# 完整项目状态检查
python check_project_status.py

# 检查环境状态
make check-env

# 测试学期管理器
make test-semester

# 运行所有测试
make test
```

## 便捷命令

项目提供了多种便捷的命令方式：

### 1. Makefile命令（推荐）
```bash
make help          # 查看所有可用命令
make runserver     # 启动开发服务器
make test          # 运行测试
make migrate       # 数据库迁移
make shell         # Django shell
```

### 2. 包装器脚本
```bash
# Django管理命令
python manage_py313.py runserver
python manage_py313.py test
python manage_py313.py migrate

# 测试命令
python test_py313.py test_semester_manager_simple.py
python test_py313.py grading.tests.test_semester_manager

# 通用命令包装器
python run_in_env.py python --version
python run_in_env.py python manage.py shell
```

### 3. VS Code集成
- 使用 Ctrl+Shift+P 打开命令面板
- 搜索 "Tasks: Run Task"
- 选择预配置的任务（如 "Django: Run Server"）

## 环境变量

项目自动设置以下环境变量：
- `DJANGO_SETTINGS_MODULE=hualiEdu.settings`
- `PYTHONPATH` 包含项目根目录

## 故障排除

1. **conda命令未找到**：
   - 确保已安装Anaconda或Miniconda
   - 运行 `conda init` 初始化shell

2. **py313环境不存在**：
   - 运行 `conda env create -f environment.yml`

3. **VS Code终端未激活环境**：
   - 重启VS Code
   - 检查 `.vscode/settings.json` 配置

4. **direnv未工作**：
   - 确保已运行 `direnv allow`
   - 检查shell配置中是否添加了direnv hook
