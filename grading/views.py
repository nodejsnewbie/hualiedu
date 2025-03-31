import logging
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import os
from docx import Document
from django.conf import settings
import shutil
import json
import tempfile
import traceback
import mimetypes
import mammoth
import base64
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from .utils import FileHandler, DirectoryHandler, GradeHandler, GitHandler
from .config import WORD_STYLE_MAP, DIRECTORY_STRUCTURE
from django.views.decorators.http import require_http_methods
from .models import GlobalConfig, Repository
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    return render(request, 'index.html')


def grading_page(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 处理创建目录请求
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create_directory':
                try:
                    repo_path = data.get('repo_path')
                    if not repo_path:
                        return JsonResponse({
                            'status': 'error',
                            'message': '未提供仓库路径'
                        })
                    
                    logger.info(f'收到克隆仓库请求，源路径: {repo_path}')
                    
                    # 检查是否为 Git 仓库
                    if not GitHandler.is_git_repo(repo_path):
                        return JsonResponse({
                            'status': 'error',
                            'message': '所选路径不是有效的 Git 仓库'
                        })
                    
                    # 获取仓库名称
                    repo_name = GitHandler.get_repo_name(repo_path)
                    logger.info(f'获取到仓库名称: {repo_name}')
                    
                    # 构建目标路径
                    target_path = os.path.join(settings.BASE_DIR, 'media', 'grades', repo_name)
                    logger.info(f'目标路径: {target_path}')
                    
                    # 克隆仓库
                    if not GitHandler.clone_repo(repo_path, target_path):
                        return JsonResponse({
                            'status': 'error',
                            'message': '克隆仓库失败，请检查日志'
                        })
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': '仓库克隆成功',
                        'repo_name': repo_name
                    })
                except Exception as e:
                    logger.error(f'克隆仓库失败: {str(e)}')
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    })
        
        # 处理文件上传请求
        if action == 'upload_directory':
            try:
                target_path = request.POST.get('target_path')
                files = request.FILES.getlist('files[]')
                file_paths = request.POST.getlist('file_paths[]')
                
                if not FileHandler.is_safe_path(target_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '无效的上传路径'
                    })
                
                uploaded_files = []
                for file, rel_path in zip(files, file_paths):
                    # 构建目标文件路径
                    target_file_path = os.path.join(
                        settings.BASE_DIR,
                        target_path.lstrip('/'),
                        os.path.dirname(rel_path)
                    )
                    
                    # 创建必要的目录
                    DirectoryHandler.ensure_directory(target_file_path)
                    
                    # 构建完整的文件路径
                    full_file_path = os.path.join(target_file_path, os.path.basename(rel_path))
                    
                    # 检查文件类型
                    if not FileHandler.is_allowed_file(full_file_path):
                        continue
                    
                    # 保存文件
                    with open(full_file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    uploaded_files.append(rel_path)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'成功上传 {len(uploaded_files)} 个文件',
                    'files': uploaded_files
                })
            except Exception as e:
                logger.error(f'文件上传失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # 处理获取目录树请求
        elif action == 'get_directory_tree':
            try:
                file_path = request.POST.get('file_path', '')
                
                # 从全局配置获取仓库基础目录
                config = GlobalConfig.objects.first()
                if not config or not config.repo_base_dir:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未配置仓库基础目录'
                    })
                
                # 展开路径中的用户目录符号（~）
                base_dir = os.path.expanduser(config.repo_base_dir)
                
                # 如果目录不存在，尝试创建它
                if not os.path.exists(base_dir):
                    try:
                        os.makedirs(base_dir, exist_ok=True)
                    except Exception as e:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'无法创建目录: {str(e)}'
                        })
                
                # 如果是根路径，使用基础目录
                if not file_path:
                    full_path = base_dir
                else:
                    full_path = os.path.join(base_dir, file_path)
                
                # 确保路径在基础目录内
                if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
                    return JsonResponse({'status': 'error', 'message': 'Invalid path'})
                
                if not os.path.exists(full_path):
                    return JsonResponse({'status': 'error', 'message': 'Path does not exist'})
                
                # 获取目录内容
                items = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    relative_path = os.path.relpath(item_path, base_dir)
                    
                    if os.path.isdir(item_path):
                        items.append({
                            'path': relative_path,
                            'name': item,
                            'type': 'folder',
                            'children': True  # 表示这是一个目录，可能有子项
                        })
                    else:
                        items.append({
                            'path': relative_path,
                            'name': item,
                            'type': 'file',
                            'children': False
                        })
                
                # 按类型和名称排序：目录在前，文件在后
                items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
                
                return JsonResponse({
                    'status': 'success',
                    'children': items
                })
                
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        
        # 处理获取内容请求
        elif action == 'get_content':
            try:
                file_path = request.POST.get('file_path')
                if not file_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未提供文件路径'
                    })

                # 从全局配置获取仓库基础目录
                config = GlobalConfig.objects.first()
                if not config or not config.repo_base_dir:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未配置仓库基础目录'
                    })
                
                # 展开路径中的用户目录符号（~）
                base_dir = os.path.expanduser(config.repo_base_dir)
                full_path = os.path.join(base_dir, file_path)
                
                # 确保路径在基础目录内
                if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
                    return JsonResponse({
                        'status': 'error',
                        'message': '无权访问该文件'
                    })

                if not os.path.exists(full_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在'
                    })

                if not os.path.isfile(full_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '不是有效的文件'
                    })
                
                # 检查文件类型
                mime_type = FileHandler.get_mime_type(full_path)
                if not mime_type:
                    return JsonResponse({
                        'status': 'error',
                        'message': '无法识别的文件类型'
                    })

                content = None
                
                # 处理 Word 文档
                if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    content = FileHandler.handle_docx(full_path)
                    if not content:
                        return JsonResponse({
                            'status': 'error',
                            'message': '无法读取 Word 文档内容'
                        })
                # 处理 PDF 文件
                elif mime_type == 'application/pdf':
                    content = f'''
                    <div class="pdf-container">
                        <object data="/grading/file/{file_path}" type="application/pdf" width="100%" height="100%">
                            <p>您的浏览器不支持 PDF 预览，<a href="/grading/file/{file_path}" target="_blank">点击下载</a></p>
                        </object>
                    </div>
                    '''
                    return JsonResponse({
                        'status': 'success',
                        'content': content
                    })
                # 处理文本文件
                elif mime_type.startswith('text/'):
                    content = FileHandler.read_text_file(full_path)
                    if not content:
                        return JsonResponse({
                            'status': 'error',
                            'message': '无法读取文本文件内容'
                        })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': '不支持的文件类型'
                    })
                
                return JsonResponse({
                    'status': 'success',
                    'content': content
                })
            except Exception as e:
                logger.error(f'读取文件失败: {str(e)}\n{traceback.format_exc()}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'读取文件失败: {str(e)}'
                })
        
        # 处理保存评分请求
        elif action == 'save_grade':
            try:
                grade = request.POST.get('grade')
                if not grade or not GradeHandler.validate_grade(grade):
                    return JsonResponse({
                        'status': 'error',
                        'message': '无效的评分'
                    })
                
                # TODO: 实现评分保存逻辑
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'评分已保存: {GradeHandler.get_grade_description(grade)}'
                })
            except Exception as e:
                logger.error(f'保存评分失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # 处理获取课程列表请求
        elif action == 'get_courses':
            try:
                # 获取grades目录下的所有课程目录
                grades_dir = os.path.join(settings.MEDIA_ROOT, 'grades')
                os.makedirs(grades_dir, exist_ok=True)
                courses = [d for d in os.listdir(grades_dir) 
                         if os.path.isdir(os.path.join(grades_dir, d))]
                
                return JsonResponse({
                    'status': 'success',
                    'courses': courses
                })
            except Exception as e:
                logger.error(f'获取课程列表失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'获取课程列表失败: {str(e)}'
                })

        # 处理获取班级列表请求
        elif action == 'get_classes':
            try:
                course_name = request.POST.get('course_name')
                if not course_name:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未提供课程名称'
                    })

                # 获取课程目录下的所有班级目录
                course_dir = os.path.join(settings.MEDIA_ROOT, 'grades', course_name)
                if not os.path.exists(course_dir):
                    return JsonResponse({
                        'status': 'success',
                        'classes': []
                    })

                classes = [d for d in os.listdir(course_dir) 
                         if os.path.isdir(os.path.join(course_dir, d))]
                
                return JsonResponse({
                    'status': 'success',
                    'classes': classes
                })
            except Exception as e:
                logger.error(f'获取班级列表失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'获取班级列表失败: {str(e)}'
                })
        
        else:
            return JsonResponse({
                'status': 'error',
                'message': '无效的操作'
            })
    
    # GET 请求返回页面
    return render(request, 'grading.html', {
        'upload_path': '/media/grades'
    })


