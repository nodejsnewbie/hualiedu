// 全局变量
let currentFile = '';
let selectedGrade = 'B';  // 设置默认评分为 B
var currentFilePath = null;
let pendingGrade = null;  // 待确认的评分

// 获取 CSRF Token
function getCSRFToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// 显示错误信息
function showError(message) {
  const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
  $('#file-content').html(alertHtml);
}

// 显示加载指示器
function showLoading() {
  $('#loading').show();
}

// 隐藏加载指示器
function hideLoading() {
  $('#loading').hide();
}

// 设置评分按钮状态
function setGradeButtonState(grade) {
  $('.grade-button').removeClass('active');
  $(`.grade-button[data-grade="${grade}"]`).addClass('active');
  selectedGrade = grade;
}

// 处理文件内容显示
function handleFileContent(response) {
    if (response.status === 'success') {
        const fileContent = $('#file-content');
        fileContent.empty();

        switch (response.type) {
            case 'text':
                // 文本文件
                fileContent.html(`<pre class="border p-3 bg-light">${response.content}</pre>`);
                break;
            case 'image':
                // 图片文件
                fileContent.html(`<img src="${response.content}" class="img-fluid" alt="图片">`);
                break;
            case 'pdf':
                // PDF 文件
                fileContent.html(`<iframe src="${response.content}" class="w-100" style="height: 800px;"></iframe>`);
                break;
            case 'excel':
                // Excel 文件
                try {
                    // 直接显示后端返回的 HTML 表格
                    fileContent.html(response.content);
                } catch (error) {
                    console.error('Error displaying Excel content:', error);
                    fileContent.html('<div class="alert alert-danger">无法显示 Excel 内容</div>');
                }
                break;
            case 'docx':
                // Word 文档
                try {
                    console.log('Displaying Word document content:', response.content);
                    fileContent.html(response.content);
                } catch (error) {
                    console.error('Error displaying Word content:', error);
                    fileContent.html('<div class="alert alert-danger">无法显示 Word 文档内容</div>');
                }
                break;
            case 'binary':
                // 二进制文件，提供下载链接
                fileContent.html(`
                    <div class="alert alert-info">
                        <i class="bi bi-download"></i> 
                        <a href="${response.content}" class="alert-link" download>点击下载文件</a>
                    </div>
                `);
                break;
            default:
                fileContent.html('<div class="alert alert-warning">不支持的文件类型</div>');
        }
    } else {
        $('#file-content').html(`<div class="alert alert-danger">${response.message}</div>`);
    }
}

// 加载文件内容
function loadFile(path) {
    console.log('Loading file:', path);
    showLoading();
    currentFilePath = path;
    
    // 获取当前文件所在目录
    const dirPath = path.substring(0, path.lastIndexOf('/'));
    if (!dirPath) {
        console.error('Invalid directory path');
        $('#directory-file-count').text('0');
        return;
    }

    console.log('Current directory path:', dirPath);
    console.log('Current file path:', currentFilePath);

    // 尝试从目录树中获取缓存的文件数量
    const tree = $('#directory-tree').jstree(true);
    const node = tree.get_node(dirPath);
    console.log('Directory node:', node);

    if (node && node.data && node.data.file_count !== undefined) {
        console.log('Using cached file count:', node.data.file_count);
        $('#directory-file-count').text(node.data.file_count);
    } else {
        // 如果没有缓存，则从服务器获取
        console.log('No cached file count, fetching from server');
        
        // 准备请求数据
        const requestData = {
            path: dirPath
        };
        console.log('Request data:', requestData);

        // 获取CSRF Token
        const csrfToken = getCSRFToken();
        console.log('CSRF Token:', csrfToken);

        $.ajax({
            url: '/grading/get_dir_file_count/',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json; charset=utf-8'
            },
            data: JSON.stringify(requestData),
            processData: false,
            contentType: 'application/json; charset=utf-8',
            success: function(response) {
                console.log('Response:', response);
                console.log('Response type:', typeof response);
                console.log('Response text:', response);
                
                // 直接使用响应文本作为文件数量
                const fileCount = response;
                console.log('Setting file count to:', fileCount);
                $('#directory-file-count').text(fileCount);
                console.log(`Found ${fileCount} files in directory: ${dirPath}`);
                
                // 更新目录树中的缓存
                if (node) {
                    node.data = node.data || {};
                    node.data.file_count = fileCount;
                    tree.redraw_node(node);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error getting file count:', error);
                console.error('XHR status:', xhr.status);
                console.error('XHR response:', xhr.responseText);
                console.error('XHR status text:', xhr.statusText);
                console.error('XHR ready state:', xhr.readyState);
                $('#directory-file-count').text('0');
                showError('获取文件数量失败');
            }
        });
    }

    // 添加超时处理
    const timeout = setTimeout(() => {
        hideLoading();
        showError('加载文件超时，请重试');
    }, 30000); // 30秒超时

    $.ajax({
        url: '/grading/get_file_content/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: {
            path: path
        },
        success: function(response) {
            clearTimeout(timeout);
            console.log('File content response:', response);
            handleFileContent(response);
        },
        error: function(xhr, status, error) {
            clearTimeout(timeout);
            console.error('Error loading file:', error);
            console.error('XHR status:', xhr.status);
            console.error('XHR response:', xhr.responseText);
            showError('加载文件失败：' + (error || '未知错误'));
        },
        complete: function() {
            clearTimeout(timeout);
            hideLoading();
        }
    });
}

