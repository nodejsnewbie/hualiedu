# Design Document

## Overview

本设计文档描述作业管理系统重构的技术方案。核心目标是将面向技术人员的"仓库管理"转变为面向教师的"作业管理"，同时实现远程 Git 仓库直接访问架构，消除本地同步需求。

### 设计原则

1. **用户友好性**: 隐藏技术细节，使用教育领域术语
2. **架构简化**: 远程直接访问，避免本地存储
3. **统一接口**: Git 和文件系统使用统一的抽象层
4. **性能优化**: 内存缓存机制，支持并发访问
5. **安全性**: 凭据加密存储，路径验证

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 作业管理界面  │  │ 作业提交界面  │  │ 评分界面      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         AssignmentManagementService                   │   │
│  │  - create_assignment()                                │   │
│  │  - list_assignments()                                 │   │
│  │  - get_assignment_structure()                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         StorageAbstractionLayer                       │   │
│  │  ┌─────────────────┐    ┌─────────────────┐          │   │
│  │  │ GitStorageAdapter│    │FileSystemAdapter│          │   │
│  │  └─────────────────┘    └─────────────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Assignment   │  │ Course       │  │ Class        │      │
│  │ Model        │  │ Model        │  │ Model        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌─────────────────┐              ┌─────────────────┐       │
│  │  Remote Git     │              │  Local File     │       │
│  │  Repository     │              │  System         │       │
│  └─────────────────┘              └─────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 核心架构变更

1. **远程 Git 访问**: 使用 GitPython 的远程命令（ls-remote, show）直接读取
2. **存储抽象层**: 统一 Git 和文件系统的访问接口
3. **内存缓存**: 使用 Django 缓存框架缓存远程数据
4. **术语重构**: Repository → Assignment，所有相关术语更新


## Components and Interfaces

### 1. Assignment Model (重构自 Repository)

```python
class Assignment(models.Model):
    """作业配置模型 - 重构自 Repository"""
    
    STORAGE_TYPE_CHOICES = [
        ("git", "Git仓库"),
        ("filesystem", "文件上传"),
    ]
    
    # 基本信息
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPE_CHOICES)
    
    # Git 存储配置
    git_url = models.URLField(blank=True, null=True)
    git_branch = models.CharField(max_length=100, default="main")
    git_username = models.CharField(max_length=100, blank=True)
    git_password_encrypted = models.CharField(max_length=500, blank=True)
    
    # 文件系统存储配置
    base_path = models.CharField(max_length=500, blank=True)
    
    # 元数据
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. StorageAdapter Interface

```python
class StorageAdapter(ABC):
    """存储适配器抽象接口"""
    
    @abstractmethod
    def list_directory(self, path: str) -> List[Dict]:
        """列出目录内容
        
        Returns:
            [{"name": "文件名", "type": "file|dir", "size": 123, ...}]
        """
        pass
    
    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """读取文件内容"""
        pass
    
    @abstractmethod
    def write_file(self, path: str, content: bytes) -> bool:
        """写入文件"""
        pass
    
    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        pass
```

### 3. GitStorageAdapter

```python
class GitStorageAdapter(StorageAdapter):
    """Git 远程仓库存储适配器"""
    
    def __init__(self, git_url: str, branch: str, username: str = "", password: str = ""):
        self.git_url = git_url
        self.branch = branch
        self.username = username
        self.password = password
        self.cache_timeout = 300  # 5分钟缓存
    
    def list_directory(self, path: str) -> List[Dict]:
        """使用 git ls-tree 列出远程目录"""
        cache_key = f"git_ls_{self._get_cache_key(path)}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # 执行 git ls-tree
        result = self._execute_git_command(
            ["ls-tree", "-l", f"{self.branch}:{path}"]
        )
        
        entries = self._parse_ls_tree_output(result)
        cache.set(cache_key, entries, self.cache_timeout)
        return entries
    
    def read_file(self, path: str) -> bytes:
        """使用 git show 读取远程文件"""
        cache_key = f"git_file_{self._get_cache_key(path)}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # 执行 git show
        content = self._execute_git_command(
            ["show", f"{self.branch}:{path}"]
        )
        
        cache.set(cache_key, content, self.cache_timeout)
        return content
