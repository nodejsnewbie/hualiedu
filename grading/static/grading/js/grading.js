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

  $.ajax({
    url: '/grading/',
    method: 'POST',
    data: {
      action: 'get_content',
      path: path,
      csrfmiddlewaretoken: getCSRFToken()
    },
    success: function(response) {
      if (response.status === 'success') {
        $('#file-content').html(response.content);
        // 设置默认评分按钮状态
        setGradeButtonState(selectedGrade);
      } else {
        showError(response.message);
      }
    },
    error: function(xhr, status, error) {
      console.error('Error loading file:', error);
      showError('加载文件失败：' + error);
    },
    complete: function() {
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
      grade: grade,
      csrfmiddlewaretoken: getCSRFToken()
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
  
  $('#grade-tree').jstree({
    'core': {
      'data': function(node) {
        console.log('Getting data for node:', node);
        
        // 如果是根节点且有初始数据，直接使用初始数据
        if (node.id === '#' && initialData.length > 0) {
          console.log('Using initial tree data:', initialData);
          return initialData;
        }
        
        // 否则从服务器获取数据
        console.log('Fetching data from server for path:', node.id === '#' ? '' : node.id);
        return {
          'url': '/grading/',
          'data': function(node) {
            return {
              'action': 'get_directory_tree',
              'file_path': node.id === '#' ? '' : node.id,
              'csrfmiddlewaretoken': getCSRFToken()
            };
          },
          'type': 'POST',
          'dataType': 'json',
          'processData': function(data) {
            console.log('Received data from server:', data);
            if (data.status === 'success') {
              return data.data;
            } else {
              console.error('Failed to load directory tree:', data.message);
              showError(data.message || '加载目录失败');
              return [];
            }
          }
        };
      },
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
      },
      'file': {
        'icon': 'jstree-file'
      }
    },
    'plugins': ['types', 'wholerow', 'state'],
    'state': { 'key': 'grading_tree_state' }
  }).on('ready.jstree', function() {
    console.log('Tree is ready');
    const tree = $('#grade-tree').jstree(true);
    const rootNode = tree.get_node('#');
    if (rootNode) {
      console.log('Opening root node');
      tree.open_node(rootNode);
    }
  }).on('select_node.jstree', function(e, data) {
    console.log('Node selected:', data.node);
    if (data.node.type !== 'folder') {
      console.log('Loading file:', data.node.id);
      loadFile(data.node.id);
    }
  });
}

// 初始化评分按钮
function initGradeButtons() {
  // 设置默认评分按钮状态
  setGradeButtonState(selectedGrade);

  $('.grade-button').click(function() {
    const grade = $(this).data('grade');
    saveGrade(grade);
  });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  initTree();
  initGradeButtons();
}); 