// 保存评分
function saveGrade(grade) {
    console.log('Saving grade:', grade);
    if (!currentFilePath) {
        showError('请先选择要评分的文件');
        return;
    }

    // 更新按钮状态
    setGradeButtonState(grade);
    // 保存当前选中的评分
    selectedGrade = grade;
    // 直接调用 addGradeToFile 进行评分并切换下一个文件
    addGradeToFile(grade);
}

// 获取所有文件节点
function getAllFileNodes() {
    const tree = $('#directory-tree').jstree(true);
    const allNodes = tree.get_json('#', { flat: true });
    return allNodes.filter(node => node.type === 'file');
}

// 获取当前文件在文件列表中的索引
function getCurrentFileIndex() {
    const fileNodes = getAllFileNodes();
    const currentFile = $('#directory-tree').jstree('get_selected', true)[0];
    if (!currentFile) return -1;
    return fileNodes.findIndex(node => node.id === currentFile.id);
}

// 导航到上一个文件
$('#prev-file').on('click', function() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();
    
    if (currentIndex > 0) {
        const prevNode = fileNodes[currentIndex - 1];
        $('#directory-tree').jstree('select_node', prevNode.id);
    }
});

// 导航到下一个文件
$('#next-file').on('click', function() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();
    
    if (currentIndex < fileNodes.length - 1) {
        const nextNode = fileNodes[currentIndex + 1];
        $('#directory-tree').jstree('select_node', nextNode.id);
    }
});

// 更新导航按钮状态
function updateNavigationButtons() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();
    
    $('#prev-file').prop('disabled', currentIndex <= 0);
    $('#next-file').prop('disabled', currentIndex >= fileNodes.length - 1);
}

// 在文件选择时更新导航按钮状态
$('#directory-tree').on('select_node.jstree', function(e, data) {
    if (data.node.type === 'file') {
        updateNavigationButtons();
    }
});

