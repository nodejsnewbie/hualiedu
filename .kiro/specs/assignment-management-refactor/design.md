# Design Document

## Overview

本设计文档描述作业管理系统重构的技术方案。核心目标是将面向技术人员的"仓库管理"转变为面向教师的"作业管理"，同时实现远程 Git 仓库直接访问架构，消除本地同步需求。

**系统定位**: 作业评分系统本质上是一个统一的客户端，它同时支持 Git 仓库和文件系统两种存储方式，为教师提供统一的界面来批量处理和评分学生作业，而无需关心底层的存储技术细节。

### 设计原则

1. **用户友好性**: 隐藏技术细节，使用教育领域术语
2. **架构简化**: 远程直接访问，避免本地存储
3. **统一接口**: Git 和文件系统使用统一的抽象层
4. **性能优化**: 内存缓存机制，支持并发访问
5. **安全性**: 凭据加密存储，路径验证

### 关键设计决策

1. **远程优先架构**: 选择直接访问远程 Git 仓库而非本地克隆，理由是：
   - 消除本地存储空间占用
   - 避免同步延迟和冲突
   - 简化教师操作流程
   - 降低系统维护复杂度

2. **存储抽象层**: 使用适配器模式统一 Git 和文件系统访问，理由是：
   - 为未来扩展其他存储方式（如云存储）提供灵活性
   - 简化业务逻辑层代码
   - 便于单元测试和模拟

3. **内存缓存策略**: 使用 Django 缓存框架而非文件系统缓存，理由是：
   - 提高远程访问性能
   - 支持多进程共享缓存
   - 自动过期管理
   - 减少磁盘 I/O

4. **术语重构**: 将"仓库"改为"作业配置"，理由是：
   - 更符合教育场景的语言习惯
   - 降低教师用户的学习成本
   - 隐藏技术实现细节

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

### 5. StudentSubmissionService

