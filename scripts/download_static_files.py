import os
import requests
from pathlib import Path

# 创建必要的目录
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / 'grading' / 'static' / 'grading'

# 确保目录存在
os.makedirs(STATIC_DIR / 'vendor' / 'bootstrap', exist_ok=True)
os.makedirs(STATIC_DIR / 'vendor' / 'jquery', exist_ok=True)
os.makedirs(STATIC_DIR / 'vendor' / 'jstree' / 'themes' / 'default', exist_ok=True)
os.makedirs(STATIC_DIR / 'vendor' / 'bootstrap-icons' / 'font', exist_ok=True)
os.makedirs(STATIC_DIR / 'vendor' / 'codemirror', exist_ok=True)
os.makedirs(STATIC_DIR / 'vendor' / 'viewerjs', exist_ok=True)
os.makedirs(STATIC_DIR / 'css', exist_ok=True)
os.makedirs(STATIC_DIR / 'images', exist_ok=True)

# 要下载的文件列表
files_to_download = {
    'vendor/bootstrap/bootstrap.min.css': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'vendor/bootstrap/bootstrap.min.css.map': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css.map',
    'vendor/bootstrap/bootstrap.bundle.min.js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
    'vendor/bootstrap/bootstrap.bundle.min.js.map': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js.map',
    'vendor/jquery/jquery.min.js': 'https://code.jquery.com/jquery-3.6.0.min.js',
    'vendor/jstree/jstree.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/jstree.min.js',
    'vendor/jstree/themes/default/style.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/style.min.css',
    'vendor/jstree/themes/default/32px.png': 'https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/32px.png',
    'vendor/jstree/themes/default/40px.png': 'https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/40px.png',
    'vendor/jstree/themes/default/throbber.gif': 'https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/throbber.gif',
    'vendor/bootstrap-icons/font/bootstrap-icons.css': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
    'vendor/codemirror/codemirror.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css',
    'vendor/viewerjs/viewer.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.11.1/viewer.min.css',
}

# 下载文件
for local_path, url in files_to_download.items():
    full_path = STATIC_DIR / local_path
    print(f"Downloading {url} to {full_path}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果响应状态码不是 200，将引发异常
        os.makedirs(os.path.dirname(full_path), exist_ok=True)  # 确保目标目录存在
        with open(full_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully downloaded {local_path}")
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")

# 创建自定义CSS文件
custom_css = """
/* 自定义样式 */
.file-count-display {
    position: absolute;
    right: 1rem;
    top: 1rem;
}
"""
with open(STATIC_DIR / 'css' / 'custom.css', 'w') as f:
    f.write(custom_css)
print("Created custom.css")

# 创建favicon
favicon = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
    <path fill="none" d="M0 0h24v24H0z"/>
    <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
</svg>
"""
with open(STATIC_DIR / 'images' / 'favicon.ico', 'w') as f:
    f.write(favicon)
print("Created favicon.ico") 