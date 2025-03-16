from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Assignment, Submission, Repository, GlobalConfig
import os
import git
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
import tempfile
from django import forms
from django.core.files.storage import FileSystemStorage
from pathlib import Path

class SSHKeyFileInput(forms.ClearableFileInput):
    template_name = 'django/forms/widgets/clearable_file_input.html'
    
    class Media:
        css = {
            'all': ('admin/css/ssh_key_input.css',)
        }
        js = ('admin/js/ssh_key_input.js',)

    def __init__(self, attrs=None):
        default_attrs = {
            'accept': '*',
            'class': 'ssh-key-file-input',
            'type': 'file'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        return format_html(
            '<div class="ssh-key-file-input-wrapper">'
            '<button type="button" class="button select-ssh-key">上传 SSH 私钥文件</button>'
            '<span class="ssh-key-file-name"></span>'
            '{}</div>',
            html
        )

class SSHKeyFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = SSHKeyFileInput()

    def clean(self, value, initial):
        if value:
            # 读取上传的文件内容
            content = value.read().decode('utf-8')
            # 验证 SSH 密钥格式
            if not (content.strip().startswith('-----BEGIN') and content.strip().endswith('PRIVATE KEY-----')):
                raise forms.ValidationError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件')
            # 将文件内容保存到 ssh_key 字段
            if hasattr(self, 'parent') and hasattr(self.parent, 'instance'):
                self.parent.instance.ssh_key = content
        return value

class GlobalConfigForm(forms.ModelForm):
    ssh_key_file = forms.FileField(
        label='SSH 私钥文件',
        required=False,
        widget=SSHKeyFileInput(),
        help_text='上传 SSH 私钥文件（支持 .pem、.key、.rsa 格式或无后缀名文件）'
    )

    class Meta:
        model = GlobalConfig
        fields = ('https_username', 'https_password', 'ssh_key')
        widgets = {
            'https_password': forms.PasswordInput(render_value=True),
            'ssh_key': forms.Textarea(attrs={
                'rows': 10,
                'class': 'ssh-key-textarea',
                'placeholder': '如果不上传文件，也可以直接粘贴 SSH 私钥内容到这里（支持 RSA 格式）'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        if 'ssh_key_file' in self.files:
            try:
                file = self.files['ssh_key_file']
                content = file.read().decode('utf-8')
                # 验证 SSH 密钥格式
                if not (content.strip().startswith('-----BEGIN') and content.strip().endswith('PRIVATE KEY-----')):
                    raise forms.ValidationError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件')
                cleaned_data['ssh_key'] = content
            except UnicodeDecodeError:
                raise forms.ValidationError('无效的文件格式，请确保上传的是文本格式的 SSH 私钥文件')
            except Exception as e:
                raise forms.ValidationError(f'读取文件失败：{str(e)}')
        return cleaned_data

@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    form = GlobalConfigForm
    list_display = ('id', 'https_username', 'ssh_key_info')
    
    class Media:
        css = {
            'all': ('admin/css/ssh_key_input.css',)
        }
        js = ('admin/js/ssh_key_input.js',)
    
    def ssh_key_info(self, obj):
        return format_html('<span class="ssh-key-status">{}</span>', 
                         '已配置' if obj.ssh_key else '未配置')
    ssh_key_info.short_description = 'SSH密钥状态'
    
    def has_add_permission(self, request):
        if GlobalConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj and GlobalConfig.objects.count() <= 1:
            return False
        return super().has_delete_permission(request, obj)

class RepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ['url', 'branch']

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        
        if url:
            # 生成仓库名称
            name = Repository.generate_name_from_url(url)
            
            # 检查名称是否已存在
            if Repository.objects.filter(name=name).exists():
                raise forms.ValidationError('该仓库已存在')
            
            # 检查认证信息
            config = GlobalConfig.objects.first()
            if not config:
                raise forms.ValidationError('请先配置全局认证信息')
            
            is_ssh = url.startswith('git@') or url.startswith('ssh://')
            if is_ssh:
                if not config.ssh_key:
                    raise forms.ValidationError('使用 SSH 协议需要配置 SSH 私钥')
                # 验证 SSH 密钥格式
                key_content = config.ssh_key.strip()
                if not (key_content.startswith('-----BEGIN') and key_content.endswith('PRIVATE KEY-----')):
                    raise forms.ValidationError('SSH 私钥格式无效，请检查全局配置中的 SSH 私钥格式')
            elif not (config.https_username and config.https_password):
                raise forms.ValidationError('使用 HTTPS 协议需要配置用户名和密码')
            
            cleaned_data['name'] = name
        
        return cleaned_data

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    form = RepositoryForm
    list_display = ('name', 'url', 'branch', 'get_last_sync_time', 'get_sync_status')
    list_filter = ('branch',)
    search_fields = ('name', 'url')
    readonly_fields = ('name', 'get_last_sync_time', 'get_sync_status')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('url', 'branch')
        }),
        ('同步状态', {
            'fields': ('get_last_sync_time', 'get_sync_status'),
            'classes': ('collapse',)
        }),
    )
    
    def get_last_sync_time(self, obj):
        return obj.last_sync_time if hasattr(obj, 'last_sync_time') else None
    get_last_sync_time.short_description = '最后同步时间'
    
    def get_sync_status(self, obj):
        if not obj.last_sync_time:
            return format_html('<span style="color: #999;">未同步</span>')
        return format_html('<span style="color: green;">已同步</span>')
    get_sync_status.short_description = '同步状态'
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建仓库时
            # 设置本地路径
            obj.local_path = obj.get_local_path()
            
            try:
                # 确保目录存在
                os.makedirs(obj.local_path, exist_ok=True)
                
                # 准备克隆选项
                clone_kwargs = {
                    'url': obj.get_clone_url(),
                    'to_path': obj.local_path,
                    'branch': obj.branch,
                }
                
                # 获取全局配置
                config = GlobalConfig.objects.first()
                
                # 处理 SSH 密钥
                if obj.is_ssh_protocol() and config and config.ssh_key:
                    # 创建临时文件存储 SSH 密钥
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                        key_file.write(config.ssh_key.strip())  # 确保移除多余的空白字符
                        key_file.flush()
                        # 设置正确的权限
                        os.chmod(key_file.name, 0o600)
                        
                        try:
                            # 配置 SSH 命令
                            git_ssh_cmd = f'ssh -i {key_file.name} -o StrictHostKeyChecking=no'
                            clone_kwargs['env'] = {'GIT_SSH_COMMAND': git_ssh_cmd}
                            
                            # 克隆仓库
                            git.Repo.clone_from(**clone_kwargs)
                        finally:
                            # 确保在任何情况下都清理临时文件
                            try:
                                os.unlink(key_file.name)
                            except OSError:
                                pass
                else:
                    # 使用 HTTPS 认证
                    git.Repo.clone_from(**clone_kwargs)
                
                messages.success(request, f'仓库 {obj.name} 克隆成功')
            except git.exc.GitCommandError as e:
                if 'Permission denied (publickey)' in str(e):
                    messages.error(request, f'仓库克隆失败：SSH 密钥认证失败，请检查密钥是否正确')
                elif 'Authentication failed' in str(e):
                    messages.error(request, f'仓库克隆失败：HTTPS 认证失败，请检查用户名和密码是否正确')
                else:
                    messages.error(request, f'仓库克隆失败：{str(e)}')
                raise
            except Exception as e:
                messages.error(request, f'仓库克隆失败：{str(e)}')
                raise
        
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:repo_id>/sync/',
                self.admin_site.admin_view(self.sync_repository),
                name='repository-sync',
            ),
            path(
                '<int:repo_id>/commit/',
                self.admin_site.admin_view(self.commit_repository),
                name='repository-commit',
            ),
        ]
        return custom_urls + urls
    
    def sync_repository(self, request, repo_id):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        repo = Repository.objects.get(id=repo_id)
        config = GlobalConfig.objects.first()
        
        try:
            git_repo = git.Repo(repo.local_path)
            
            # 处理 SSH 密钥
            if repo.is_ssh_protocol() and config and config.ssh_key:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                    key_file.write(config.ssh_key)
                    key_file.flush()
                    os.chmod(key_file.name, 0o600)
                    
                    # 配置 SSH 命令
                    git_ssh_cmd = f'ssh -i {key_file.name} -o StrictHostKeyChecking=no'
                    with git_repo.git.custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                        git_repo.remotes.origin.fetch()
                        git_repo.remotes.origin.pull()
                    
                    # 清理临时文件
                    os.unlink(key_file.name)
            else:
                # 处理 HTTPS 认证
                if config and config.https_username and config.https_password:
                    origin = git_repo.remotes.origin
                    url = repo.get_clone_url()
                    origin.set_url(url)
                
                git_repo.remotes.origin.fetch()
                git_repo.remotes.origin.pull()
            
            repo.last_sync_time = timezone.now()
            repo.save()
            
            messages.success(request, f'仓库 {repo.name} 同步成功')
        except Exception as e:
            messages.error(request, f'仓库同步失败：{str(e)}')
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
    
    def commit_repository(self, request, repo_id):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        repo = Repository.objects.get(id=repo_id)
        config = GlobalConfig.objects.first()
        
        try:
            git_repo = git.Repo(repo.local_path)
            
            # 添加所有更改
            git_repo.git.add('--all')
            
            # 检查是否有更改需要提交
            if git_repo.is_dirty():
                # 提交更改
                git_repo.index.commit(f'Auto commit at {timezone.now()}')
                
                # 处理 SSH 密钥
                if repo.is_ssh_protocol() and config and config.ssh_key:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                        key_file.write(config.ssh_key)
                        key_file.flush()
                        os.chmod(key_file.name, 0o600)
                        
                        # 配置 SSH 命令
                        git_ssh_cmd = f'ssh -i {key_file.name} -o StrictHostKeyChecking=no'
                        with git_repo.git.custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                            git_repo.remotes.origin.push()
                        
                        # 清理临时文件
                        os.unlink(key_file.name)
                else:
                    # 处理 HTTPS 认证
                    if config and config.https_username and config.https_password:
                        origin = git_repo.remotes.origin
                        url = repo.get_clone_url()
                        origin.set_url(url)
                    
                    git_repo.remotes.origin.push()
                
                messages.success(request, f'仓库 {repo.name} 提交并推送成功')
            else:
                messages.info(request, f'仓库 {repo.name} 没有需要提交的更改')
        except Exception as e:
            messages.error(request, f'仓库提交失败：{str(e)}')
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))

# 注册其他模型
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'class_name']
    search_fields = ['student_id', 'name', 'class_name']
    list_filter = ['class_name']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'due_date', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['due_date', 'created_at']
    date_hierarchy = 'due_date'

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'submitted_at', 'grade', 'status']
    search_fields = ['student__name', 'student__student_id', 'assignment__name']
    list_filter = ['status', 'submitted_at', 'assignment']
    date_hierarchy = 'submitted_at'
    raw_id_fields = ['student', 'assignment']