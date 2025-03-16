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
                logger.info(f'获取目录树请求: {file_path}')
                
                # 处理根节点请求
                if file_path == '#' or not file_path:
                    return JsonResponse({
                        'status': 'success',
                        'children': [{
                            'id': 'media/grades',
                            'text': '作业目录',
                            'type': 'folder',
                            'children': True,
                            'state': {
                                'opened': True
                            }
                        }]
                    })
                
                # 构建完整的文件路径
                full_path = os.path.join(settings.BASE_DIR, file_path)
                logger.info(f'完整路径: {full_path}')
                
                # 检查路径安全性
                if not os.path.exists(full_path):
                    logger.error(f'目录不存在: {full_path}')
                    return JsonResponse({
                        'status': 'error',
                        'message': '目录不存在'
                    })
                
                if not os.path.isdir(full_path):
                    logger.error(f'不是有效的目录: {full_path}')
                    return JsonResponse({
                        'status': 'error',
                        'message': '不是有效的目录'
                    })
                
                grades_dir = os.path.join(settings.BASE_DIR, 'media', 'grades')
                if not os.path.commonpath([full_path, grades_dir]) == grades_dir:
                    logger.error(f'无权访问目录: {full_path}')
                    return JsonResponse({
                        'status': 'error',
                        'message': '无权访问该目录'
                    })
                
                # 获取目录结构
                try:
                    items = []
                    for item in sorted(os.listdir(full_path)):
                        item_path = os.path.join(full_path, item)
                        rel_path = os.path.relpath(item_path, settings.BASE_DIR)
                        is_dir = os.path.isdir(item_path)
                        
                        node = {
                            'id': rel_path,
                            'text': item,
                            'type': 'folder' if is_dir else 'file',
                            'children': is_dir,
                            'icon': 'jstree-folder' if is_dir else 'jstree-file'
                        }
                        items.append(node)
                    
                    logger.info(f'成功获取目录结构，共 {len(items)} 个项目')
                    return JsonResponse({
                        'status': 'success',
                        'children': items
                    })
                except Exception as e:
                    logger.error(f'获取目录结构失败: {str(e)}')
                    return JsonResponse({
                        'status': 'error',
                        'message': f'获取目录结构失败: {str(e)}'
                    })
                
            except Exception as e:
                logger.error(f'获取目录树失败: {str(e)}\n{traceback.format_exc()}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # 处理获取内容请求
        elif action == 'get_content':
            try:
                file_path = request.POST.get('file_path')
                if not file_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未提供文件路径'
                    })

                # 确保文件路径在 media/grades 目录下
                if 'media/grades' not in file_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': '只能查看作业目录下的文件'
                    })
                
                # 构建完整的文件路径
                full_path = os.path.join(settings.BASE_DIR, file_path.lstrip('/'))
                
                # 规范化路径并检查安全性
                normalized_path = os.path.normpath(full_path)
                grades_dir = os.path.join(settings.BASE_DIR, 'media', 'grades')
                if not normalized_path.startswith(grades_dir):
                    return JsonResponse({
                        'status': 'error',
                        'message': '无权访问该文件'
                    })

                if not os.path.exists(normalized_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在'
                    })

                if not os.path.isfile(normalized_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '不是有效的文件'
                    })
                
                # 检查文件类型
                mime_type = FileHandler.get_mime_type(normalized_path)
                if not mime_type:
                    return JsonResponse({
                        'status': 'error',
                        'message': '无法识别的文件类型'
                    })

                content = None
                
                # 处理 Word 文档
                if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    content = FileHandler.handle_docx(normalized_path)
                    if not content:
                        return JsonResponse({
                            'status': 'error',
                            'message': '无法读取 Word 文档内容'
                        })
                # 处理文本文件
                elif mime_type.startswith('text/'):
                    content = FileHandler.read_text_file(normalized_path)
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