```


### 4. FileSystemStorageAdapter

```python
class FileSystemStorageAdapter(StorageAdapter):
    """文件系统存储适配器"""
    
    def __init__(self, base_path: str):
        self.base_path = os.path.expanduser(base_path)
    
    def list_directory(self, path: str) -> List[Dict]:
        """列出本地目录"""
        full_path = self._get_full_path(path)
        self._validate_path(full_path)
        
        entries = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            entries.append({
                "name": item,
                "type": "dir" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                "modified": os.path.getmtime(item_path)
            })
        return entries
    
    def read_file(self, path: str) -> bytes:
        """读取本地文件"""
        full_path = self._get_full_path(path)
        self._validate_path(full_path)
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    def write_file(self, path: str, content: bytes) -> bool:
        """写入本地文件"""
        full_path = self._get_full_path(path)
        self._validate_path(full_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)
        return True
```

### 5. AssignmentManagementService

```python
class AssignmentManagementService:
    """作业管理服务"""
    
    def create_assignment(
        self,
        teacher: User,
        course: Course,
        class_obj: Class,
        name: str,
        storage_type: str,
        **kwargs
    ) -> Assignment:
        """创建作业配置"""
        
        # 验证输入
        self._validate_assignment_name(name)
        self._validate_course_class(course, class_obj)
        
        # 创建作业记录
        assignment = Assignment.objects.create(
            owner=teacher,
            tenant=teacher.profile.tenant,
            course=course,
            class_obj=class_obj,
            name=name,
            storage_type=storage_type,
            **kwargs
        )
        
        # 如果是文件系统类型，创建基础目录
        if storage_type == "filesystem":
            base_path = self._generate_base_path(course, class_obj)
            assignment.base_path = base_path
            assignment.save()
            
            adapter = self._get_storage_adapter(assignment)
            adapter.create_directory("")
        
        return assignment
    
    def get_assignment_structure(self, assignment: Assignment, path: str = "") -> Dict:
        """获取作业目录结构"""
        adapter = self._get_storage_adapter(assignment)
        
        try:
            entries = adapter.list_directory(path)
            return {
                "success": True,
                "path": path,
                "entries": entries
            }
        except Exception as e:
            logger.error(f"获取作业结构失败: {e}")
            return {
                "success": False,
                "error": "无法访问作业目录，请检查配置或稍后重试"
            }
    
    def _get_storage_adapter(self, assignment: Assignment) -> StorageAdapter:
        """获取存储适配器"""
        if assignment.storage_type == "git":
            return GitStorageAdapter(
                git_url=assignment.git_url,
                branch=assignment.git_branch,
                username=assignment.git_username,
                password=self._decrypt_password(assignment.git_password_encrypted)
            )
        else:
            return FileSystemStorageAdapter(assignment.base_path)
```


## Data Models

### Assignment Model 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| owner | ForeignKey(User) | 作业创建者（教师） |
| tenant | ForeignKey(Tenant) | 所属租户 |
| course | ForeignKey(Course) | 关联课程 |
| class_obj | ForeignKey(Class) | 关联班级 |
| name | CharField | 作业名称 |
| description | TextField | 作业描述 |
| storage_type | CharField | 存储类型（git/filesystem） |
| git_url | URLField | Git 仓库 URL |
| git_branch | CharField | Git 分支名 |
| git_username | CharField | Git 用户名 |
| git_password_encrypted | CharField | 加密的 Git 密码 |
| base_path | CharField | 文件系统基础路径 |
| is_active | BooleanField | 是否激活 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

### 目录结构规范

#### 文件系统存储

```
<base_path>/
  └── <课程名称>/
      └── <班级名称>/
          ├── 第一次作业/
          │   ├── 张三-作业1.docx
          │   ├── 李四-作业1.pdf
          │   └── 王五-作业1.zip
          ├── 第二次作业/
          │   ├── 张三-作业2.docx
          │   └── 李四-作业2.pdf
          └── 第三次作业/
              └── ...
```

#### Git 仓库存储

Git 仓库应遵循相同的目录结构，系统直接从远程读取：

```
<git_repo>/
  └── <课程名称>/
      └── <班级名称>/
          ├── 第一次作业/
          └── 第二次作业/
