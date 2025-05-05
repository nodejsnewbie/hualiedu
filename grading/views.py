import logging
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
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

# 在文件开头添加缓存字典
directory_file_count_cache = {}

def get_directory_file_count_cached(dir_path):
    """获取目录文件数量（带缓存）"""
    logger.info(f'开始统计目录文件数量: {dir_path}')
    
    if dir_path in directory_file_count_cache:
        logger.info(f'使用缓存的文件数量: {directory_file_count_cache[dir_path]}')
        return directory_file_count_cache[dir_path]
    
    try:
        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config or not config.repo_base_dir:
            logger.error('未配置仓库基础目录')
            return 0
            
        # 展开路径中的用户目录符号（~）
        base_dir = os.path.expanduser(config.repo_base_dir)
        full_path = os.path.join(base_dir, dir_path)
        
        logger.info(f'基础目录: {base_dir}')
        logger.info(f'完整路径: {full_path}')
        
        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
            logger.error(f'路径不在基础目录内: {full_path}')
            return 0
            
        if not os.path.exists(full_path):
            logger.error(f'目录不存在: {full_path}')
            return 0
            
        if not os.path.isdir(full_path):
            logger.error(f'不是目录: {full_path}')
            return 0
            
        # 统计.docx文件
        file_count = 0
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isfile(item_path) and item.lower().endswith('.docx'):
                file_count += 1
                logger.info(f'找到文件: {item}')
        
        logger.info(f'目录 {dir_path} 中共有 {file_count} 个 .docx 文件')
        
        # 缓存结果
        directory_file_count_cache[dir_path] = file_count
        return file_count
        
    except Exception as e:
        logger.error(f'统计目录文件数量失败: {str(e)}\n{traceback.format_exc()}')
        return 0

def clear_directory_file_count_cache():
    """清除目录文件数量缓存"""
    directory_file_count_cache.clear()

def index(request):
    return render(request, 'index.html')


@login_required
@require_http_methods(["POST"])
def get_dir_file_count(request):
    """获取目录中文件数量的视图函数"""
    try:
        # 解析请求数据
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            elif request.content_type == 'application/x-www-form-urlencoded':
                data = request.POST
            else:
                return HttpResponse('不支持的Content-Type', status=400)
        except json.JSONDecodeError:
            return HttpResponse('无效的JSON数据', status=400)
        
        # 获取目录路径
        dir_path = data.get('path')
        logger.info(f'统计目录: {str(dir_path)}')
        if not dir_path:
            return HttpResponse('缺少path参数', status=400)
        
        # 使用缓存获取文件数量
        file_count = get_directory_file_count_cached(dir_path)
        
        # 直接返回文件数量字符串
        return HttpResponse(str(file_count))
        
    except Exception as e:
        logger.error(f'获取目录文件数量出错: {str(e)}\n{traceback.format_exc()}')
        return HttpResponse('服务器错误', status=500)