```python
class StudentSubmissionService:
    """学生作业提交服务"""
    
    def get_student_courses(self, student: User) -> List[Course]:
        """获取学生所在班级的课程列表
        
        Args:
            student: 学生用户
            
        Returns:
            课程列表
        """
        # 学生课程列表隔离（Requirement 9.1）
        student_classes = student.profile.classes.all()
        return Course.objects.filter(
            class_obj__in=student_classes,
            tenant=student.profile.tenant
        ).distinct()
    
    def list_assignment_directories(
        self,
        assignment: Assignment,
        student: User
    ) -> Dict:
        """列出作业次数目录
        
        Args:
            assignment: 作业配置
            student: 学生用户
            
        Returns:
            包含目录列表和学生提交状态的字典
        """
        adapter = self._get_storage_adapter(assignment)
        
        try:
            # 获取作业目录列表
            entries = adapter.list_directory("")
            
            # 检查学生在每个目录中的提交状态
            directories = []
            for entry in entries:
                if entry["type"] == "dir":
                    has_submission = self._check_student_submission(
                        adapter, entry["name"], student
                    )
                    directories.append({
                        "name": entry["name"],
                        "has_submission": has_submission,
                        "submission_file": self._get_student_file(
                            adapter, entry["name"], student
                        ) if has_submission else None
                    })
            
            return {
                "success": True,
                "directories": directories
            }
        except Exception as e:
            logger.error(f"列出作业目录失败: {e}")
            return {
                "success": False,
                "error": "无法获取作业列表，请稍后重试"
            }
    
    def create_assignment_directory(
        self,
        assignment: Assignment,
        student: User
    ) -> Dict:
        """创建新的作业次数目录
        
        根据现有目录自动生成下一个作业次数名称。
        
        Args:
            assignment: 作业配置
            student: 学生用户
            
        Returns:
            包含新目录名称的字典
        """
        adapter = self._get_storage_adapter(assignment)
        
        try:
            # 获取现有作业次数
            entries = adapter.list_directory("")
            existing_numbers = self._extract_assignment_numbers(entries)
            
            # 生成新的作业次数名称（Requirement 9.3, 9.4）
            new_dir_name = PathValidator.generate_assignment_number_name(
                existing_numbers
            )
            
            # 创建目录（Requirement 4.4, 9.8）
            adapter.create_directory(new_dir_name)
            
            return {
                "success": True,
                "directory_name": new_dir_name
            }
        except Exception as e:
            logger.error(f"创建作业目录失败: {e}")
            return {
                "success": False,
                "error": "无法创建作业目录，请稍后重试"
            }
    
    def submit_assignment_file(
        self,
        assignment: Assignment,
        student: User,
        directory_name: str,
        file: UploadedFile
    ) -> Dict:
        """提交作业文件
        
        Args:
            assignment: 作业配置
            student: 学生用户
            directory_name: 作业次数目录名
            file: 上传的文件
            
        Returns:
            提交结果字典
        """
        # 验证文件格式（Requirement 9.6）
        if not self._validate_file_format(file.name):
            return {
                "success": False,
                "error": "不支持的文件格式，请上传 docx、pdf、zip、txt、jpg 或 png 文件"
            }
        
        # 验证文件大小
        if not self._validate_file_size(file.size):
            return {
                "success": False,
                "error": "文件大小超过限制（最大 10MB）"
            }
        
        # 处理文件名（Requirement 4.3, 9.5）
        processed_filename = self._process_filename(file.name, student)
        
        # 构建文件路径（Requirement 4.2）
        file_path = f"{directory_name}/{processed_filename}"
        
        adapter = self._get_storage_adapter(assignment)
        
        try:
            # 写入文件（Requirement 9.7 - 覆盖旧文件）
            adapter.write_file(file_path, file.read())
            
            return {
                "success": True,
                "filename": processed_filename,
                "message": "作业提交成功"
            }
        except Exception as e:
            logger.error(f"提交作业失败: {e}")
            return {
                "success": False,
                "error": "文件上传失败，请稍后重试"
            }
    
    def _validate_file_format(self, filename: str) -> bool:
        """验证文件格式"""
        allowed_extensions = {'.docx', '.pdf', '.zip', '.txt', '.jpg', '.png'}
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions
    
    def _validate_file_size(self, size: int) -> bool:
        """验证文件大小"""
        max_size = 10 * 1024 * 1024  # 10MB
        return size <= max_size
    
    def _process_filename(self, filename: str, student: User) -> str:
        """处理文件名，确保包含学生姓名
        
        如果文件名不包含学生姓名，自动添加前缀。
        """
        student_name = student.profile.name or student.username
        
        # 检查文件名是否已包含学生姓名（Requirement 4.8, 11）
        if student_name not in filename:
            # 添加学生姓名前缀（Requirement 9.5）
            name, ext = os.path.splitext(filename)
            filename = f"{student_name}-{name}{ext}"
        
        return filename
    
    def _check_student_submission(
        self,
        adapter: StorageAdapter,
        directory: str,
        student: User
    ) -> bool:
        """检查学生在指定目录中是否有提交"""
        student_name = student.profile.name or student.username
        
        try:
            entries = adapter.list_directory(directory)
            return any(student_name in entry["name"] for entry in entries)
        except:
            return False
    
    def _get_student_file(
        self,
        adapter: StorageAdapter,
        directory: str,
        student: User
    ) -> str:
        """获取学生在指定目录中的文件名"""
        student_name = student.profile.name or student.username
        
        try:
            entries = adapter.list_directory(directory)
            for entry in entries:
                if student_name in entry["name"]:
                    return entry["name"]
        except:
            pass
        
        return None
    
    def _extract_assignment_numbers(self, entries: List[Dict]) -> List[int]:
        """从目录列表中提取作业次数"""
        import re
        numbers = []
        
        for entry in entries:
            if entry["type"] == "dir":
                # 匹配 "第N次作业" 或 "第N次实验" 格式
                match = re.search(r'第(\d+|[一二三四五六七八九十]+)次', entry["name"])
                if match:
                    num_str = match.group(1)
                    # 转换中文数字或阿拉伯数字
                    try:
                        numbers.append(int(num_str))
                    except ValueError:
                        # 中文数字转换
                        num = self._chinese_to_number(num_str)
                        if num:
                            numbers.append(num)
        
        return numbers
    
    def _chinese_to_number(self, chinese: str) -> int:
        """中文数字转阿拉伯数字"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        if chinese in chinese_map:
            return chinese_map[chinese]
        elif chinese.startswith('十'):
            if len(chinese) == 1:
                return 10
            else:
                return 10 + chinese_map.get(chinese[1], 0)
        
        return None
    
    def _get_storage_adapter(self, assignment: Assignment) -> StorageAdapter:
        """获取存储适配器"""
        if assignment.storage_type == "git":
            return GitStorageAdapter(
                git_url=assignment.git_url,
                branch=assignment.git_branch,
                username=assignment.git_username,
                password=CredentialEncryption.decrypt(
                    assignment.git_password_encrypted
                )
            )
        else:
            return FileSystemStorageAdapter(assignment.base_path)
```