def get_directory_structure(root_dir):
    try:
        name = os.path.basename(root_dir)
        structure = {
            'text': name,
            'children': [],
            'type': 'folder',
            'id': root_dir
        }
        
        if not os.path.exists(root_dir):
            logger.warning(f'目录不存在: {root_dir}')
            return structure
        
        # 过滤掉隐藏文件和目录
        items = [item for item in sorted(os.listdir(root_dir)) if not item.startswith('.')]
        
        for item in items:
            path = os.path.join(root_dir, item)
            if os.path.isdir(path):
                structure['children'].append(get_directory_structure(path))
            else:
                structure['children'].append({
                    'text': item,
                    'type': 'file',
                    'icon': 'jstree-file',
                    'id': path
                })
        return structure
    
    except Exception as e:
        logger.error(f'获取目录结构失败: {str(e)}')
        return {
            'text': os.path.basename(root_dir),
            'children': [],
            'type': 'folder',
            'id': root_dir
        }

def is_safe_path(path):
    """检查路径是否在允许的范围内"""
    normalized_path = os.path.normpath(path)
    return normalized_path.startswith(os.path.join(settings.BASE_DIR, 'media', 'grades'))

@require_http_methods(['POST'])
def create_directory(request):
    """创建目录"""
    try:
        data = json.loads(request.body)
        repo_name = data.get('repo_name')
        
        if not repo_name:
            return JsonResponse({'status': 'error', 'message': '未提供仓库名称'})
            
        logger.info(f'接收到的仓库名称: {repo_name}')
        
        # 构建目标路径
        target_path = os.path.join(settings.BASE_DIR, 'media', 'grades', repo_name)
        logger.info(f'目标路径: {target_path}')
        
        # 创建目录
        success = GitHandler.clone_repo(repo_name, target_path)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': '目录创建成功',
                'repo_name': repo_name
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': '目录创建失败，请检查日志'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '无效的 JSON 数据'})
    except Exception as e:
        logger.error(f'创建目录时发生错误: {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)})

def serve_file(request, file_path):
    """提供文件下载服务"""
    try:
        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            return HttpResponse('未配置仓库基础目录', status=400)
        
        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, file_path)
        
        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
            return HttpResponse('无权访问该文件', status=403)

        if not os.path.exists(full_path):
            return HttpResponse('文件不存在', status=404)

        # 获取文件类型
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # 以二进制模式读取文件
        with open(full_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            return response

    except Exception as e:
        logger.error(f'文件服务失败: {str(e)}')
        return HttpResponse('服务器错误', status=500)

@login_required
def change_branch(request, repo_id):
    """切换仓库分支"""
    try:
        repo = Repository.objects.get(id=repo_id)
        if request.method == 'POST':
            branch = request.POST.get('branch')
            if branch in repo.branches:
                repo.branch = branch
                repo.save()
                messages.success(request, f'已切换到分支 {branch}')
                return redirect('admin:grading_repository_changelist')
            else:
                messages.error(request, f'分支 {branch} 不存在')
        return render(request, 'admin/grading/repository/change_branch.html', {
            'repo': repo,
            'branches': repo.branches,
            'current_branch': repo.branch
        })
    except Repository.DoesNotExist:
        messages.error(request, '仓库不存在')
        return redirect('admin:grading_repository_changelist')

@login_required
def grading_view(request):
    logger.info('开始处理评分页面请求')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        logger.info(f'收到 POST 请求，action: {action}')
        
        if action == 'get_content':
            path = request.POST.get('path')
            logger.info(f'请求获取文件内容，路径: {path}')
            try:
                # 从全局配置获取仓库基础目录
                config = GlobalConfig.objects.first()
                if not config or not config.repo_base_dir:
                    logger.error('未配置仓库基础目录')
                    return JsonResponse({
                        'status': 'error',
                        'message': '未配置仓库基础目录'
                    })
                
                # 展开路径中的用户目录符号（~）
                base_dir = os.path.expanduser(config.repo_base_dir)
                full_path = os.path.join(base_dir, path)
                
                logger.info(f'尝试读取文件: {full_path}')
                
                # 检查文件是否存在
                if not os.path.exists(full_path):
                    logger.error(f'文件不存在: {full_path}')
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在'
                    })
                
                # 读取文件内容
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f'成功读取文件: {full_path}')
                return JsonResponse({
                    'status': 'success',
                    'content': content
                })
            except Exception as e:
                logger.error(f'读取文件失败: {str(e)}\n{traceback.format_exc()}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
                
        elif action == 'save_grade':
            path = request.POST.get('path')
            grade = request.POST.get('grade')
            logger.info(f'保存评分: 文件={path}, 评分={grade}')
            try:
                # 这里可以添加保存评分的逻辑
                # 例如保存到数据库或文件中
                return JsonResponse({
                    'status': 'success',
                    'message': '评分已保存'
                })
            except Exception as e:
                logger.error(f'保存评分失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
    
    # GET 请求，显示评分页面
    try:
        logger.info('处理 GET 请求，准备显示评分页面')
        
        # 从全局配置获取仓库基础目录
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error('未配置仓库基础目录')
            return render(request, 'grading.html', {
                'files': [],
                'error': '未配置仓库基础目录'
            })
        
        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        logger.info(f'使用仓库基础目录: {base_dir}')
        
        # 如果目录不存在，尝试创建它
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir, exist_ok=True)
                logger.info(f'创建目录: {base_dir}')
            except Exception as e:
                logger.error(f'创建目录失败: {str(e)}')
                return render(request, 'grading.html', {
                    'files': [],
                    'error': f'无法创建目录: {str(e)}'
                })
        
        # 获取所有文件
        files = []
        logger.info('开始扫描文件...')
        
        # 检查目录权限
        try:
            os.access(base_dir, os.R_OK)
            logger.info(f'目录 {base_dir} 可读')
        except Exception as e:
            logger.error(f'目录权限检查失败: {str(e)}')
        
        for root, dirs, filenames in os.walk(base_dir):
            # 过滤掉隐藏文件和目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]
            
            logger.info(f'扫描目录: {root}')
            logger.info(f'发现文件: {filenames}')
            
            for filename in filenames:
                # 构建相对路径
                rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                full_path = os.path.join(root, filename)
                
                # 检查文件类型
                mime_type = FileHandler.get_mime_type(full_path)
                logger.info(f'文件类型检查: {filename} -> {mime_type}')
                
                if mime_type and (mime_type.startswith('text/') or 
                                mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or
                                mime_type == 'application/pdf'):
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'type': mime_type
                    })
                    logger.info(f'添加文件: {filename} ({mime_type})')
        
        # 按文件名排序
        files.sort(key=lambda x: x['name'].lower())
        
        # 添加调试信息
        logger.info(f'找到 {len(files)} 个文件')
        for file in files:
            logger.info(f'文件: {file["name"]}, 路径: {file["path"]}, 类型: {file["type"]}')
        
        return render(request, 'grading.html', {
            'files': files,
            'error': None
        })
        
    except Exception as e:
        logger.error(f'获取文件列表失败: {str(e)}\n{traceback.format_exc()}')
        return render(request, 'grading.html', {
            'files': [],
            'error': f'获取文件列表失败: {str(e)}'
        })