@login_required
@require_http_methods(["GET", "POST"])
def grading_page(request):
    """评分页面视图"""
    try:
        logger.info('开始处理评分页面请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return HttpResponseForbidden('请先登录')
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return HttpResponseForbidden('无权限访问')
        
        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
            logger.info("Created new GlobalConfig with default repo_base_dir")
        
        base_dir = os.path.expanduser(config.repo_base_dir)
        logger.info(f"Base directory: {base_dir}")
        
        # 检查目录权限
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            logger.info(f"Created base directory: {base_dir}")
        
        if not os.access(base_dir, os.R_OK):
            logger.error(f"No read permission for directory: {base_dir}")
            return HttpResponseForbidden('无权限访问目录')
        
        # 获取目录树
        try:
            initial_tree_data = get_directory_tree()
            logger.info(f"Successfully retrieved initial directory tree")
            logger.info(f"Initial tree data: {json.dumps(initial_tree_data, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"Error getting directory tree: {str(e)}\n{traceback.format_exc()}")
            return render(request, 'grading.html', {
                'files': [],
                'error': f'获取目录树失败: {str(e)}',
                'config': config,
                'base_dir': base_dir,
                'initial_tree_data': '[]'
            })
        
        return render(request, 'grading.html', {
            'files': [],
            'error': None,
            'config': config,
            'base_dir': base_dir,
            'initial_tree_data': json.dumps(initial_tree_data, ensure_ascii=False)
        })
        
    except Exception as e:
        logger.error(f'处理评分页面请求失败: {str(e)}\n{traceback.format_exc()}')
        return render(request, 'grading.html', {
            'files': [],
            'error': f'处理请求失败: {str(e)}',
            'config': config if 'config' in locals() else None,
            'base_dir': base_dir if 'base_dir' in locals() else None,
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
        config = GlobalConfig.objects.first()
        if not config:
            config = GlobalConfig.objects.create(repo_base_dir='~/jobs')
            logger.info("Created new GlobalConfig with default repo_base_dir")
        
        base_dir = os.path.expanduser(config.repo_base_dir)
        logger.info(f"Base directory: {base_dir}")
        
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            logger.info(f"Created base directory: {base_dir}")
        
        # 检查目录权限
        if not os.access(base_dir, os.R_OK):
            error_msg = f"No read permission for directory: {base_dir}"
            logger.error(error_msg)
            return []
        
        # 构建完整路径
        full_path = os.path.join(base_dir, file_path)
        logger.info(f"Getting directory tree for path: {full_path}")
        
        # 检查路径是否存在
        if not os.path.exists(full_path):
            error_msg = f"Path does not exist: {full_path}"
            logger.error(error_msg)
            return []
        
        # 检查路径权限
        if not os.access(full_path, os.R_OK):
            error_msg = f"No read permission for path: {full_path}"
            logger.error(error_msg)
            return []
        
        items = []
        try:
            # 获取目录内容并过滤掉隐藏文件和目录
            for item in sorted(os.listdir(full_path)):
                # 跳过隐藏文件和目录
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(full_path, item)
                relative_path = os.path.join(file_path, item)
                
                # 检查项目权限
                if not os.access(item_path, os.R_OK):
                    logger.warning(f"No read permission for item: {item_path}")
                    continue
                
                # 获取项目状态
                is_dir = os.path.isdir(item_path)
                
                # 构建节点数据
                node = {
                    'id': relative_path,
                    'text': item,
                    'type': 'folder' if is_dir else 'file',
                    'icon': 'jstree-folder' if is_dir else 'jstree-file',
                    'state': {
                        'opened': False,
                        'disabled': False,
                        'selected': False
                    }
                }
                
                # 如果是目录，递归获取子目录并统计文件数量
                if is_dir:
                    children = get_directory_tree(relative_path)
                    if children:
                        node['children'] = children
                    else:
                        node['children'] = []
                        node['state']['disabled'] = True
                    
                    # 统计并缓存目录文件数量
                    file_count = get_directory_file_count_cached(relative_path)
                    node['data'] = {
                        'file_count': file_count
                    }
                # 如果是文件，添加文件特定的属性
                else:
                    # 获取文件扩展名
                    _, ext = os.path.splitext(item)
                    node['a_attr'] = {
                        'href': '#',
                        'data-type': 'file',
                        'data-ext': ext.lower()
                    }
                
                items.append(node)
                logger.info(f"Added {'directory' if is_dir else 'file'}: {item}")
            
            # 按类型和名称排序：目录在前，文件在后
            items.sort(key=lambda x: (x['type'] == 'file', x['text'].lower()))
            
            logger.info(f"Successfully generated directory tree for path: {full_path}")
            logger.info(f"Found {len(items)} items")
            return items
            
        except Exception as e:
            error_msg = f"Error listing directory contents: {str(e)}"
            logger.error(error_msg)
            return []
            
    except Exception as e:
        error_msg = f"Error in get_directory_tree: {str(e)}"
        logger.error(error_msg)
        return []

def get_file_content(file_path):
    # Implementation of get_file_content function
    pass

def save_file_grade(file_path, grade):
    # Implementation of save_file_grade function
    pass

@login_required
@require_http_methods(["GET"])
def get_template_list(request):
    """获取模板列表"""
    try:
        logger.info('开始处理获取模板列表请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return JsonResponse({
                'code': 403,
                'msg': 'permission error',
                'error': 'exceptions.UserAuthError'
            }, status=403)
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return JsonResponse({
                'code': 403,
                'msg': 'permission error',
                'error': 'exceptions.UserAuthError'
            }, status=403)
        
        # 获取全局配置
        config = GlobalConfig.objects.first()
        if not config:
            logger.error('未找到全局配置')
            return JsonResponse({
                'code': 500,
                'msg': 'configuration error',
                'error': 'exceptions.ConfigError'
            }, status=500)
        
        # 获取模板目录路径
        template_dir = os.path.join(settings.BASE_DIR, 'templates', 'writing')
        logger.info(f'模板目录路径: {template_dir}')
        
        # 检查目录是否存在
        if not os.path.exists(template_dir):
            logger.info(f'创建模板目录: {template_dir}')
            os.makedirs(template_dir, exist_ok=True)
        
        # 获取模板列表
        templates = []
        if os.path.exists(template_dir):
            for item in os.listdir(template_dir):
                if item.endswith('.docx'):
                    template_path = os.path.join(template_dir, item)
                    templates.append({
                        'name': item,
                        'path': template_path,
                        'size': os.path.getsize(template_path),
                        'modified': os.path.getmtime(template_path)
                    })
        
        logger.info(f'找到 {len(templates)} 个模板')
        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': templates
        })
        
    except Exception as e:
        logger.error(f'获取模板列表失败: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({
            'code': 500,
            'msg': str(e),
            'error': 'exceptions.ServerError'
        }, status=500)

