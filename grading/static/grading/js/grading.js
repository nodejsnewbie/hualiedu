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

// 加载文件内容
function loadFile(path) {
  console.log('Loading file:', path);
  showLoading();
  currentFilePath = path;

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
      if (response.status === 'success') {
        // 根据文件类型显示内容
        switch (response.type) {
          case 'docx':
            // Word 文档已经转换为 HTML
            $('#file-content').html(response.content);
            break;
            
          case 'pdf':
            // 使用 PDF.js 显示 PDF 文件
            $('#file-content').html(`
              <div class="pdf-container">
                <iframe src="/static/pdfjs/web/viewer.html?file=${encodeURIComponent(response.content)}" 
                        width="100%" height="800px" frameborder="0"></iframe>
              </div>
            `);
            break;
            
          case 'image':
            // 使用 viewer.js 显示图片
            $('#file-content').html(`
              <div class="image-container">
                <img src="${response.content}" class="img-fluid" alt="图片预览">
              </div>
            `);
            // 初始化 viewer.js
            $('.image-container img').viewer({
              navbar: false,
              title: false,
              toolbar: {
                zoomIn: 1,
                zoomOut: 1,
                oneToOne: 1,
                reset: 1,
                prev: 0,
                play: 0,
                next: 0,
                rotateLeft: 1,
                rotateRight: 1,
                flipHorizontal: 1,
                flipVertical: 1,
              }
            });
            break;
            
          case 'text':
            // 使用 CodeMirror 显示文本文件
            $('#file-content').html(`
              <div class="text-container">
                <textarea id="code-editor">${response.content}</textarea>
              </div>
            `);
            // 初始化 CodeMirror
            const editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
              mode: 'text/plain',
              lineNumbers: true,
              readOnly: true,
              theme: 'default',
              lineWrapping: true
            });
            break;
            
          case 'binary':
            // 显示二进制文件提示
            $('#file-content').html(`
              <div class="alert alert-info">
                这是一个二进制文件，无法直接显示。请下载后查看。
                <a href="${response.content}" class="btn btn-primary btn-sm ms-2" download>
                  下载文件
                </a>
              </div>
            `);
            break;
            
          default:
            showError('不支持的文件类型');
        }
        
        // 设置默认评分按钮状态
        setGradeButtonState(selectedGrade);
      } else {
        showError(response.message || '加载文件失败');
      }
    },
    error: function(xhr, status, error) {
      clearTimeout(timeout);
      console.error('Error loading file:', error);
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
  if (!currentFilePath) {
    showError('请先选择要评分的文件');
    return;
  }

  // 只更新按钮状态，不立即保存
  setGradeButtonState(grade);
  pendingGrade = grade;
  
  // 自动点击确定按钮
  $('#add-grade-to-file').click();
}

// 获取所有文件节点
function getAllFileNodes() {
    const allNodes = $('#directory-tree').jstree('get_json', '#', { flat: true });
    return allNodes.filter(node => node.type === 'file');
}

// 获取当前文件在文件列表中的索引
function getCurrentFileIndex() {
    const fileNodes = getAllFileNodes();
    const currentFile = $('#directory-tree').jstree('get_selected', true)[0];
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
      if (response.status === 'success') {
        const alertHtml = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            评分已添加到文件末尾
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        `;
        $('#file-content').prepend(alertHtml);
        
        // 重新加载文件内容以显示新添加的评分
        loadFile(currentFilePath);
        
        // 重置待确认的评分
        pendingGrade = null;
        // 禁用确定按钮
        $('#add-grade-to-file').prop('disabled', true);

        // 自动导航到下一个文件
        navigateToNextFile();
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
                'variant': 'large'
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
        saveGrade(grade);
    });
    
    // 绑定添加评分到文件按钮点击事件
    $('#add-grade-to-file').click(function() {
        if (pendingGrade) {
            addGradeToFile(pendingGrade);
        }
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