### 6. AssignmentManagementService

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
        """创建作业配置
        
        验证输入并创建作业配置记录。对于文件系统类型，自动生成并创建目录结构。
        
        Args:
            teacher: 创建作业的教师用户
            course: 关联的课程
            class_obj: 关联的班级
            name: 作业名称
            storage_type: 存储类型（git/filesystem）
            **kwargs: 其他配置参数（git_url, git_branch等）
            
        Returns:
            创建的 Assignment 对象
            
        Raises:
            ValidationError: 输入验证失败
            DuplicateAssignmentError: 作业配置已存在
        """
        
        # 验证输入
        self._validate_assignment_name(name)
        self._validate_course_class(course, class_obj)
        
        # 检查重复配置（Requirement 8.5）
        if self._check_duplicate_assignment(teacher, course, class_obj, name):
            raise DuplicateAssignmentError(
                f"作业配置已存在: {course.name}/{class_obj.name}/{name}",
                "该课程和班级已存在同名作业配置，请使用不同的名称"
            )
        
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
        
        # 如果是文件系统类型，创建基础目录（Requirement 4.1, 4.6）
        if storage_type == "filesystem":
            base_path = self._generate_base_path(course, class_obj)
            assignment.base_path = base_path
            assignment.save()
            
            adapter = self._get_storage_adapter(assignment)
            adapter.create_directory("")
        
        return assignment
    
    def list_assignments(
        self,
        teacher: User,
        course: Course = None,
        class_obj: Class = None
    ) -> QuerySet:
        """获取教师的作业配置列表
        
        只返回该教师创建的作业，支持按课程和班级筛选。
        
        Args:
            teacher: 教师用户
            course: 可选的课程筛选
            class_obj: 可选的班级筛选
            
        Returns:
            作业配置查询集
        """
        # 教师隔离（Requirement 5.1）
        queryset = Assignment.objects.filter(
            owner=teacher,
            tenant=teacher.profile.tenant,
            is_active=True
        ).select_related('course', 'class_obj')
        
        # 课程和班级筛选（Requirement 7.4）
        if course:
            queryset = queryset.filter(course=course)
        if class_obj:
            queryset = queryset.filter(class_obj=class_obj)
        
        return queryset
    
    def get_assignment_structure(self, assignment: Assignment, path: str = "") -> Dict:
        """获取作业目录结构
        
        直接从远程仓库或本地文件系统读取目录结构。
        
        Args:
            assignment: 作业配置对象
            path: 相对路径（默认为根目录）
            
        Returns:
            包含目录结构的字典，格式：
            {
                "success": True/False,
                "path": "路径",
                "entries": [{"name": "文件名", "type": "file/dir", ...}],
                "error": "错误消息"（仅在失败时）
            }
        """
        adapter = self._get_storage_adapter(assignment)
        
        try:
            entries = adapter.list_directory(path)
            return {
                "success": True,
                "path": path,
                "entries": entries
            }
        except RemoteAccessError as e:
            # 友好的错误消息（Requirement 3.5）
            logger.error(f"获取作业结构失败: {e.message}", extra={
                "assignment_id": assignment.id,
                "path": path,
                "user_message": e.user_message
            })
            return {
                "success": False,
                "error": e.user_message
            }
        except Exception as e:
            logger.error(f"获取作业结构失败: {e}", extra={
                "assignment_id": assignment.id,
                "path": path
            })
            return {
                "success": False,
                "error": "无法访问作业目录，请检查配置或稍后重试"
            }
    
    def update_assignment(
        self,
        assignment: Assignment,
        **kwargs
    ) -> Assignment:
        """更新作业配置
        
        更新作业配置，保护已提交的学生作业数据。
        
        Args:
            assignment: 要更新的作业配置
            **kwargs: 要更新的字段
            
        Returns:
            更新后的 Assignment 对象
        """
        # 保护关键字段，避免破坏已提交的作业（Requirement 5.4）
        protected_fields = {'course', 'class_obj', 'storage_type'}
        for field in protected_fields:
            if field in kwargs and getattr(assignment, field) != kwargs[field]:
                logger.warning(f"尝试修改受保护字段: {field}")
                # 可以选择抛出异常或忽略
        
        # 更新允许的字段
        for key, value in kwargs.items():
            if key not in protected_fields and hasattr(assignment, key):
                setattr(assignment, key, value)
        
        assignment.save()
        return assignment
    
    def delete_assignment(self, assignment: Assignment) -> Dict:
        """删除作业配置
        
        软删除作业配置，保留已提交的学生作业数据。
        
        Args:
            assignment: 要删除的作业配置
            
        Returns:
            包含删除结果的字典
        """
        # 检查是否有已提交的作业
        submission_count = assignment.submissions.count()
        
        # 软删除（Requirement 5.5）
        assignment.is_active = False
        assignment.save()
        
        return {
            "success": True,
            "message": f"作业配置已删除，保留了 {submission_count} 份学生作业"
        }
    
    def _check_duplicate_assignment(
        self,
        teacher: User,
        course: Course,
        class_obj: Class,
        name: str
    ) -> bool:
        """检查是否存在重复的作业配置"""
        return Assignment.objects.filter(
            owner=teacher,
            course=course,
            class_obj=class_obj,
            name=name,
            is_active=True
        ).exists()
    
    def _generate_base_path(self, course: Course, class_obj: Class) -> str:
        """生成文件系统基础路径
        
        格式: <课程名称>/<班级名称>/
        """
        course_name = PathValidator.sanitize_name(course.name)
        class_name = PathValidator.sanitize_name(class_obj.name)
        return f"{course_name}/{class_name}/"
    
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
    
    def _decrypt_password(self, encrypted: str) -> str:
        """解密密码"""
        return CredentialEncryption.decrypt(encrypted)
    
    def _validate_assignment_name(self, name: str):
        """验证作业名称
        
        Raises:
            ValidationError: 名称无效
        """
        if not name or not name.strip():
            raise ValidationError("作业名称不能为空", "请输入作业名称")
        
        # 验证不包含非法字符（Requirement 8.1）
        if not PathValidator.validate_name(name):
            raise ValidationError(
                f"作业名称包含非法字符: {name}",
                "作业名称不能包含特殊字符，如 / \\ : * ? \" < > |"
            )
    
    def _validate_course_class(self, course: Course, class_obj: Class):
        """验证课程和班级关联
        
        Raises:
            ValidationError: 课程和班级不匹配
        """
        if class_obj.course != course:
            raise ValidationError(
                f"班级 {class_obj.name} 不属于课程 {course.name}",
                "所选班级不属于该课程，请重新选择"
            )
