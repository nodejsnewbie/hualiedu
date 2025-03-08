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
                
                # 只在需要file_path的操作中检查
                if action in ['get_directory_tree', 'get_content', 'save_grade']:
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
                                    try:
                                        with image.open() as image_bytes:
                                            encoded_image = base64.b64encode(image_bytes.read()).decode('utf-8')
                                            image_type = image.content_type or 'image/png'
                                            logger.info(f'处理图片: {image_type}')
                                            return {
                                                "src": f"data:{image_type};base64,{encoded_image}"
                                            }
                                    except Exception as e:
                                        logger.error(f'图片处理失败: {str(e)}')
                                        return {"src": ""}

                                # 使用更完整的样式映射
                                style_map = """
                                    p[style-name='Title'] => h1:fresh
                                    p[style-name='Heading 1'] => h2:fresh
                                    p[style-name='Heading 2'] => h3:fresh
                                    p[style-name='Heading 3'] => h4:fresh
                                    p[style-name='Normal'] => p:fresh
                                    r[style-name='Strong'] => strong
                                    r[style-name='Emphasis'] => em
                                    table => table
                                    tr => tr
                                    td => td
                                """

                                with open(file_path, 'rb') as docx_file:
                                    logger.info(f'开始转换Word文档: {file_path}')
                                    result = mammoth.convert_to_html(
                                        docx_file,
                                        convert_image=mammoth.images.img_element(handle_image),
                                        style_map=style_map
                                    )
                                    content = result.value

                                    # 记录转换过程中的消息
                                    if result.messages:
                                        for message in result.messages:
                                            logger.info(f'Mammoth转换消息: {message}')

                                    # 添加基本样式和包装容器
                                    content = f"""
                                    <div class="word-content" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                        {content}
                                    </div>
                                    """

                                    logger.info(f'转换后的HTML长度: {len(content)}')
                                    logger.info(f'HTML内容预览: {content[:200]}...')  # 只记录前200个字符

                                if not content.strip():
                                    logger.warning(f'Word文档为空: {file_path}')
                                    return JsonResponse({
                                        'status': 'error',
                                        'message': 'Word文档为空或不包含内容'
                                    })

                                return JsonResponse({
                                    'status': 'success',
                                    'content': content
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
                        # TODO: 实现评分保存
                        
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
                        if not files:
                            logger.error('没有接收到文件')
                            return JsonResponse({
                                'status': 'error',
                                'message': '没有接收到文件'
                            })

                        logger.info(f'接收到 {len(files)} 个文件')
                        
                        # 获取目标目录名
                        directory_name = request.POST.get('directory_name')
                        logger.info(f'目录名: {directory_name}')
                        
                        if not directory_name:
                            logger.error('未提供目录名')
                            return JsonResponse({
                                'status': 'error',
                                'message': '未提供目录名'
                            })

                        # 确保上传目录存在
                        upload_dir = os.path.join(settings.MEDIA_ROOT, directory_name)
                        os.makedirs(upload_dir, exist_ok=True)
                        logger.info(f'创建目录: {upload_dir}')

                        uploaded_files = []
                        # 处理每个文件
                        for uploaded_file in files:
                            try:
                                # 获取文件的相对路径
                                file_path = str(uploaded_file)
                                logger.info(f'处理文件: {file_path}')
                                
                                # 从完整路径中提取相对路径
                                if '/' in file_path:
                                    relative_path = '/'.join(file_path.split('/')[1:])  # 跳过第一个目录名
                                elif '\\' in file_path:
                                    relative_path = '\\'.join(file_path.split('\\')[1:])  # 跳过第一个目录名
                                else:
                                    relative_path = file_path

                                logger.info(f'相对路径: {relative_path}')
                                
                                # 构建目标路径
                                target_path = os.path.join(upload_dir, relative_path)
                                if os.path.dirname(target_path):
                                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                                logger.info(f'保存文件到: {target_path}')

                                # 写入文件
                                with open(target_path, 'wb+') as destination:
                                    for chunk in uploaded_file.chunks():
                                        destination.write(chunk)
                                
                                uploaded_files.append(target_path)
                                logger.info(f'文件上传成功: {target_path}')
                            except Exception as e:
                                logger.error(f'处理文件 {uploaded_file} 时出错: {str(e)}')
                                return JsonResponse({
                                    'status': 'error',
                                    'message': f'处理文件 {uploaded_file} 时出错: {str(e)}'
                                })

                        return JsonResponse({
                            'status': 'success',
                            'message': f'成功上传 {len(files)} 个文件到 {directory_name}',
                            'uploaded_files': uploaded_files
                        })

                    except Exception as e:
                        logger.error(f'上传目录失败: {str(e)}')
                        return JsonResponse({
                            'status': 'error',
                            'message': f'上传失败: {str(e)}'
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
