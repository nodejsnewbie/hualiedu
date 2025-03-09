# 文件类型配置
ALLOWED_FILE_TYPES = {
    'document': {
        'extensions': ['.docx', '.doc', '.txt', '.pdf'],
        'mime_types': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'application/pdf'
        ]
    },
    'image': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif'],
        'mime_types': ['image/jpeg', 'image/png', 'image/gif']
    }
}

# 文件编码配置
FILE_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'ascii']

# Word文档样式映射
WORD_STYLE_MAP = """
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

# 评分等级配置
GRADE_LEVELS = {
    'A': {'range': (90, 100), 'description': '优秀'},
    'B': {'range': (80, 89), 'description': '良好'},
    'C': {'range': (70, 79), 'description': '中等'},
    'D': {'range': (60, 69), 'description': '及格'},
    'E': {'range': (0, 59), 'description': '不及格'}
}

# 目录结构配置
DIRECTORY_STRUCTURE = {
    'root': 'grades',
    'required_subdirs': ['课程', '班级', '作业']
}

# 文件处理配置
FILE_PROCESSING = {
    'chunk_size': 8192,  # 文件上传分块大小
    'max_file_size': 50 * 1024 * 1024,  # 最大文件大小（50MB）
    'image_preview_size': (800, 600)  # 图片预览最大尺寸
}