```


## Data Models

### Course and Class Relationship

为支持 Requirement 7（为不同课程和班级创建独立作业配置），需要明确课程和班级的关系：

**关系模型**:
```
Course (课程)
  ├── name: 课程名称（如"数据结构"）
  ├── teacher: 授课教师
  └── classes: 关联的班级列表

Class (班级)
  ├── name: 班级名称（如"计算机1班"）
  ├── course: 所属课程
  └── students: 班级学生列表

Assignment (作业配置)
  ├── course: 关联课程
  ├── class_obj: 关联班级
  └── 约束: class_obj.course == course
```

**业务规则**:
1. 一个课程可以有多个班级（Requirement 7.3）
2. 一个班级只能属于一个课程
3. 作业配置必须同时关联课程和班级
4. 同一课程的不同班级有独立的作业目录（Requirement 7.3）

**目录隔离示例**:
```
数据结构/
  ├── 计算机1班/
  │   ├── 第一次作业/
  │   └── 第二次作业/
  └── 计算机2班/
      ├── 第一次作业/
      └── 第二次作业/
```

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
    def validate_name(cls, name: str) -> bool:
        """验证名称是否包含非法字符
        
        Args:
            name: 要验证的名称
            
        Returns:
            True 如果名称有效，False 如果包含非法字符
        """
        if not name or not name.strip():
            return False
        
        # 检查是否包含非法字符（Requirement 8.1, 8.2）
        return not any(char in name for char in cls.ILLEGAL_CHARS)
    
    @classmethod
    def validate_assignment_number_format(cls, name: str) -> bool:
        """验证作业次数格式
        
        Args:
            name: 作业次数名称
            
        Returns:
            True 如果格式正确
        """
        import re
        # 匹配 "第N次作业" 或 "第N次实验" 格式（Requirement 8.3）
        pattern = r'^第(\d+|[一二三四五六七八九十]+)次(作业|实验)$'
        return bool(re.match(pattern, name))
    
    @classmethod
    def validate_git_url(cls, url: str) -> bool:
        """验证 Git URL 格式
        
        Args:
            url: Git 仓库 URL
            
        Returns:
            True 如果格式正确
        """
        import re
        # 支持 http/https/git/ssh 协议（Requirement 8.4）
        patterns = [
            r'^https?://[^\s]+\.git$',  # https://github.com/user/repo.git
            r'^git@[^\s]+:[^\s]+\.git$',  # git@github.com:user/repo.git
            r'^git://[^\s]+\.git$',  # git://github.com/user/repo.git
            r'^ssh://[^\s]+\.git$',  # ssh://git@github.com/user/repo.git
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
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


## Documentation and Help

### 用户帮助文档

为满足 Requirement 1.4 和 6.3，系统需要提供面向教师的帮助文档：

**帮助文档内容**:

1. **作业管理快速入门**
   - 如何创建作业配置
   - Git 仓库方式 vs 文件上传方式的选择
   - 课程和班级的关联

2. **Git 仓库配置指南**
   - 如何获取 Git 仓库 URL
   - 分支选择说明
   - 认证凭据配置

3. **文件上传方式指南**
   - 目录结构说明
   - 学生提交流程
   - 文件命名规范

4. **常见问题解答**
   - 无法访问远程仓库怎么办
   - 如何修改作业配置
   - 如何查看学生提交情况

5. **故障排查**
   - 常见错误消息及解决方案
   - 联系技术支持的方式

**帮助文档位置**:
- 每个页面右上角的"帮助"链接
- 表单字段的提示图标
- 错误消息中的"了解更多"链接

**实现方式**:
```python
# 在模板中添加帮助链接
<a href="{% url 'grading:help' section='assignment-management' %}" 
   class="help-link" target="_blank">
    <i class="fa fa-question-circle"></i> 帮助