// 修改addGradeToFile函数，在评分后自动导航到下一个文件
function addGradeToFile(grade) {
    console.log('Adding grade to file:', grade);
    console.log('Current file path:', currentFilePath);
    
    if (!currentFilePath) {
        showError('请先选择要评分的文件');
        return;
    }

    if (!grade) {
        showError('请先选择一个评分');
        return;
    }

    showLoading();
    $.ajax({
        url: '/grading/add_grade_to_file/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: {
            path: currentFilePath,
            grade: grade
        },
        success: function(response) {
            console.log('Grade added successfully:', response);
            if (response.status === 'success') {
                const alertHtml = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        评分已添加到文件末尾
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                $('#file-content').prepend(alertHtml);
                
                // 获取所有文件节点
                const fileNodes = getAllFileNodes();
                const currentIndex = getCurrentFileIndex();
                console.log('Current file index:', currentIndex);
                console.log('Total files:', fileNodes.length);
                
                // 自动导航到下一个文件
                if (currentIndex < fileNodes.length - 1) {
                    const nextNode = fileNodes[currentIndex + 1];
                    console.log('Navigating to next file:', nextNode.id);
                    // 使用 jstree 的 select_node 方法选中下一个文件
                    $('#directory-tree').jstree('select_node', nextNode.id);
                    // 加载下一个文件的内容
                    loadFile(nextNode.id);
                } else {
                    console.log('Last file reached, reloading current file');
                    // 如果是最后一个文件，重新加载当前文件以显示新添加的评分
                    loadFile(currentFilePath);
                }
            } else {
                showError(response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error adding grade to file:', error);
            showError('添加评分到文件失败：' + error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// 撤销评分
function cancelGrade() {
    if (!currentFilePath) {
        showError('请先选择要评分的文件');
        return;
    }

    showLoading();
    $.ajax({
        url: '/grading/remove_grade/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: {
            path: currentFilePath
        },
        success: function(response) {
            if (response.status === 'success') {
                // 恢复之前的评分状态
                setGradeButtonState(selectedGrade);
                pendingGrade = null;
                // 禁用确定按钮
                $('#add-grade-to-file').prop('disabled', true);
                
                // 重新加载文件内容
                loadFile(currentFilePath);
                
                const alertHtml = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        评分已撤销
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                $('#file-content').prepend(alertHtml);
            } else {
                showError(response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error removing grade:', error);
            showError('撤销评分失败：' + error);
        },
        complete: function() {
            hideLoading();
        }
    });
}

// 初始化文件树
function initTree() {
    console.log('Initializing tree...');
    console.log('Initial tree data:', window.initialTreeData);
    
    // 确保 initialTreeData 是数组
    const initialData = Array.isArray(window.initialTreeData) ? window.initialTreeData : [];
    console.log('Processed initial data:', initialData);
    
    // 销毁现有的树（如果存在）
    if ($('#directory-tree').jstree(true)) {
        $('#directory-tree').jstree(true).destroy();
    }
    
    // 显示加载状态
    $('#directory-tree').html('<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');
    
    // 配置 jstree
    const treeConfig = {
        'core': {
            'data': initialData,
            'check_callback': true,
            'multiple': false,  // 确保只能选择一个节点
            'themes': {
                'responsive': true,
                'dots': true,
                'icons': true,
                'stripes': true,
                'variant': 'large',
                'url': '/static/grading/vendor/jstree/themes/default/style.min.css',
                'dir': '/static/grading/vendor/jstree/themes/default/'
            }
        },
        'types': {
            'default': {
                'icon': 'jstree-file'
            },
            'file': {
                'icon': 'jstree-file'
            },
            'folder': {
                'icon': 'jstree-folder'
            }
        },
        'plugins': ['types', 'wholerow', 'state'],
        'state': {
            'key': 'grading-tree',
            'filter': function(state) {
                // 只保存打开/关闭状态
                return {
                    'core': {
                        'open': state.core.open,
                        'selected': state.core.selected
                    }
                };
            }
        }
    };
    
    // 初始化 jstree
    $('#directory-tree').jstree(treeConfig).on('ready.jstree', function() {
        console.log('Tree initialized');
        // 树初始化完成后，如果有初始选中的节点，加载其内容
        const selectedNodes = $('#directory-tree').jstree('get_selected');
        if (selectedNodes.length > 0) {
            const node = $('#directory-tree').jstree('get_node', selectedNodes[0]);
            if (node && node.type === 'file') {
                loadFile(node.id);
            }
        }
    }).on('select_node.jstree', function(e, data) {
        // 确保只处理文件节点
        if (data.node.type === 'file') {
            // 取消其他节点的选中状态
            const selectedNodes = $('#directory-tree').jstree('get_selected');
            selectedNodes.forEach(nodeId => {
                if (nodeId !== data.node.id) {
                    $('#directory-tree').jstree('deselect_node', nodeId);
                }
            });
            
            // 加载文件内容
            loadFile(data.node.id);
            // 更新导航按钮状态
            updateNavigationButtons();
        }
    });
}

// 页面加载完成后初始化树
$(document).ready(function() {
    console.log('Document ready, initializing tree...');
    // 设置初始树数据
    if (window.initialTreeData) {
        console.log('Initial tree data:', window.initialTreeData);
        initTree();
    } else {
        console.error('No initial tree data available');
    }
    
    // 设置默认评分按钮状态
    setGradeButtonState('B');
    
    // 绑定评分按钮点击事件
    $('.grade-button').click(function() {
        const grade = $(this).data('grade');
        console.log('Grade button clicked:', grade);
        saveGrade(grade);
    });
    
    // 绑定确定按钮点击事件
    $('#add-grade-to-file').click(function() {
        console.log('Confirm button clicked, using selected grade:', selectedGrade);
        // 使用当前选中的评分
        addGradeToFile(selectedGrade);
    });
    
    // 绑定撤销按钮点击事件
    $('#cancel-grade').click(function() {
        cancelGrade();
    });
    
    // 绑定导航按钮事件
    $('#prev-file').click(function() {
        navigateToPrevFile();
    });
    
    $('#next-file').click(function() {
        navigateToNextFile();
    });
});