```

### 数据库迁移策略

由于不需要向后兼容，采用以下迁移策略：

1. **重命名模型**: Repository → Assignment
2. **重命名字段**: 
   - repo_type → storage_type
   - url → git_url
   - branch → git_branch
3. **新增字段**:
   - course (ForeignKey)
   - base_path (CharField)
4. **移除字段**:
   - last_sync (不再需要同步)
   - path (使用 base_path 替代)
   - allocated_space_mb (简化管理)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 表单验证完整性
*For any* 作业配置表单提交，所有必填字段都应该被验证，未填写的必填字段应该阻止提交
**Validates: Requirements 2.5**

### Property 2: 远程仓库目录读取
*For any* 有效的 Git 仓库 URL 和路径，系统应该能够直接从远程仓库读取目录结构而不创建本地克隆
**Validates: Requirements 3.2, 3.6**

### Property 3: 远程仓库文件读取
*For any* 远程仓库中存在的文件路径，系统应该能够直接获取文件内容
**Validates: Requirements 3.4**

### Property 4: 错误消息友好性
*For any* 远程仓库访问失败的情况，系统应该向用户显示友好的错误消息而不是技术堆栈信息
**Validates: Requirements 3.5**

### Property 5: 无本地克隆约束
*For any* Git 仓库访问操作，系统不应该在本地文件系统创建仓库克隆目录
**Validates: Requirements 3.6**

### Property 6: 目录路径生成规则
*For any* 课程名称和班级名称的组合，系统应该生成格式为 `<课程名称>/<班级名称>/` 的基础路径
**Validates: Requirements 4.1**

### Property 7: 文件存储路径规则
*For any* 学生作业提交，文件应该存储在 `<课程名称>/<班级名称>/<作业次数>/` 格式的路径中
**Validates: Requirements 4.2**

### Property 8: 文件名学生姓名验证
*For any* 学生上传的作业文件，文件名应该包含学生姓名，否则应该被拒绝
**Validates: Requirements 4.3**

### Property 9: 作业目录自动创建
*For any* 不存在的作业次数目录，学生提交时系统应该自动创建该目录
**Validates: Requirements 4.4, 4.6**

### Property 10: 路径特殊字符处理
*For any* 包含特殊字符的课程名、班级名或作业次数，系统应该进行转义或替换以确保文件系统兼容性
**Validates: Requirements 4.7**

### Property 11: 文件名唯一性
*For any* 两个不同学生上传的文件，即使基础文件名相同，也应该通过文件名中的学生姓名进行区分
**Validates: Requirements 4.8**

### Property 12: 教师作业列表隔离
*For any* 教师用户，作业管理页面应该只显示该教师创建的作业配置
**Validates: Requirements 5.1**

### Property 13: 编辑保留数据完整性
*For any* 作业配置的编辑操作，已提交的学生作业数据应该保持不变
**Validates: Requirements 5.4**

### Property 14: 班级目录隔离
*For any* 同一课程的不同班级，系统应该为每个班级维护独立的作业目录
**Validates: Requirements 7.3**

### Property 15: 课程名称验证
*For any* 课程名称输入，系统应该验证名称不为空且不包含文件系统非法字符（如 `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`）
**Validates: Requirements 8.1**

### Property 16: 班级名称验证
*For any* 班级名称输入，系统应该验证名称不为空且不包含文件系统非法字符
**Validates: Requirements 8.2**

### Property 17: 作业次数格式验证
*For any* 作业次数输入，系统应该验证格式符合 "第N次作业" 或 "第N次实验" 等规范格式
**Validates: Requirements 8.3**

### Property 18: Git URL 验证
*For any* Git URL 输入，系统应该验证 URL 格式正确（http/https/git/ssh 协议）
**Validates: Requirements 8.4**

### Property 19: 作业配置唯一性
*For any* 新的作业配置，系统应该检查是否存在相同课程、班级和名称的配置，存在则拒绝创建
**Validates: Requirements 8.5**

### Property 20: 学生课程列表隔离
*For any* 学生用户，作业提交页面应该只显示该学生所在班级的课程
**Validates: Requirements 9.1**

### Property 21: 作业次数自动递增
*For any* 现有的作业次数列表，点击"创建新作业"应该生成下一个序号的作业目录名（如已有"第一次作业"则生成"第二次作业"）
**Validates: Requirements 9.3**

### Property 22: 作业命名规范一致性
*For any* 自动生成的作业目录名称，应该遵循统一的命名规范（"第N次作业"格式）
**Validates: Requirements 9.4**

### Property 23: 文件名自动处理
*For any* 学生上传的文件，如果文件名不包含学生姓名，系统应该自动添加学生姓名前缀
**Validates: Requirements 9.5**

### Property 24: 文件格式验证
*For any* 上传的文件，系统应该验证文件格式是否在允许的列表中（docx, pdf, zip, txt, jpg, png 等）
**Validates: Requirements 9.6**

### Property 25: 文件覆盖规则
*For any* 学生重复上传相同作业次数的文件，新文件应该覆盖旧文件
**Validates: Requirements 9.7**

### Property 26: 远程访问技术约束
*For any* Git 仓库内容访问，系统应该使用 Git 远程命令（ls-tree, show）而不是本地克隆
**Validates: Requirements 10.1, 10.2, 10.3**

### Property 27: 内存缓存约束
*For any* 远程仓库数据缓存，应该使用内存缓存（Django cache）而不是文件系统缓存
**Validates: Requirements 10.4**

### Property 28: 缓存自动刷新
*For any* 过期的缓存数据，系统应该自动从远程仓库重新获取最新数据
**Validates: Requirements 10.5**

### Property 29: 缓存共享
*For any* 多个教师访问同一仓库的相同路径，应该共享缓存数据以提高性能
**Validates: Requirements 10.6**

### Property 30: 凭据安全存储
*For any* Git 仓库认证凭据，应该使用加密方式存储在数据库中，不应该以明文形式存储
**Validates: Requirements 10.7**


## Error Handling

### 错误分类

1. **用户输入错误**: 表单验证失败、非法字符、格式错误
2. **远程访问错误**: Git 仓库不可达、认证失败、网络超时
3. **文件系统错误**: 权限不足、磁盘空间不足、路径不存在
4. **业务逻辑错误**: 重复配置、数据不一致

### 错误处理策略

```python
class AssignmentError(Exception):
    """作业管理基础异常"""
    def __init__(self, message: str, user_message: str = None):
        self.message = message
        self.user_message = user_message or "操作失败，请稍后重试"
        super().__init__(self.message)