</a>

# 字段级帮助提示
<span class="help-tooltip" data-toggle="tooltip" 
      title="Git 仓库 URL 格式示例: https://github.com/user/repo.git">
    <i class="fa fa-info-circle"></i>
</span>
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

**动态表单行为** (Requirement 2.2):

当用户选择不同的提交方式时，表单动态显示相应的配置字段：

- **选择 "Git仓库"**: 显示 Git URL、分支、用户名、密码字段
- **选择 "文件上传"**: 隐藏 Git 配置，显示目录结构说明

**JavaScript 实现**:
```javascript
// 动态切换表单字段
document.querySelectorAll('input[name="storage_type"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const gitFields = document.getElementById('git-config-fields');
        const fsFields = document.getElementById('filesystem-config-fields');
        
        if (this.value === 'git') {
            gitFields.style.display = 'block';
            fsFields.style.display = 'none';
            // 设置 Git 字段为必填
            document.getElementById('id_git_url').required = true;
            document.getElementById('id_git_branch').required = true;
        } else {
            gitFields.style.display = 'none';
            fsFields.style.display = 'block';
            // 移除 Git 字段的必填要求
            document.getElementById('id_git_url').required = false;
            document.getElementById('id_git_branch').required = false;
        }
    });
});
```

**表单结构**:
```
┌─────────────────────────────────────────────────────────┐
│ 创建作业配置                                             │
├─────────────────────────────────────────────────────────┤
│ 基本信息                                                 │
│   作业名称: [________________] *必填                    │
│   课程:     [选择课程 ▼] *必填                          │
│   班级:     [选择班级 ▼] *必填                          │
│   描述:     [________________]                          │
│                                                          │
│ 提交方式 *必填                                           │
│   ○ Git仓库    ● 文件上传                               │
│                                                          │
│ [Git仓库配置] (当选择Git仓库时显示)                      │
│   仓库URL:  [https://github.com/...    ] *必填 ⓘ       │
│   分支:     [main                      ] *必填          │
│   用户名:   [________________] (可选)                   │
│   密码:     [****************] (可选)                   │
│   [测试连接] 按钮                                        │
│                                                          │
│ [文件上传配置] (当选择文件上传时显示)                     │
│   系统将自动创建目录结构:                                │
│   <课程名称>/<班级名称>/<作业次数>/                      │
│   例如: 数据结构/计算机1班/第一次作业/                   │
│                                                          │
│                              [取消] [保存]               │
└─────────────────────────────────────────────────────────┘

注: ⓘ 表示有帮助提示图标
```

