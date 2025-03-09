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
from .utils import FileHandler, DirectoryHandler, GradeHandler
from .config import WORD_STYLE_MAP, DIRECTORY_STRUCTURE

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
                    parent_path = data.get('parent_path')
                    directory_name = data.get('directory_name')
                    
                    # 构建新目录的完整路径
                    new_dir_path = os.path.join(settings.BASE_DIR, parent_path.lstrip('/'), directory_name)
                    
                    # 检查路径安全性
                    if not FileHandler.is_safe_path(new_dir_path):
                        return JsonResponse({
                            'status': 'error',
                            'message': '无效的目录路径'
                        })
                    
                    # 创建目录
                    DirectoryHandler.ensure_directory(new_dir_path)
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': '目录创建成功'
                    })
                except Exception as e:
                    logger.error(f'创建目录失败: {str(e)}')
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
                file_path = request.POST.get('file_path')
                
                # 处理根节点请求
                if file_path == '#':
                    return JsonResponse({
                        'status': 'success',
                        'children': [{
                            'id': '/media/grades',
                            'text': DIRECTORY_STRUCTURE['root'],
                            'type': 'folder',
                            'children': True,
                            'state': {
                                'opened': True
                            }
                        }]
                    })
                
                # 处理子节点请求
                base_path = os.path.join(settings.BASE_DIR, file_path.lstrip('/'))
                structure = DirectoryHandler.get_directory_structure(base_path)
                
                return JsonResponse({
                    'status': 'success',
                    'children': structure.get('children', [])
                })
            except Exception as e:
                logger.error(f'获取目录树失败: {str(e)}')
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
                
                # 构建完整的文件路径
                full_path = os.path.join(settings.BASE_DIR, file_path.lstrip('/'))
                
                if not os.path.exists(full_path) or not os.path.isfile(full_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': '文件不存在或不是有效的文件'
                    })
                
                # 检查文件类型
                mime_type = FileHandler.get_mime_type(full_path)
                content = None
                
                if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    content = FileHandler.handle_docx(full_path)
                    if content:
                        content = f"""
                        <div class="word-content" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            {content}
                        </div>
                        """
                else:
                    content = FileHandler.read_text_file(full_path)
                
                if not content:
                    return JsonResponse({
                        'status': 'error',
                        'message': '无法读取文件内容'
                    })
                
                return JsonResponse({
                    'status': 'success',
                    'content': content
                })
            except Exception as e:
                logger.error(f'读取文件失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
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
        
        for item in sorted(os.listdir(root_dir)):
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