class ValidationError(AssignmentError):
    """验证错误"""
    pass

class StorageError(AssignmentError):
    """存储访问错误"""
    pass

class RemoteAccessError(StorageError):
    """远程仓库访问错误"""
    pass
```

### 错误消息映射

| 技术错误 | 用户友好消息 |
|---------|------------|
| `git: command not found` | Git 服务暂时不可用，请联系管理员 |
| `Authentication failed` | Git 仓库认证失败，请检查用户名和密码 |
| `Repository not found` | 找不到指定的 Git 仓库，请检查 URL |
| `Connection timeout` | 网络连接超时，请稍后重试 |
| `Permission denied` | 没有权限访问该目录，请联系管理员 |
| `Disk quota exceeded` | 存储空间不足，请清理旧文件或联系管理员 |
| `Invalid path` | 路径包含非法字符，请修改后重试 |

### 日志记录

```python
# 记录详细的技术错误信息
logger.error(
    f"Git 仓库访问失败: {technical_error}",
    extra={
        "user": request.user.username,
        "assignment_id": assignment.id,
        "git_url": assignment.git_url,
        "path": path
    }
)

# 向用户返回友好消息
return JsonResponse({
    "success": False,
    "error": "无法访问 Git 仓库，请检查配置或稍后重试"
})
```


## Testing Strategy

### 单元测试 (Unit Tests)

单元测试验证具体的功能实现和边界情况：

1. **模型测试**
   - Assignment 模型的字段验证
   - 路径生成方法的正确性
   - 加密/解密方法的可逆性

2. **适配器测试**
   - GitStorageAdapter 的命令构建
   - FileSystemStorageAdapter 的路径处理
   - 缓存键生成的唯一性

3. **服务测试**
   - AssignmentManagementService 的业务逻辑
   - 输入验证的边界情况
   - 错误处理的正确性

4. **视图测试**
   - 权限检查
   - 表单提交处理
   - JSON 响应格式

### 属性测试 (Property-Based Tests)

使用 Hypothesis 库进行属性测试，验证通用规则：

**测试框架**: Hypothesis 6.122.3 (已在 pyproject.toml 中配置)

**配置要求**:
- 每个属性测试至少运行 100 次迭代
- 使用 `@given` 装饰器定义输入生成策略
- 每个测试必须标注对应的设计文档属性编号

**示例**:

```python
from hypothesis import given, strategies as st
import hypothesis

# 配置最小迭代次数
hypothesis.settings.register_profile("ci", max_examples=100)
hypothesis.settings.load_profile("ci")