**表单验证** (Requirement 2.5):

前端验证:
- 必填字段检查
- Git URL 格式验证
- 课程和班级关联验证

后端验证:
- 所有前端验证的重复检查
- 重复配置检查 (Requirement 8.5)
- Git 仓库可访问性验证 (可选)

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

**移除的元素** (Requirement 6.1, 6.4):
- "同步仓库"按钮
- "切换分支"选项
- "克隆"、"拉取"、"推送"等 Git 操作按钮
- 本地路径显示
- "最后同步时间"显示

**保留的元素**:
- 目录树浏览
- 文件内容查看
- 评分和评语输入
- 批量评分功能

**新增元素** (Requirement 6.5):
- 远程仓库实时状态指示器
- 数据来源标签（"来自 Git 仓库" 或 "来自本地文件"）
- 刷新按钮（清除缓存，重新获取远程数据）

**改进**:
- 添加加载指示器（远程读取时）
  ```html
  <div class="loading-indicator" style="display: none;">
      <i class="fa fa-spinner fa-spin"></i> 正在从远程仓库读取...
  </div>
  ```
- 显示文件来源（Git/本地）
  ```html
  <span class="badge badge-info">
      <i class="fa fa-git"></i> Git 仓库
  </span>
  ```
- 优化大文件预览
  - 文件大小超过 1MB 时显示下载链接而非直接预览
  - 支持常见格式的在线预览（PDF、图片、文本）
- 错误处理
  - 网络超时时显示友好提示
  - 提供重试按钮

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

## Requirements Coverage Summary

本设计文档完整覆盖了需求文档中的所有 10 个需求：

### Requirement 1: 术语重构
- ✅ 导航菜单和页面标题更新为"作业管理"
- ✅ 使用教育领域术语替代技术术语
- ✅ 提供面向教师的帮助文档

### Requirement 2: 简化配置流程
- ✅ 提供 Git 仓库和文件上传两种清晰选项
- ✅ 动态表单字段显示
- ✅ 完整的表单验证

### Requirement 3: 远程仓库直接访问
- ✅ 移除同步按钮和 Git 操作
- ✅ 使用 Git 远程命令（ls-tree, show）直接读取
- ✅ 友好的错误消息处理
- ✅ 无本地克隆约束

### Requirement 4: 自动目录结构
- ✅ 基于课程和班级生成目录路径
- ✅ 标准化的目录结构（<课程>/<班级>/<作业次数>/）
- ✅ 文件名包含学生姓名验证
- ✅ 自动创建目录
- ✅ 特殊字符处理

### Requirement 5: 作业配置管理
- ✅ 教师作业列表隔离
- ✅ 完整的 CRUD 操作
- ✅ 编辑时保护已提交数据
- ✅ 删除确认机制

### Requirement 6: 简洁界面
- ✅ 移除所有 Git 技术操作按钮
- ✅ 只显示必要信息
- ✅ 提供帮助链接
- ✅ 显示远程仓库实时状态

### Requirement 7: 多课程多班级支持
- ✅ 课程和班级选择器
- ✅ 独立的班级目录
- ✅ 按课程和班级筛选
- ✅ 清晰的课程区分

### Requirement 8: 输入验证
- ✅ 课程名称验证
- ✅ 班级名称验证
- ✅ 作业次数格式验证
- ✅ Git URL 格式验证
- ✅ 重复配置检查
- ✅ 清晰的错误消息

### Requirement 9: 学生作业提交
- ✅ 学生课程列表隔离
- ✅ 作业次数目录列表
- ✅ 一键创建新作业目录
- ✅ 自动命名规范
- ✅ 文件名自动处理
- ✅ 文件格式验证
- ✅ 文件覆盖规则

### Requirement 10: 远程访问架构
- ✅ Git 远程命令使用
- ✅ 内存缓存机制
- ✅ 缓存自动刷新
- ✅ 缓存共享
- ✅ 凭据安全存储

所有 30 个正确性属性都已在设计中体现，并将在实现阶段通过属性测试验证。

