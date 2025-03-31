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
    """评分页面"""
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'get_directory_tree':
            file_path = request.POST.get('file_path', '')
            items = get_directory_tree(file_path)
            print(f"Returning directory tree data: {items}")
            return JsonResponse({
                'status': 'success',
                'data': items
            })
        elif action == 'get_content':
            path = request.POST.get('path')
            try:
                config = GlobalConfig.objects.first()
                if not config:
                    config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
                base_dir = os.path.expanduser(config.repo_base_dir)
                full_path = os.path.join(base_dir, path)
                print(f"Loading file content from: {full_path}")
                
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return JsonResponse({
                        'status': 'success',
                        'content': content
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在'
                    })
            except Exception as e:
                print(f"Error loading file content: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        elif action == 'save_grade':
            path = request.POST.get('path')
            grade = request.POST.get('grade')
            try:
                config = GlobalConfig.objects.first()
                if not config:
                    config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
                base_dir = os.path.expanduser(config.repo_base_dir)
                full_path = os.path.join(base_dir, path)
                print(f"Saving grade for file: {full_path}")
                
                if os.path.exists(full_path):
                    # 保存评分
                    grade_file = os.path.join(base_dir, 'grades.json')
                    grades = {}
                    if os.path.exists(grade_file):
                        with open(grade_file, 'r', encoding='utf-8') as f:
                            grades = json.load(f)
                    grades[path] = grade
                    with open(grade_file, 'w', encoding='utf-8') as f:
                        json.dump(grades, f, ensure_ascii=False, indent=2)
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在'
                    })
            except Exception as e:
                print(f"Error saving grade: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
    
    # GET 请求，返回初始页面
    try:
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
        
        # 确保基础目录存在
        base_dir = os.path.expanduser(config.repo_base_dir)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # 获取初始目录树数据
        items = get_directory_tree()
        print(f"Initial directory tree data: {items}")
        
        # 将目录树数据转换为 JSON 字符串
        initial_tree_data = json.dumps(items, ensure_ascii=False)
        print(f"Initial tree data JSON: {initial_tree_data}")
        
        return render(request, 'grading.html', {
            'initial_tree_data': initial_tree_data
        })
    except Exception as e:
        print(f"Error in grading_page: {str(e)}")
        return render(request, 'grading.html', {
            'error': str(e),
            'initial_tree_data': '[]'
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
                'error': '未配置仓库基础目录',
                'config': config,
                'base_dir': None
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
                    'error': f'无法创建目录: {str(e)}',
                    'config': config,
                    'base_dir': base_dir
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
        
        # 遍历所有目录和文件
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
                
                logger.info(f'处理文件: {filename}')
                logger.info(f'相对路径: {rel_path}')
                logger.info(f'完整路径: {full_path}')
                
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
                else:
                    logger.info(f'跳过文件: {filename} (不支持的文件类型)')
        
        # 按文件名排序
        files.sort(key=lambda x: x['name'].lower())
        
        # 添加调试信息
        logger.info(f'找到 {len(files)} 个文件')
        for file in files:
            logger.info(f'文件: {file["name"]}, 路径: {file["path"]}, 类型: {file["type"]}')
        
        return render(request, 'grading.html', {
            'files': files,
            'error': None,
            'config': config,
            'base_dir': base_dir
        })
        
    except Exception as e:
        logger.error(f'获取文件列表失败: {str(e)}\n{traceback.format_exc()}')
        return render(request, 'grading.html', {
            'files': [],
            'error': f'获取文件列表失败: {str(e)}',
            'config': config if 'config' in locals() else None,
            'base_dir': base_dir if 'base_dir' in locals() else None
        })

def get_directory_tree(file_path=''):
    """获取目录树结构"""
    try:
        # 获取基础目录
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
        base_dir = os.path.expanduser(config.repo_base_dir)
        print(f"Base directory: {base_dir}")
        
        # 确保基础目录存在
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            print(f"Created base directory: {base_dir}")
        
        # 构建完整路径
        full_path = os.path.join(base_dir, file_path)
        print(f"Full path: {full_path}")
        
        # 获取目录内容
        items = []
        for item in os.listdir(full_path):
            # 跳过隐藏文件和目录（以.开头的文件和目录）
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(full_path, item)
            print(f"Processing item: {item_path}")
            
            # 获取相对路径
            rel_path = os.path.relpath(item_path, base_dir)
            print(f"Relative path: {rel_path}")
            
            # 构建树节点
            node = {
                'id': rel_path,
                'text': item,
                'type': 'folder' if os.path.isdir(item_path) else 'file',
                'children': os.path.isdir(item_path)
            }
            print(f"Created node: {node}")
            items.append(node)
        
        # 按文件夹在前，文件在后的顺序排序
        items.sort(key=lambda x: (x['type'] != 'folder', x['text'].lower()))
        print(f"Final items: {items}")
        
        return items
    except Exception as e:
        print(f"Error in get_directory_tree: {str(e)}")
        return []

def get_file_content(file_path):
    # Implementation of get_file_content function
    pass

def save_file_grade(file_path, grade):
    # Implementation of save_file_grade function
    pass
