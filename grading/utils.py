import os
import logging
import mimetypes
from django.conf import settings
from .config import ALLOWED_FILE_TYPES, FILE_ENCODINGS, FILE_PROCESSING
import mammoth
import base64

logger = logging.getLogger(__name__)

class FileHandler:
    @staticmethod
    def is_safe_path(path):
        """检查路径是否在允许的范围内"""
        normalized_path = os.path.normpath(path)
        return normalized_path.startswith(os.path.join(settings.BASE_DIR, 'media', 'grades'))

    @staticmethod
    def get_mime_type(file_path):
        """获取文件的MIME类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type

    @staticmethod
    def is_allowed_file(file_path):
        """检查文件类型是否允许"""
        mime_type = FileHandler.get_mime_type(file_path)
        if not mime_type:
            return False
        
        for file_type in ALLOWED_FILE_TYPES.values():
            if mime_type in file_type['mime_types']:
                return True
        return False

    @staticmethod
    def read_text_file(file_path):
        """读取文本文件，尝试不同编码"""
        content = None
        for encoding in FILE_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        return content

    @staticmethod
    def handle_docx(file_path):
        """处理Word文档"""
        try:
            def handle_image(image):
                try:
                    with image.open() as image_bytes:
                        encoded_image = base64.b64encode(image_bytes.read()).decode('utf-8')
                        image_type = image.content_type or 'image/png'
                        return {
                            "src": f"data:{image_type};base64,{encoded_image}"
                        }
                except Exception as e:
                    logger.error(f'图片处理失败: {str(e)}')
                    return {"src": ""}

            with open(file_path, 'rb') as docx_file:
                result = mammoth.convert_to_html(
                    docx_file,
                    convert_image=mammoth.images.img_element(handle_image)
                )
                return result.value
        except Exception as e:
            logger.error(f'Word文档处理失败: {str(e)}')
            return None

class DirectoryHandler:
    @staticmethod
    def ensure_directory(path):
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_directory_structure(root_dir):
        """获取目录结构"""
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
            
            items = sorted(os.listdir(root_dir))
            for item in items:
                path = os.path.join(root_dir, item)
                if os.path.isdir(path):
                    structure['children'].append(DirectoryHandler.get_directory_structure(path))
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
            return structure

class GradeHandler:
    @staticmethod
    def validate_grade(grade):
        """验证评分是否有效"""
        from .config import GRADE_LEVELS
        return grade in GRADE_LEVELS

    @staticmethod
    def get_grade_description(grade):
        """获取评分描述"""
        from .config import GRADE_LEVELS
        return GRADE_LEVELS.get(grade, {}).get('description', '未知') 