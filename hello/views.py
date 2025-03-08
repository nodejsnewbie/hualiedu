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

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    return HttpResponse("Hello, World!")


def grading_page(request):
    try:
        # 确保 media 目录存在
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        if request.method == 'POST':
            try:
                action = request.POST.get('action')
                file_path = request.POST.get('file_path')
                
                if not file_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': '未提供文件路径'
                    })
                
                if action == 'get_directory_tree':
                    try:
                        if not os.path.exists(file_path):
                            logger.warning(f'路径不存在: {file_path}')
                            return JsonResponse({'status': 'error', 'message': '路径不存在'})
                        
                        structure = get_directory_structure(file_path)
                        return JsonResponse({'status': 'success', 'children': structure['children']})
                    except Exception as e:
                        logger.error(f'获取目录结构失败: {str(e)}')
                        return JsonResponse({'status': 'error', 'message': str(e)})
                
                elif action == 'get_content':
                    try:
                        if not os.path.exists(file_path):
                            logger.warning(f'文件不存在: {file_path}')
                            return JsonResponse({
                                'status': 'error',
                                'message': '文件不存在'
                            })
                        
                        if not os.path.isfile(file_path):
                            return JsonResponse({
                                'status': 'error',
                                'message': '不是有效的文件'
                            })
                        
                        # 检查文件类型
                        mime_type, _ = mimetypes.guess_type(file_path)
                        content = ''
                        
                        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                            try:
                                def handle_image(image):
                                    with image.open() as image_bytes:
                                        encoded_image = base64.b64encode(image_bytes.read()).decode('utf-8')
                                        image_type = image.content_type or 'image/png'
                                        return {
                                            "src": f"data:{image_type};base64,{encoded_image}"
                                        }

                                # 使用单行字符串形式的style_map
                                style_map = """
p[style-name='Title'] => h1:fresh
p[style-name='Heading 1'] => h2:fresh
p[style-name='Heading 2'] => h3:fresh
p[style-name='Heading 3'] => h4:fresh
"""

                                with open(file_path, 'rb') as docx_file:
                                    result = mammoth.convert_to_html(
                                        docx_file,
                                        convert_image=mammoth.images.inline(handle_image),
                                        style_map=style_map
                                    )
                                    content = result.value

                                if not content.strip():
                                    logger.warning(f'Word文档为空: {file_path}')
                                    return JsonResponse({
                                        'status': 'error',
                                        'message': 'Word文档为空或不包含内容'
                                    })

                            except Exception as e:
                                logger.error(f'Word文档读取失败: {str(e)}')
                                return JsonResponse({
                                    'status': 'error',
                                    'message': f'Word文档读取失败: {str(e)}'
                                })
                        else:
                            # 尝试以不同编码读取文本文件
                            encodings = ['utf-8', 'gbk', 'gb2312', 'ascii']
                            for encoding in encodings:
                                try:
                                    with open(file_path, 'r', encoding=encoding) as f:
                                        content = f.read()
                                    break
                                except UnicodeDecodeError:
                                    continue
                            
                            if not content:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': '不支持的文件格式或编码'
                                })
                        
                        return JsonResponse({
                            'status': 'success',
                            'content': content
                        })
                    except Exception as e:
                        logger.error(f'读取文件失败: {str(e)}')
                        return JsonResponse({
                            'status': 'error',
                            'message': f'读取文件失败: {str(e)}'
                        })
                
                elif action == 'save_grade':
                    try:
                        grade = request.POST.get('grade')
                        if not grade:
                            return JsonResponse({
                                'status': 'error',
                                'message': '未提供评分'
                            })
                        
                        # 保存评分逻辑
                        grade_path = os.path.join(settings.MEDIA_ROOT, 'grades')
                        os.makedirs(grade_path, exist_ok=True)
                        
                        target_file = os.path.join(grade_path, os.path.basename(file_path) + '.grade')
                        temp_file = target_file + '.tmp'
                        
                        try:
                            # 使用文件锁保证并发安全
                            import fcntl
                            with open(temp_file, 'w') as f:
                                fcntl.flock(f, fcntl.LOCK_EX)
                                f.write(grade)
                                f.flush()
                            # 原子替换操作
                            os.replace(temp_file, target_file)
                            logger.info(f'评分保存成功: {target_file} 分数: {grade}')
                        except Exception as e:
                            logger.error(f'评分保存失败: {str(e)}，文件路径: {target_file}')
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                            raise e
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
                        
                        return JsonResponse({
                            'status': 'success',
                            'message': '评分已保存'
                        })
                    except Exception as e:
                        logger.error(f'保存评分失败: {str(e)}')
                        return JsonResponse({
                            'status': 'error',
                            'message': f'保存评分失败: {str(e)}'
                        })
                
                elif action == 'upload_directory':
                    try:
                        files = request.FILES.getlist('files')
                        directory_path = request.POST.get('directory_path', 'uploads')
                        target_dir = os.path.join(settings.MEDIA_ROOT, directory_path)
                        
                        os.makedirs(target_dir, exist_ok=True)
                        
                        for uploaded_file in files:
                            file_path = os.path.join(target_dir, uploaded_file.name)
                            with open(file_path, 'wb+') as destination:
                                for chunk in uploaded_file.chunks():
                                    destination.write(chunk)
                        
                        return JsonResponse({
                            'status': 'success',
                            'message': '目录上传成功',
                            'directory_structure': get_directory_structure(target_dir)
                        })
                    except Exception as e:
                        logger.error(f'上传目录失败: {str(e)}')
                        return JsonResponse({
                            'status': 'error',
                            'message': f'上传目录失败: {str(e)}'
                        })
                
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': '无效的操作'
                    })
            
            except Exception as e:
                logger.error(f'请求处理失败: {str(e)}')
                return JsonResponse({
                    'status': 'error',
                    'message': f'请求处理失败: {str(e)}'
                })
        
        # GET 请求返回页面
        context = {
            'upload_path': os.path.join(settings.MEDIA_ROOT)
        }
        return render(request, 'grading.html', context)
    
    except Exception as e:
        logger.error(f'服务器错误: {str(e)}')
        return JsonResponse({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
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