@login_required
@require_http_methods(['POST'])
def get_file_content(request):
    """获取文件内容"""
    try:
        logger.info('开始处理获取文件内容请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return JsonResponse({
                'status': 'error',
                'message': '请先登录'
            }, status=403)
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return JsonResponse({
                'status': 'error',
                'message': '无权限访问'
            }, status=403)
        
        # 获取文件路径
        path = request.POST.get('path')
        if not path:
            logger.error('未提供文件路径')
            return JsonResponse({
                'status': 'error',
                'message': '未提供文件路径'
            })
        
        logger.info(f'请求获取文件内容，路径: {path}')
        
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
        
        # 检查文件权限
        if not os.access(full_path, os.R_OK):
            logger.error(f'无权限读取文件: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '无权限读取文件'
            })
        
        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()
        
        # 根据文件类型处理内容
        if ext == '.docx':
            # 使用 mammoth 将 Word 文档转换为 HTML
            with open(full_path, 'rb') as f:
                result = mammoth.convert_to_html(f)
                html = result.value
                messages = result.messages
                
                # 添加样式
                html = f'''
                <div class="word-document">
                    <style>
                        .word-document {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            padding: 20px;
                        }}
                        .word-document p {{
                            margin: 0 0 1em 0;
                        }}
                        .word-document h1, .word-document h2, .word-document h3 {{
                            margin: 1em 0 0.5em 0;
                        }}
                    </style>
                    {html}
                </div>
                '''
                return JsonResponse({
                    'status': 'success',
                    'content': html,
                    'type': 'docx'
                })
                
        elif ext == '.pdf':
            # 返回 PDF 文件的 URL
            pdf_url = reverse('grading:serve_file', args=[path])
            return JsonResponse({
                'status': 'success',
                'content': pdf_url,
                'type': 'pdf'
            })
            
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            # 返回图片文件的 URL
            image_url = reverse('grading:serve_file', args=[path])
            return JsonResponse({
                'status': 'success',
                'content': image_url,
                'type': 'image'
            })
            
        else:
            # 对于其他文本文件，尝试以文本方式读取
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return JsonResponse({
                    'status': 'success',
                    'content': content,
                    'type': 'text'
                })
            except UnicodeDecodeError:
                # 如果无法以文本方式读取，返回二进制文件提示
                return JsonResponse({
                    'status': 'success',
                    'content': '二进制文件内容无法直接显示',
                    'type': 'binary'
                })
            
    except Exception as e:
        logger.error(f'读取文件失败: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_http_methods(['POST'])
def add_grade_to_file(request):
    """添加评分到文件末尾"""
    try:
        logger.info('开始处理添加评分到文件请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return JsonResponse({
                'status': 'error',
                'message': '请先登录'
            }, status=403)
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return JsonResponse({
                'status': 'error',
                'message': '无权限访问'
            }, status=403)
        
        # 获取文件路径和评分
        path = request.POST.get('path')
        grade = request.POST.get('grade')
        
        if not path or not grade:
            logger.error('未提供文件路径或评分')
            return JsonResponse({
                'status': 'error',
                'message': '未提供文件路径或评分'
            })
        
        logger.info(f'请求添加评分到文件，路径: {path}, 评分: {grade}')
        
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
        
        logger.info(f'尝试修改文件: {full_path}')
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f'文件不存在: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '文件不存在'
            })
        
        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f'无权限修改文件: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '无权限修改文件'
            })
        
        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()
        
        # 根据文件类型处理
        if ext == '.docx':
            # 对于 Word 文档，使用 python-docx 添加评分
            try:
                doc = Document(full_path)
                
                # 检查最后一段是否已经是评分
                if doc.paragraphs and doc.paragraphs[-1].text.startswith('老师评分：'):
                    # 如果是评分，则删除它
                    doc._body._body.remove(doc.paragraphs[-1]._p)
                
                # 添加一个空段落
                doc.add_paragraph()
                # 添加评分段落
                doc.add_paragraph(f'老师评分：{grade}')
                # 保存文档
                doc.save(full_path)
                logger.info(f'成功添加评分到 Word 文档: {full_path}')
                return JsonResponse({
                    'status': 'success',
                    'message': '评分已添加到文件末尾',
                    'file_type': 'docx'
                })
            except Exception as e:
                logger.error(f'添加评分到 Word 文档失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'添加评分到 Word 文档失败: {str(e)}'
                })
        else:
            # 对于其他文件，尝试以文本方式添加
            try:
                with open(full_path, 'r+', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 检查最后一行是否已经是评分
                    if lines and lines[-1].strip().startswith('老师评分：'):
                        # 如果是评分，则删除它
                        lines = lines[:-1]
                    
                    # 移动到文件末尾
                    f.seek(0)
                    f.truncate()
                    
                    # 写入所有行（除了最后一个评分）
                    f.writelines(lines)
                    
                    # 添加新行和评分
                    f.write(f'\n老师评分：{grade}\n')
                
                logger.info(f'成功添加评分到文件: {full_path}')
                return JsonResponse({
                    'status': 'success',
                    'message': '评分已添加到文件末尾',
                    'file_type': 'text'
                })
            except Exception as e:
                logger.error(f'添加评分到文件失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'添加评分到文件失败: {str(e)}'
                })
            
    except Exception as e:
        logger.error(f'添加评分到文件失败: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_http_methods(['POST'])
def save_grade(request):
    """保存评分"""
    try:
        logger.info('开始处理保存评分请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return JsonResponse({
                'status': 'error',
                'message': '请先登录'
            }, status=403)
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return JsonResponse({
                'status': 'error',
                'message': '无权限访问'
            }, status=403)
        
        # 获取文件路径和评分
        path = request.POST.get('path')
        grade = request.POST.get('grade')
        
        if not path or not grade:
            logger.error('未提供文件路径或评分')
            return JsonResponse({
                'status': 'error',
                'message': '未提供文件路径或评分'
            })
        
        logger.info(f'请求保存评分，路径: {path}, 评分: {grade}')
        
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
        
        logger.info(f'尝试修改文件: {full_path}')
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f'文件不存在: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '文件不存在'
            })
        
        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f'无权限修改文件: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '无权限修改文件'
            })
        
        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()
        
        # 根据文件类型处理
        if ext == '.docx':
            # 对于 Word 文档，使用 python-docx 添加评分
            try:
                doc = Document(full_path)
                # 添加一个空段落
                doc.add_paragraph()
                # 添加评分段落
                doc.add_paragraph(f'老师评分：{grade}')
                # 保存文档
                doc.save(full_path)
                logger.info(f'成功添加评分到 Word 文档: {full_path}')
                return JsonResponse({
                    'status': 'success',
                    'message': '评分已保存',
                    'file_type': 'docx'
                })
            except Exception as e:
                logger.error(f'添加评分到 Word 文档失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'添加评分到 Word 文档失败: {str(e)}'
                })
        else:
            # 对于其他文件，尝试以文本方式添加
            try:
                with open(full_path, 'a', encoding='utf-8') as f:
                    f.write(f'\n老师评分：{grade}\n')
                logger.info(f'成功添加评分到文件: {full_path}')
                return JsonResponse({
                    'status': 'success',
                    'message': '评分已保存',
                    'file_type': 'text'
                })
            except Exception as e:
                logger.error(f'添加评分到文件失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'添加评分到文件失败: {str(e)}'
                })
            
    except Exception as e:
        logger.error(f'保存评分失败: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_http_methods(['POST'])
def remove_grade(request):
    """删除文件中的评分"""
    try:
        logger.info('开始处理删除评分请求')
        
        # 检查用户权限
        if not request.user.is_authenticated:
            logger.error('用户未认证')
            return JsonResponse({
                'status': 'error',
                'message': '请先登录'
            }, status=403)
        
        if not request.user.is_staff:
            logger.error('用户无权限')
            return JsonResponse({
                'status': 'error',
                'message': '无权限访问'
            }, status=403)
        
        # 获取文件路径
        path = request.POST.get('path')
        if not path:
            logger.error('未提供文件路径')
            return JsonResponse({
                'status': 'error',
                'message': '未提供文件路径'
            })
        
        logger.info(f'请求删除评分，路径: {path}')
        
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
        
        logger.info(f'尝试修改文件: {full_path}')
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f'文件不存在: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '文件不存在'
            })
        
        # 检查文件权限
        if not os.access(full_path, os.W_OK):
            logger.error(f'无权限修改文件: {full_path}')
            return JsonResponse({
                'status': 'error',
                'message': '无权限修改文件'
            })
        
        # 获取文件扩展名
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()
        
        # 根据文件类型处理
        if ext == '.docx':
            # 对于 Word 文档，使用 python-docx 删除评分
            try:
                doc = Document(full_path)
                
                # 检查最后一段是否是评分
                if doc.paragraphs and doc.paragraphs[-1].text.startswith('老师评分：'):
                    # 如果是评分，则删除它
                    doc._body._body.remove(doc.paragraphs[-1]._p)
                    # 如果前一段是空行，也删除它
                    if doc.paragraphs and not doc.paragraphs[-1].text.strip():
                        doc._body._body.remove(doc.paragraphs[-1]._p)
                    # 保存文档
                    doc.save(full_path)
                    logger.info(f'成功删除 Word 文档中的评分: {full_path}')
                    return JsonResponse({
                        'status': 'success',
                        'message': '评分已删除',
                        'file_type': 'docx'
                    })
                else:
                    logger.info(f'Word 文档中没有找到评分: {full_path}')
                    return JsonResponse({
                        'status': 'success',
                        'message': '文件中没有找到评分',
                        'file_type': 'docx'
                    })
            except Exception as e:
                logger.error(f'删除 Word 文档中的评分失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'删除 Word 文档中的评分失败: {str(e)}'
                })
        else:
            # 对于其他文件，尝试以文本方式删除
            try:
                with open(full_path, 'r+', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 检查最后一行是否是评分
                    if lines and lines[-1].strip().startswith('老师评分：'):
                        # 如果是评分，则删除它
                        lines = lines[:-1]
                        # 如果前一行是空行，也删除它
                        if lines and not lines[-1].strip():
                            lines = lines[:-1]
                        
                        # 移动到文件开头并截断
                        f.seek(0)
                        f.truncate()
                        # 写入剩余内容
                        f.writelines(lines)
                        
                        logger.info(f'成功删除文件中的评分: {full_path}')
                        return JsonResponse({
                            'status': 'success',
                            'message': '评分已删除',
                            'file_type': 'text'
                        })
                    else:
                        logger.info(f'文件中没有找到评分: {full_path}')
                        return JsonResponse({
                            'status': 'success',
                            'message': '文件中没有找到评分',
                            'file_type': 'text'
                        })
            except Exception as e:
                logger.error(f'删除文件中的评分失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'删除文件中的评分失败: {str(e)}'
                })
            
    except Exception as e:
        logger.error(f'删除评分失败: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