class TestAssignmentProperties:
    
    @given(
        course_name=st.text(min_size=1, max_size=50),
        class_name=st.text(min_size=1, max_size=50)
    )
    def test_property_6_path_generation(self, course_name, class_name):
        """**Feature: assignment-management-refactor, Property 6: 目录路径生成规则**
        
        For any 课程名称和班级名称的组合，系统应该生成格式为 
        `<课程名称>/<班级名称>/` 的基础路径
        """
        # 清理输入
        clean_course = sanitize_name(course_name)
        clean_class = sanitize_name(class_name)
        
        # 生成路径
        path = generate_base_path(clean_course, clean_class)
        
        # 验证格式
        assert path.endswith('/')
        assert clean_course in path
        assert clean_class in path
        parts = path.rstrip('/').split('/')
        assert len(parts) == 2
        assert parts[0] == clean_course
        assert parts[1] == clean_class
    
    @given(
        filename=st.text(min_size=1, max_size=100),
        student_name=st.text(min_size=1, max_size=20)
    )
    def test_property_23_filename_auto_processing(self, filename, student_name):
        """**Feature: assignment-management-refactor, Property 23: 文件名自动处理**
        
        For any 学生上传的文件，如果文件名不包含学生姓名，
        系统应该自动添加学生姓名前缀
        """
        # 处理文件名
        processed = process_student_filename(filename, student_name)
        
        # 验证包含学生姓名
        assert student_name in processed
        
        # 如果原文件名已包含学生姓名，不应该重复添加
        if student_name in filename:
            assert processed.count(student_name) == 1
    
    @given(
        path=st.text(min_size=1, max_size=200)
    )
    def test_property_15_course_name_validation(self, path):
        """**Feature: assignment-management-refactor, Property 15: 课程名称验证**
        
        For any 课程名称输入，系统应该验证名称不为空且不包含
        文件系统非法字符
        """
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        # 验证逻辑
        is_valid = validate_course_name(path)
        
        # 如果包含非法字符，应该验证失败
        has_illegal = any(char in path for char in illegal_chars)
        if has_illegal or not path.strip():
            assert not is_valid
        else:
            assert is_valid
