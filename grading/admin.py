import os
import git
import shutil
import tempfile
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render
from django import forms
from .models import Student, Assignment, Submission, Repository, GlobalConfig
from django.conf import settings
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
    """全局配置表单"""
    
    class Meta:
        model = GlobalConfig
        fields = ('https_username', 'https_password', 'ssh_key', 'ssh_key_file')
        widgets = {
            'https_password': forms.PasswordInput(render_value=True),
            'ssh_key': forms.Textarea(attrs={
                'rows': 10,
                'cols': 80,
                'class': 'vLargeTextField',
                'style': 'display: block !important; width: 100%; height: 200px; font-family: monospace; margin-bottom: 10px;',
                'placeholder': '如果不上传文件，也可以直接粘贴 SSH 私钥内容到这里（支持 RSA 格式）'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.ssh_key:
            self.initial['ssh_key'] = self.instance.ssh_key
            # 确保文本框可见
            self.fields['ssh_key'].widget.attrs['style'] = 'display: block !important; width: 100%; height: 200px; font-family: monospace; margin-bottom: 10px;'

    def clean(self):
        """验证表单数据"""
        cleaned_data = super().clean()
        
        # 验证 HTTPS 认证信息
        https_username = cleaned_data.get('https_username')
        https_password = cleaned_data.get('https_password')
        
        if bool(https_username) != bool(https_password):
            raise forms.ValidationError('HTTPS 用户名和密码必须同时提供或同时为空')
        
        # 验证 SSH 密钥
        ssh_key_file = cleaned_data.get('ssh_key_file')
        if ssh_key_file:
            try:
                content = ssh_key_file.read().decode('utf-8')
                # 验证 SSH 密钥格式
                if not (content.strip().startswith('-----BEGIN') and content.strip().endswith('PRIVATE KEY-----')):
                    raise forms.ValidationError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件')
                # 检查密钥类型
                if 'OPENSSH PRIVATE KEY' not in content and 'RSA PRIVATE KEY' not in content:
                    raise forms.ValidationError('不支持的 SSH 私钥格式，请确保上传的是 RSA 或 ED25519 格式的私钥文件')
                cleaned_data['ssh_key'] = content
            except UnicodeDecodeError:
                raise forms.ValidationError('无效的文件格式，请确保上传的是文本格式的 SSH 私钥文件')
            except Exception as e:
                raise forms.ValidationError(f'读取文件失败：{str(e)}')
        
        return cleaned_data

    def save(self, commit=True):
        """保存表单数据"""
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    """全局配置管理界面"""
    
    form = GlobalConfigForm
    list_display = ('updated_at', 'has_https_auth', 'has_ssh_key')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('认证信息', {
            'fields': ('https_username', 'https_password', 'ssh_key_file', 'ssh_key'),
            'description': '配置访问 Git 仓库所需的认证信息。可以使用 HTTPS 用户名密码或 SSH 私钥。'
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '系统自动记录的时间信息。'
        }),
    )

    def has_https_auth(self, obj):
        """检查是否配置了 HTTPS 认证"""
        return bool(obj.https_username and obj.https_password)
    has_https_auth.boolean = True
    has_https_auth.short_description = 'HTTPS 认证'

    def has_ssh_key(self, obj):
        """检查是否配置了 SSH 密钥"""
        return bool(obj.ssh_key)
    has_ssh_key.boolean = True
    has_ssh_key.short_description = 'SSH 密钥'

    def get_readonly_fields(self, request, obj=None):
        """获取只读字段"""
        if obj:  # 编辑现有对象
            return self.readonly_fields + ('created_at',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """保存模型时的处理"""
        if not change:  # 新建仓库时
            # 设置本地路径
            obj.local_path = obj.get_local_path()
            
            try:
                # 确保 media/repo 目录存在
                repo_dir = os.path.join(settings.MEDIA_ROOT, 'repo')
                os.makedirs(repo_dir, exist_ok=True)
                
                # 如果目标目录已存在，先删除
                if os.path.exists(obj.local_path):
                    import shutil
                    shutil.rmtree(obj.local_path)
                
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
                        # 确保密钥内容格式正确
                        key_content = config.ssh_key.strip()
                        if not key_content.startswith('-----BEGIN'):
                            key_content = '-----BEGIN RSA PRIVATE KEY-----\n' + key_content
                        if not key_content.endswith('-----END'):
                            key_content = key_content + '\n-----END RSA PRIVATE KEY-----'
                        
                        # 确保密钥内容格式正确
                        key_content = key_content.replace('\r\n', '\n').replace('\r', '\n')
                        key_lines = key_content.split('\n')
                        formatted_key = '\n'.join(line.strip() for line in key_lines if line.strip())
                        
                        key_file.write(formatted_key)
                        key_file.flush()
                        # 设置正确的权限
                        os.chmod(key_file.name, 0o600)
                        
                        try:
                            # 配置 SSH 命令
                            git_ssh_cmd = f'ssh -i {key_file.name} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes'
                            clone_kwargs['env'] = {'GIT_SSH_COMMAND': git_ssh_cmd}
                            
                            # 克隆仓库
                            git.Repo.clone_from(**clone_kwargs)
                            # 更新同步时间
                            obj.last_sync_time = timezone.now()
                        finally:
                            # 确保在任何情况下都清理临时文件
                            try:
                                os.unlink(key_file.name)
                            except OSError:
                                pass
                else:
                    # 使用 HTTPS 认证
                    git.Repo.clone_from(**clone_kwargs)
                    # 更新同步时间
                    obj.last_sync_time = timezone.now()
                
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

    def has_add_permission(self, request):
        """控制是否允许添加新对象"""
        return not GlobalConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """控制是否允许删除对象"""
        return False

    class Media:
        css = {
            'all': ('admin/css/ssh_key_input.css',)
        }
        js = ('admin/js/ssh_key_input.js',)

class RepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ['url', 'branch']
        help_texts = {
            'url': '支持 SSH 和 HTTPS 格式。SSH 格式示例：git@gitee.com:username/repository.git，HTTPS 格式示例：https://gitee.com/username/repository.git'
        }

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        
        if url:
            # 生成仓库名称
            name = Repository.generate_name_from_url(url)
            
            # 检查 URL 是否已存在
            existing_repo = Repository.objects.filter(url=url).first()
            if existing_repo:
                raise forms.ValidationError(
                    f'该仓库 URL 已存在：\n'
                    f'仓库名称：{existing_repo.name}\n'
                    f'仓库 URL：{existing_repo.url}\n'
                    f'最后同步：{existing_repo.last_sync_time.strftime("%Y-%m-%d %H:%M:%S") if existing_repo.last_sync_time else "未同步"}'
                )
            
            # 检查认证信息
            config = GlobalConfig.objects.first()
            if not config:
                raise forms.ValidationError('请先配置全局认证信息')
            
            # 验证 URL 格式
            is_ssh = url.startswith('git@') or url.startswith('ssh://')
            if is_ssh:
                if not config.ssh_key:
                    raise forms.ValidationError('使用 SSH 协议需要配置 SSH 私钥')
                # 验证 SSH 密钥格式
                key_content = config.ssh_key.strip()
                if not (key_content.startswith('-----BEGIN') and key_content.endswith('PRIVATE KEY-----')):
                    raise forms.ValidationError('SSH 私钥格式无效，请检查全局配置中的 SSH 私钥格式')
                # 验证 SSH URL 格式
                if url.startswith('git@'):
                    # 移除 .git 后缀（如果有）
                    url = url.replace('.git', '')
                    # 分割主机和路径
                    parts = url.split(':')
                    if len(parts) != 2:
                        raise forms.ValidationError(
                            '无效的 SSH URL 格式。\n'
                            '正确格式为：git@host:username/repository\n'
                            '示例：git@gitee.com:username/repository'
                        )
                    # 验证路径部分
                    path_parts = parts[1].split('/')
                    if len(path_parts) < 2:
                        raise forms.ValidationError(
                            '无效的仓库路径格式。\n'
                            '正确格式为：username/repository\n'
                            '示例：username/repository'
                        )
            elif not url.startswith('http://') and not url.startswith('https://'):
                raise forms.ValidationError(
                    '无效的 URL 格式。\n'
                    '请使用以下格式之一：\n'
                    '1. SSH 格式：git@host:username/repository.git\n'
                    '2. HTTPS 格式：https://host/username/repository.git'
                )
            elif not (config.https_username and config.https_password):
                raise forms.ValidationError('使用 HTTPS 协议需要配置用户名和密码')
            
            cleaned_data['name'] = name
        
        return cleaned_data

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    form = RepositoryForm
    list_display = ('name', 'url', 'get_branch', 'get_last_sync_time', 'get_sync_status', 'get_action_buttons')
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
        """获取同步状态"""
        if not obj.is_cloned():
            return format_html('<span style="color: #999;">未克隆</span>')
        elif not hasattr(obj, 'last_sync_time') or not obj.last_sync_time:
            return format_html('<span style="color: #999;">未同步</span>')
        return format_html('<span style="color: green;">已同步</span>')
    get_sync_status.short_description = '同步状态'

    def get_branch(self, obj):
        """显示分支和修改按钮"""
        return format_html(
            '{} <a href="{}" class="button">修改</a>',
            obj.branch,
            reverse('admin:grading_repository_change_branch', args=[obj.pk])
        )
    get_branch.short_description = '分支'

    def get_action_buttons(self, obj):
        """获取操作按钮"""
        if not obj.is_cloned():
            # 如果仓库未克隆，只显示克隆按钮
            return format_html(
                '<div class="action-buttons">'
                '<a class="button" href="{}">克隆</a>'
                '</div>',
                reverse('admin:grading_repository_clone', args=[obj.pk])
            )
        
        # 如果仓库已克隆，显示更新、推送和清除按钮
        return format_html(
            '<div class="action-buttons">'
            '<a class="button" href="{}">更新</a> '
            '<a class="button" href="{}">推送</a> '
            '<a class="button delete-button" href="{}">清除</a>'
            '</div>',
            reverse('admin:grading_repository_sync', args=[obj.pk]),
            reverse('admin:grading_repository_push', args=[obj.pk]),
            reverse('admin:grading_repository_clear', args=[obj.pk])
        )
    get_action_buttons.short_description = '操作'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:repo_id>/clone/',
                self.admin_site.admin_view(self.clone_repository),
                name='grading_repository_clone',
            ),
            path(
                '<int:repo_id>/sync/',
                self.admin_site.admin_view(self.sync_repository),
                name='grading_repository_sync',
            ),
            path(
                '<int:repo_id>/push/',
                self.admin_site.admin_view(self.push_repository),
                name='grading_repository_push',
            ),
            path(
                '<int:repo_id>/clear/',
                self.admin_site.admin_view(self.clear_repository),
                name='grading_repository_clear',
            ),
            path(
                '<int:repo_id>/change_branch/',
                self.admin_site.admin_view(self.change_branch),
                name='grading_repository_change_branch',
            ),
        ]
        return custom_urls + urls

    def clone_repository(self, request, repo_id):
        """克隆仓库"""
        try:
            repo = Repository.objects.get(id=repo_id)
            local_path = repo.get_local_path()
            
            # 检查目录是否已存在
            if os.path.exists(local_path) and os.path.exists(os.path.join(local_path, '.git')):
                self.message_user(request, f'仓库目录已存在：{local_path}', level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
            
            # 如果目录存在但不是 git 仓库，则删除它
            if os.path.exists(local_path):
                import shutil
                shutil.rmtree(local_path)
            
            # 准备克隆选项
            clone_kwargs = {
                'url': repo.get_clone_url(),
                'to_path': local_path,
                'branch': repo.branch,
            }
            
            # 获取全局配置
            config = GlobalConfig.objects.first()
            
            # 处理 SSH 密钥
            if repo.is_ssh_protocol() and config and config.ssh_key:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                    key_file.write(config.ssh_key)
                    key_file.flush()
                    os.chmod(key_file.name, 0o600)
                    
                    try:
                        # 配置 SSH 命令
                        git_ssh_cmd = f'ssh -i {key_file.name} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes'
                        clone_kwargs['env'] = {'GIT_SSH_COMMAND': git_ssh_cmd}
                        
                        # 先克隆仓库，不指定分支
                        git_repo = git.Repo.clone_from(
                            url=clone_kwargs['url'],
                            to_path=clone_kwargs['to_path']
                        )
                        
                        # 获取所有远程分支
                        git_repo.git.fetch('--all')
                        remote_branches = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                        
                        # 检查分支是否存在
                        if repo.branch not in remote_branches:
                            # 如果分支不存在，删除仓库并提示用户
                            shutil.rmtree(local_path)
                            self.message_user(request, 
                                f'仓库克隆失败：分支 {repo.branch} 不存在。\n'
                                f'可用的分支有：\n' + 
                                '\n'.join(f'- {branch}' for branch in remote_branches) + 
                                '\n\n修改分支的方法：\n'
                                '1. 点击仓库名称进入编辑页面\n'
                                '2. 在"分支"字段中输入正确的分支名称\n'
                                '3. 点击"保存"按钮\n'
                                '4. 重新点击"克隆"按钮',
                                level=messages.ERROR)
                            return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                        
                        # 切换到指定分支
                        git_repo.git.checkout(repo.branch)
                        
                        # 更新同步时间
                        repo.last_sync_time = timezone.now()
                        repo.save()
                        self.message_user(request, f'仓库 {repo.name} 克隆成功')
                    finally:
                        # 清理临时文件
                        try:
                            os.unlink(key_file.name)
                        except:
                            pass
            else:
                # 使用 HTTPS 认证
                if config and config.https_username and config.https_password:
                    clone_kwargs['env'] = {
                        'GIT_ASKPASS': 'echo',
                        'GIT_USERNAME': config.https_username,
                        'GIT_PASSWORD': config.https_password
                    }
                
                # 先克隆仓库，不指定分支
                git_repo = git.Repo.clone_from(
                    url=clone_kwargs['url'],
                    to_path=clone_kwargs['to_path']
                )
                
                # 获取所有远程分支
                git_repo.git.fetch('--all')
                remote_branches = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                
                # 检查分支是否存在
                if repo.branch not in remote_branches:
                    # 如果分支不存在，删除仓库并提示用户
                    shutil.rmtree(local_path)
                    self.message_user(request, 
                        f'仓库克隆失败：分支 {repo.branch} 不存在。\n'
                        f'可用的分支有：\n' + 
                        '\n'.join(f'- {branch}' for branch in remote_branches) + 
                        '\n\n修改分支的方法：\n'
                        '1. 点击仓库名称进入编辑页面\n'
                        '2. 在"分支"字段中输入正确的分支名称\n'
                        '3. 点击"保存"按钮\n'
                        '4. 重新点击"克隆"按钮',
                        level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                
                # 切换到指定分支
                git_repo.git.checkout(repo.branch)
                
                # 更新同步时间
                repo.last_sync_time = timezone.now()
                repo.save()
                self.message_user(request, f'仓库 {repo.name} 克隆成功')
            
        except Repository.DoesNotExist:
            self.message_user(request, '仓库不存在', level=messages.ERROR)
        except git.exc.GitCommandError as e:
            if 'Permission denied (publickey)' in str(e):
                self.message_user(request, 
                    '仓库克隆失败：SSH 密钥认证失败，请检查：\n'
                    '1. SSH 密钥是否正确配置\n'
                    '2. 远程仓库地址是否正确\n'
                    '3. 是否有权限访问该仓库', 
                    level=messages.ERROR)
            elif 'Authentication failed' in str(e):
                self.message_user(request, 
                    '仓库克隆失败：HTTPS 认证失败，请检查：\n'
                    '1. 用户名和密码是否正确\n'
                    '2. 远程仓库地址是否正确\n'
                    '3. 是否有权限访问该仓库', 
                    level=messages.ERROR)
            else:
                self.message_user(request, f'仓库克隆失败：{str(e)}', level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f'克隆失败：{str(e)}', level=messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))

    def sync_repository(self, request, repo_id):
        """同步仓库"""
        try:
            repo = Repository.objects.get(id=repo_id)
            local_path = repo.get_local_path()
            
            # 检查目录是否存在
            if not os.path.exists(local_path):
                self.message_user(request, f'仓库目录不存在：{local_path}', level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
            
            # 检查目录权限
            if not os.access(local_path, os.R_OK | os.W_OK):
                self.message_user(request, f'仓库目录权限不足：{local_path}', level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
            
            # 获取 Git 仓库对象
            git_repo = git.Repo(local_path)
            
            # 检查远程仓库配置
            if not git_repo.remotes:
                self.message_user(request, '仓库没有配置远程地址', level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
            
            # 检查 SSH 密钥配置
            if repo.is_ssh_protocol():
                config = GlobalConfig.objects.first()
                if not config or not config.ssh_key:
                    self.message_user(request, 'SSH 密钥未配置，请先在全局配置中设置 SSH 密钥', level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                
                # 创建临时 SSH 密钥文件
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                    key_file.write(config.ssh_key)
                    key_path = key_file.name
                
                try:
                    # 设置 SSH 密钥文件权限
                    os.chmod(key_path, 0o600)
                    
                    # 配置 Git 使用临时 SSH 密钥
                    with git_repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -i {key_path} -o StrictHostKeyChecking=no'):
                        # 尝试获取远程信息
                        try:
                            git_repo.git.fetch('-v', '--all')
                        except git.exc.GitCommandError as e:
                            if 'Could not read from remote repository' in str(e):
                                self.message_user(request, 
                                    '无法访问远程仓库，请检查：\n'
                                    '1. SSH 密钥是否正确配置\n'
                                    '2. 远程仓库地址是否正确\n'
                                    '3. 是否有权限访问该仓库', 
                                    level=messages.ERROR)
                            else:
                                self.message_user(request, f'Git 操作失败：{str(e)}', level=messages.ERROR)
                            return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                        
                        # 检查分支是否存在
                        try:
                            git_repo.git.show_ref(f'refs/remotes/origin/{repo.branch}')
                        except git.exc.GitCommandError:
                            # 获取所有可用分支
                            branches = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                            self.message_user(request, 
                                f'分支 {repo.branch} 不存在。\n'
                                f'可用的分支有：\n' + 
                                '\n'.join(f'- {branch}' for branch in branches) + 
                                '\n\n请修改仓库的分支设置。',
                                level=messages.ERROR)
                            return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                        
                        # 更新代码
                        git_repo.git.pull('origin', repo.branch)
                        repo.last_sync_time = timezone.now()
                        repo.save()
                        self.message_user(request, '仓库同步成功')
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(key_path)
                    except:
                        pass
            else:
                # HTTPS 方式
                config = GlobalConfig.objects.first()
                if not config or not config.https_username or not config.https_password:
                    self.message_user(request, 'HTTPS 认证信息未配置，请先在全局配置中设置用户名和密码', level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                
                # 配置 Git 使用 HTTPS 认证
                with git_repo.git.custom_environment(
                    GIT_ASKPASS='echo',
                    GIT_USERNAME=config.https_username,
                    GIT_PASSWORD=config.https_password
                ):
                    try:
                        git_repo.git.fetch('-v', '--all')
                        
                        # 检查分支是否存在
                        try:
                            git_repo.git.show_ref(f'refs/remotes/origin/{repo.branch}')
                        except git.exc.GitCommandError:
                            # 获取所有可用分支
                            branches = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                            self.message_user(request, 
                                f'分支 {repo.branch} 不存在。\n'
                                f'可用的分支有：\n' + 
                                '\n'.join(f'- {branch}' for branch in branches) + 
                                '\n\n请修改仓库的分支设置。',
                                level=messages.ERROR)
                            return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                        
                        git_repo.git.pull('origin', repo.branch)
                        repo.last_sync_time = timezone.now()
                        repo.save()
                        self.message_user(request, '仓库同步成功')
                    except git.exc.GitCommandError as e:
                        self.message_user(request, 
                            '仓库同步失败，请检查：\n'
                            '1. HTTPS 认证信息是否正确\n'
                            '2. 远程仓库地址是否正确\n'
                            '3. 是否有权限访问该仓库', 
                            level=messages.ERROR)
            
        except Repository.DoesNotExist:
            self.message_user(request, '仓库不存在', level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f'同步失败：{str(e)}', level=messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))

    def push_repository(self, request, repo_id):
        """推送仓库更改"""
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
            messages.error(request, f'仓库推送失败：{str(e)}')
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))

    def clear_repository(self, request, repo_id):
        """清除仓库"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        repo = Repository.objects.get(id=repo_id)
        
        try:
            # 删除本地目录
            if os.path.exists(repo.local_path):
                import shutil
                shutil.rmtree(repo.local_path)
            
            # 删除数据库记录
            repo.delete()
            
            messages.success(request, f'仓库 {repo.name} 已清除')
        except Exception as e:
            messages.error(request, f'清除仓库失败：{str(e)}')
        
        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))

    def get_actions(self, request):
        """获取批量操作"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def change_branch(self, request, repo_id):
        """修改分支"""
        try:
            repo = Repository.objects.get(id=repo_id)
            
            if request.method == 'POST':
                new_branch = request.POST.get('branch')
                if not new_branch:
                    self.message_user(request, '请选择分支', level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                
                # 如果仓库已克隆，验证分支是否存在并切换
                if repo.is_cloned():
                    git_repo = git.Repo(repo.get_local_path())
                    git_repo.git.fetch('--all')
                    remote_branches = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                    
                    if new_branch not in remote_branches:
                        self.message_user(request, 
                            f'分支 {new_branch} 不存在。\n'
                            f'可用的分支有：\n' + 
                            '\n'.join(f'- {branch}' for branch in remote_branches),
                            level=messages.ERROR)
                        return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
                    
                    # 切换到新分支
                    git_repo.git.checkout(new_branch)
                
                # 更新分支
                repo.branch = new_branch
                repo.save()
                
                self.message_user(request, f'分支已修改为：{new_branch}')
                return HttpResponseRedirect(reverse('admin:grading_repository_changelist'))
            
            # 显示分支选择页面
            context = {
                'title': '修改分支',
                'repo': repo,
                'branches': ['main', 'master', 'develop'],  # 默认显示常用分支
                'current_branch': repo.branch,
                'opts': self.model._meta,
                'app_label': self.model._meta.app_label,
                'has_permission': self.has_change_permission(request),
            }
            
            # 如果仓库已克隆，获取实际的分支列表
            if repo.is_cloned():
                try:
                    git_repo = git.Repo(repo.get_local_path())
                    git_repo.git.fetch('--all')
                    context['branches'] = [ref.name.split('/')[-1] for ref in git_repo.refs if ref.name.startswith('refs/remotes/origin/')]
                except Exception as e:
                    # 如果获取远程分支失败，使用默认分支列表
                    self.message_user(request, f'获取远程分支列表失败：{str(e)}，将显示默认分支列表', level=messages.WARNING)
            
            return render(request, 'admin/grading/repository/change_branch.html', context)
            
        except Repository.DoesNotExist:
            self.message_user(request, '仓库不存在', level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f'修改分支失败：{str(e)}', level=messages.ERROR)
        
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