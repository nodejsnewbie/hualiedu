// 全局变量
let currentFile = '';
let selectedGrade = 'B';  // 设置默认评分为 B

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
}

// 加载文件内容
function loadFile(path) {
  console.log('Loading file:', path);
  showLoading();
  currentFile = path;

  // 添加超时处理
  const timeout = setTimeout(() => {
    hideLoading();
    showError('加载文件超时，请重试');
  }, 30000); // 30秒超时

  $.ajax({
    url: '/grading/',
    method: 'POST',
    data: {
      action: 'get_content',
      path: path
    },
    success: function(response) {
      clearTimeout(timeout);
      if (response.status === 'success') {
        $('#file-content').html(response.content);
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
  if (!currentFile) {
    showError('请先选择要评分的文件');
    return;
  }

  selectedGrade = grade;  // 更新当前选中的评分
  setGradeButtonState(grade);  // 更新按钮状态

  showLoading();
  $.ajax({
    url: '/grading/',
    method: 'POST',
    data: {
      action: 'save_grade',
      path: currentFile,
      grade: grade
    },
    success: function(response) {
      if (response.status === 'success') {
        const alertHtml = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        评分已保存
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
        $('#file-content').prepend(alertHtml);
      } else {
        showError(response.message);
      }
    },
    error: function(xhr, status, error) {
      console.error('Error saving grade:', error);
      showError('保存评分失败：' + error);
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
  if ($('#grade-tree').jstree(true)) {
    $('#grade-tree').jstree(true).destroy();
  }
  
  // 显示加载状态
  $('#grade-tree').html('<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');
  
  // 配置 jstree
  const treeConfig = {
    'core': {
      'data': initialData,  // 直接使用初始数据
      'check_callback': true,
      'themes': {
        'responsive': true,
        'dots': true,
        'icons': true,
        'stripes': true
      }
    },
    'types': {
      'default': {
        'icon': 'jstree-file'
      },
      'folder': {
        'icon': 'jstree-folder'
      }
    },
    'plugins': ['types']
  };
  
  // 初始化 jstree
  $('#grade-tree').jstree(treeConfig).on('ready.jstree', function(e, data) {
    console.log('Tree is ready');
    // 展开根节点
    data.instance.open_node('#');
  }).on('select_node.jstree', function(e, data) {
    console.log('Selected node:', data.node);
    if (data.node.type !== 'folder') {
      loadFile(data.node.id);
    }
  }).on('error.jstree', function(e, data) {
    console.error('Tree error:', data);
    $('#grade-tree').html(`<div class="alert alert-danger">加载目录树失败：${data.error || '未知错误'}</div>`);
  });
}

// 页面加载完成后初始化树
$(document).ready(function() {
  console.log('Document ready, initializing tree...');
  initTree();
  
  // 绑定评分按钮点击事件
  $('.grade-button').click(function() {
    const grade = $(this).data('grade');
    saveGrade(grade);
  });
}); 