```

### 集成测试

测试组件之间的交互：

1. **端到端流程测试**
   - 教师创建作业配置 → 学生提交作业 → 教师评分
   - Git 仓库配置 → 远程读取 → 缓存验证

2. **多租户隔离测试**
   - 不同租户的数据隔离
   - 不同教师的作业隔离

3. **并发访问测试**
   - 多个教师同时访问同一仓库
   - 缓存共享和一致性

### 测试数据生成

使用 Hypothesis 的策略生成测试数据：

```python
# 课程名称策略
course_names = st.text(
    alphabet=st.characters(blacklist_categories=('Cs',)),  # 排除控制字符
    min_size=1,
    max_size=50
).filter(lambda x: not any(c in x for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']))

# 文件名策略
filenames = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P')),
    min_size=1,
    max_size=100
).map(lambda x: x + st.sampled_from(['.docx', '.pdf', '.zip', '.txt']).example())

# Git URL 策略
git_urls = st.one_of(
    st.builds(
        lambda host, repo: f"https://github.com/{host}/{repo}.git",
        host=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=20),
        repo=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=30)
    ),
    st.builds(
        lambda host, repo: f"git@github.com:{host}/{repo}.git",
        host=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=20),
        repo=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=30)
    )
)
```


## Implementation Details

### 1. Git 远程访问实现

使用 GitPython 的底层命令接口：

```python
import subprocess
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class GitRemoteClient:
    """Git 远程仓库客户端"""
    
    def __init__(self, url: str, branch: str, username: str = "", password: str = ""):
        self.url = url
        self.branch = branch
        self.username = username
        self.password = password
        self._auth_url = self._build_auth_url()
    
    def _build_auth_url(self) -> str:
        """构建带认证的 URL"""
        if not self.username or not self.password:
            return self.url
        
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.url)
        
        if parsed.scheme in ['http', 'https']:
            netloc = f"{self.username}:{self.password}@{parsed.netloc}"
            return urlunparse((
                parsed.scheme, netloc, parsed.path,
                parsed.params, parsed.query, parsed.fragment
            ))
        return self.url
    
    def ls_tree(self, path: str = "") -> List[Dict]:
        """列出远程目录内容"""
        ref = f"{self.branch}:{path}" if path else self.branch
        
        try:
            result = subprocess.run(
                ["git", "ls-tree", "-l", ref],
                env={"GIT_TERMINAL_PROMPT": "0"},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RemoteAccessError(
                    f"Git ls-tree failed: {result.stderr}",
                    "无法读取远程目录，请检查路径是否正确"
                )
            
            return self._parse_ls_tree(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise RemoteAccessError(
                "Git command timeout",
                "远程仓库访问超时，请稍后重试"
            )
        except FileNotFoundError:
            raise RemoteAccessError(
                "Git command not found",
                "Git 服务暂时不可用，请联系管理员"
            )
    
    def show_file(self, path: str) -> bytes:
        """读取远程文件内容"""
        ref = f"{self.branch}:{path}"
        
        try:
            result = subprocess.run(
                ["git", "show", ref],
                env={"GIT_TERMINAL_PROMPT": "0"},
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RemoteAccessError(
                    f"Git show failed: {result.stderr}",
                    "无法读取文件内容，请检查文件路径"
                )
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise RemoteAccessError(
                "Git command timeout",
                "文件读取超时，请稍后重试"
            )
    
    def _parse_ls_tree(self, output: str) -> List[Dict]:
        """解析 ls-tree 输出"""
        entries = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            # 格式: <mode> <type> <hash> <size> <name>
            parts = line.split(maxsplit=4)
            if len(parts) < 5:
                continue
            
            mode, obj_type, obj_hash, size, name = parts
            
            entries.append({
                "name": name,
                "type": "dir" if obj_type == "tree" else "file",
                "size": int(size) if size != "-" else 0,
                "mode": mode,
                "hash": obj_hash
            })
        
        return entries
```

### 2. 缓存策略

使用 Django 缓存框架：

```python
from django.core.cache import cache
from django.conf import settings
import hashlib

class CacheManager:
    """缓存管理器"""
    
    CACHE_PREFIX = "assignment"
    DEFAULT_TIMEOUT = 300  # 5分钟
    
    @classmethod
    def get_cache_key(cls, assignment_id: int, path: str, operation: str) -> str:
        """生成缓存键"""
        key_data = f"{assignment_id}:{path}:{operation}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{cls.CACHE_PREFIX}:{key_hash}"
    
    @classmethod
    def get_directory_listing(cls, assignment_id: int, path: str):
        """获取目录列表缓存"""
        key = cls.get_cache_key(assignment_id, path, "ls")
        return cache.get(key)
    
    @classmethod
    def set_directory_listing(cls, assignment_id: int, path: str, data: List[Dict]):
        """设置目录列表缓存"""
        key = cls.get_cache_key(assignment_id, path, "ls")
        cache.set(key, data, cls.DEFAULT_TIMEOUT)
    
    @classmethod
    def get_file_content(cls, assignment_id: int, path: str):
        """获取文件内容缓存"""
        key = cls.get_cache_key(assignment_id, path, "file")
        return cache.get(key)
    
    @classmethod
    def set_file_content(cls, assignment_id: int, path: str, content: bytes):
        """设置文件内容缓存"""
        key = cls.get_cache_key(assignment_id, path, "file")
        # 文件内容缓存时间更长
        cache.set(key, content, cls.DEFAULT_TIMEOUT * 2)
    
    @classmethod
    def invalidate_assignment(cls, assignment_id: int):
        """清除作业相关的所有缓存"""
        # Django 缓存不支持按前缀删除，需要记录所有键
        # 或使用 Redis 的 SCAN 命令
        pattern = f"{cls.CACHE_PREFIX}:*"
        # 实现取决于缓存后端
        pass
```

### 3. 路径清理和验证

```python
import re
import os

class PathValidator:
    """路径验证器"""
    
    # 文件系统非法字符
    ILLEGAL_CHARS = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    # 替换映射
    CHAR_REPLACEMENTS = {
        '/': '-',
        '\\': '-',
        ':': '-',
        '*': '',
        '?': '',
        '"': '',
        '<': '',
        '>': '',
        '|': '-'
    }
    
    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """清理名称中的非法字符"""
        if not name:
            raise ValidationError("名称不能为空", "请输入有效的名称")
        
        # 去除首尾空格
        name = name.strip()
        
        # 替换非法字符
        for char, replacement in cls.CHAR_REPLACEMENTS.items():
            name = name.replace(char, replacement)
        
        # 去除连续的连字符
        name = re.sub(r'-+', '-', name)
        
        # 去除首尾连字符
        name = name.strip('-')
        
        if not name:
            raise ValidationError(
                "清理后的名称为空",
                "名称包含过多特殊字符，请使用字母和数字"
            )
        
        return name
    
    @classmethod
    def validate_path(cls, path: str, base_path: str) -> bool:
        """验证路径安全性"""
        # 解析为绝对路径
        abs_path = os.path.abspath(os.path.join(base_path, path))
        abs_base = os.path.abspath(base_path)
        
        # 确保路径在基础目录内
        if not abs_path.startswith(abs_base):
            raise ValidationError(
                f"Path traversal attempt: {path}",
                "无效的路径"
            )
        
        return True
    
    @classmethod
    def generate_assignment_number_name(cls, existing_numbers: List[int]) -> str:
        """生成作业次数名称"""
        if not existing_numbers:
            next_number = 1
        else:
            next_number = max(existing_numbers) + 1
        
        return f"第{cls._number_to_chinese(next_number)}次作业"
    
    @classmethod
    def _number_to_chinese(cls, num: int) -> str:
        """数字转中文"""
        chinese_nums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        
        if num <= 10:
            return chinese_nums[num]
        elif num < 20:
            return f"十{chinese_nums[num - 10]}"
        else:
            return str(num)  # 大于20使用阿拉伯数字
```

### 4. 凭据加密

```python
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class CredentialEncryption:
    """凭据加密工具"""
    
    @classmethod
    def _get_key(cls) -> bytes:
        """获取加密密钥"""
        # 从 settings 获取密钥，或使用 SECRET_KEY 派生
        key = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', None)
        if not key:
            # 从 SECRET_KEY 派生
            from django.utils.encoding import force_bytes
            import hashlib
            key = base64.urlsafe_b64encode(
                hashlib.sha256(force_bytes(settings.SECRET_KEY)).digest()
            )
        return key
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """加密"""
        if not plaintext:
            return ""
        
        f = Fernet(cls._get_key())
        encrypted = f.encrypt(plaintext.encode())
        return encrypted.decode()
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """解密"""
        if not ciphertext:
            return ""
        
        f = Fernet(cls._get_key())
        decrypted = f.decrypt(ciphertext.encode())
        return decrypted.decode()
```


## UI/UX Changes

### 术语映射

| 旧术语 | 新术语 |
|--------|--------|
| 仓库管理 | 作业管理 |
| 仓库 | 作业配置 |
| 仓库类型 | 提交方式 |
| 同步 | (移除) |
| 克隆 | (移除) |
| 拉取 | (移除) |
| 推送 | (移除) |
| Git仓库 | Git仓库 (保留) |
| 文件系统 | 文件上传 |

### 界面改进

#### 1. 作业管理列表页

**移除的元素**:
- "同步"按钮
- "克隆"按钮
- "最后同步时间"列
- Git 分支切换下拉框

**新增的元素**:
- 课程和班级筛选器
- 提交方式标签（Git/文件上传）
- 作业状态指示器

**布局**:
```
┌─────────────────────────────────────────────────────────┐
│ 作业管理                                    [+ 创建作业]  │
├─────────────────────────────────────────────────────────┤
│ 筛选: [课程 ▼] [班级 ▼] [提交方式 ▼]                    │
├─────────────────────────────────────────────────────────┤
│ 作业名称    课程      班级      提交方式    创建时间      │
│ 数据结构1   数据结构  计算机1班  文件上传   2025-01-15   │
│ 算法作业    算法      计算机2班  Git仓库    2025-01-10   │
└─────────────────────────────────────────────────────────┘
```

#### 2. 创建/编辑作业配置页

**表单结构**:
```
┌─────────────────────────────────────────────────────────┐
│ 创建作业配置                                             │
├─────────────────────────────────────────────────────────┤
│ 基本信息                                                 │
│   作业名称: [________________]                          │
│   课程:     [选择课程 ▼]                                │
│   班级:     [选择班级 ▼]                                │
│   描述:     [________________]                          │
│                                                          │
│ 提交方式                                                 │
│   ○ Git仓库    ● 文件上传                               │
│                                                          │
│ [Git仓库配置] (当选择Git仓库时显示)                      │
│   仓库URL:  [https://github.com/...    ]               │
│   分支:     [main                      ]               │
│   用户名:   [________________]                          │
│   密码:     [****************]                          │
│                                                          │
│ [文件上传配置] (当选择文件上传时显示)                     │
│   系统将自动创建目录结构:                                │
│   <课程名称>/<班级名称>/<作业次数>/                      │
│                                                          │
│                              [取消] [保存]               │
└─────────────────────────────────────────────────────────┘
```

#### 3. 学生作业提交页

```
┌─────────────────────────────────────────────────────────┐
│ 作业提交                                                 │
├─────────────────────────────────────────────────────────┤
│ 选择课程: [数据结构 ▼]                                  │
│                                                          │
│ 现有作业:                                                │
│   📁 第一次作业  (已提交: 数据结构-张三.docx)            │
│   📁 第二次作业  (未提交)                                │
│                                                          │
│   [+ 创建新作业]                                         │
│                                                          │
│ 上传文件:                                                │
│   [选择文件] 或 拖拽文件到此处                           │
│                                                          │
│   支持格式: docx, pdf, zip, txt, jpg, png               │
│   文件名将自动添加您的姓名                               │
│                                                          │
│                              [取消] [提交]               │
└─────────────────────────────────────────────────────────┘
```

#### 4. 评分界面

**移除的元素**:
- "同步仓库"按钮
- "切换分支"选项
- 本地路径显示

**保留的元素**:
- 目录树浏览
- 文件内容查看
- 评分和评语输入

**改进**:
- 添加加载指示器（远程读取时）
- 显示文件来源（Git/本地）
- 优化大文件预览

### 错误提示改进

**旧提示**: `git: 'ls-tree' failed with exit code 128`

**新提示**: `无法访问远程仓库，请检查网络连接或联系管理员`

**旧提示**: `PermissionError: [Errno 13] Permission denied: '/path/to/file'`

**新提示**: `没有权限访问该文件，请联系管理员`


## Performance Considerations

### 1. 缓存策略

**缓存层级**:
- L1: 内存缓存（Django cache）- 5分钟
- L2: 浏览器缓存（静态资源）- 1小时

**缓存内容**:
- 远程目录列表
- 远程文件内容（小于 1MB）
- 课程和班级列表

**缓存失效**:
- 时间过期自动失效
- 手动刷新按钮触发失效
- 配置更新时清除相关缓存

### 2. 远程访问优化

**批量操作**:
```python
# 不好的做法：逐个文件读取
for file in files:
    content = adapter.read_file(file.path)  # N次远程调用

# 好的做法：批量读取
contents = adapter.read_files_batch([f.path for f in files])  # 1次远程调用
```

**并发控制**:
- 使用连接池限制并发 Git 命令数量
- 实现请求队列避免过载
- 设置超时时间防止长时间阻塞

### 3. 数据库优化

**查询优化**:
```python
# 使用 select_related 减少查询
assignments = Assignment.objects.select_related(
    'owner', 'tenant', 'course', 'class_obj'
).filter(owner=teacher)

# 使用 prefetch_related 优化反向关系
courses = Course.objects.prefetch_related('assignments').filter(teacher=teacher)
```

**索引**:
```python
class Assignment(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['course', 'class_obj']),
            models.Index(fields=['storage_type', 'is_active']),
        ]
```

### 4. 前端优化

**懒加载**:
- 目录树按需展开
- 文件内容按需加载
- 分页显示作业列表

**防抖和节流**:
```javascript
// 搜索输入防抖
const debouncedSearch = debounce((query) => {
    searchAssignments(query);
}, 300);

// 滚动加载节流
const throttledScroll = throttle(() => {
    loadMoreAssignments();
}, 1000);
```

## Security Considerations

### 1. 认证和授权

**权限检查**:
```python
@login_required
@require_teacher
def assignment_management(request):
    # 只能访问自己创建的作业
    assignments = Assignment.objects.filter(
        owner=request.user,
        tenant=request.user.profile.tenant
    )
```

**多租户隔离**:
```python
# 所有查询必须包含 tenant 过滤
Assignment.objects.filter(
    tenant=request.user.profile.tenant,
    ...
)
```

### 2. 输入验证

**路径遍历防护**:
```python
def validate_path(path: str, base_path: str):
    abs_path = os.path.abspath(os.path.join(base_path, path))
    abs_base = os.path.abspath(base_path)
    
    if not abs_path.startswith(abs_base):
        raise SecurityError("Path traversal detected")
```

**SQL 注入防护**:
- 使用 Django ORM 参数化查询
- 避免原始 SQL 拼接

**XSS 防护**:
- 模板自动转义
- 用户输入清理

### 3. 凭据安全

**存储**:
- Git 密码使用 Fernet 加密
- 加密密钥从环境变量读取
- 不在日志中记录敏感信息

**传输**:
- HTTPS 强制加密
- 表单使用 CSRF 保护

**访问控制**:
- 只有作业所有者可以查看凭据
- 管理员不能直接查看密码

### 4. 文件安全

**文件类型验证**:
```python
ALLOWED_EXTENSIONS = {'.docx', '.pdf', '.zip', '.txt', '.jpg', '.png'}

def validate_file_extension(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS
```

**文件大小限制**:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file_size(file_size: int) -> bool:
    return file_size <= MAX_FILE_SIZE
```

**病毒扫描**:
- 集成 ClamAV 或类似工具
- 异步扫描上传文件
- 隔离可疑文件

## Migration Strategy

### 数据迁移步骤

由于不需要向后兼容，采用直接重构策略：

1. **创建新模型**
   ```bash
   uv run python manage.py makemigrations
   ```

2. **应用迁移**
   ```bash
   uv run python manage.py migrate
   ```

3. **更新视图和模板**
   - 重命名 URL 路由
   - 更新模板文件
   - 修改 JavaScript 代码

4. **更新管理界面**
   - 修改 admin.py
   - 更新列表显示
   - 调整表单字段

5. **清理旧代码**
   - 删除同步相关代码
   - 移除本地克隆逻辑
   - 清理未使用的工具函数

### 部署检查清单

- [ ] 数据库迁移已应用
- [ ] 静态文件已收集
- [ ] 缓存配置已更新
- [ ] 环境变量已设置（加密密钥）
- [ ] Git 命令可用性已验证
- [ ] 权限配置已检查
- [ ] 日志记录已配置
- [ ] 错误监控已启用
- [ ] 性能监控已启用
- [ ] 备份策略已确认

