// 全局变量
let currentFile = '';
let selectedGrade = '';

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
  const docContent = document.getElementById('docContent');
  docContent.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="mdi mdi-alert"></i> ${message}
        </div>
    `;
}

// 显示内容
function showContent(content) {
  const docContent = document.getElementById('docContent');
  docContent.innerHTML = content;
}

// 文件加载函数
function loadFile(filePath) {
  if (!filePath) {
    showError('请选择要查看的文件');
    return;
  }

  // 检查文件路径是否在允许的目录下
  if (!filePath.includes('media/grades')) {
    showError('只能查看作业目录下的文件');
    return;
  }

  currentFile = filePath;
  $('#loading').show();
  document.getElementById('docContent').innerHTML = '<div class="loading-message">加载中...</div>';

  fetch('/grading/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': getCSRFToken()
    },
    body: `file_path=${encodeURIComponent(filePath)}&action=get_content`
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success' && data.content) {
        showContent(data.content);
        selectedGrade = '';
        document.querySelectorAll('#grade-buttons button').forEach(btn => {
          btn.classList.remove('selected');
        });
      } else {
        throw new Error(data.message || '文件内容加载失败');
      }
    })
    .catch(error => {
      console.error('Error loading document:', error);
      showError(error.message || '文件加载失败，请确保文件存在且可访问');
    })
    .finally(() => {
      $('#loading').hide();
    });
}

// 目录树初始化
function initTree() {
  console.log('Initializing tree...');

  $('#grade-tree').jstree('destroy');

  $('#grade-tree').jstree({
    'core': {
      'data': function (node, cb) {
        const token = getCSRFToken();
        if (!token) {
          console.error('CSRF token not found');
          showError('CSRF token not found');
          cb.call(this, []);
          return;
        }

        let requestPath = node.id === '#' ? '' : node.id;
        console.log('Requesting directory tree for path:', requestPath);

        $.ajax({
          url: '/grading/',
          method: 'POST',
          headers: { 'X-CSRFToken': token },
          data: {
            action: 'get_directory_tree',
            file_path: requestPath
          },
          success: function (data) {
            console.log('Server response:', data);
            if (data.status === 'success') {
              if (node.id === '#') {
                console.log('Processing root node data');
                cb.call(this, data.children);
              } else {
                console.log('Processing child node data');
                const processedData = data.children.map(item => ({
                  ...item,
                  type: item.type || (item.children ? 'folder' : 'file'),
                  icon: item.type === 'folder' ? 'jstree-folder' : 'jstree-file'
                }));
                console.log('Processed data:', processedData);
                cb.call(this, processedData);
              }
            } else {
              console.error('Failed to load directory tree:', data.message);
              showError(data.message || '加载目录失败');
              cb.call(this, []);
            }
          },
          error: function (xhr, status, error) {
            console.error('AJAX error:', error);
            console.error('Status:', status);
            console.error('Response:', xhr.responseText);
            showError('加载目录失败：' + error);
            cb.call(this, []);
          }
        });
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
  }).on('ready.jstree', function () {
    console.log('Tree is ready');
    const tree = $('#grade-tree').jstree(true);
    const rootNode = tree.get_node('#');
    if (rootNode) {
      console.log('Opening root node');
      tree.open_node(rootNode);
    }
  }).on('select_node.jstree', function (e, data) {
    console.log('Node selected:', data.node);
    if (data.node.type !== 'folder') {
      console.log('Loading file:', data.node.id);
      loadFile(data.node.id);
    }
  }).on('load_node.jstree', function (e, data) {
    console.log('Node loaded:', data.node.id);
  }).on('error.jstree', function (e, data) {
    console.error('jsTree error:', data);
  });
}

// 评分按钮事件处理
function initGradeButtons() {
  document.querySelectorAll('#grade-buttons button').forEach(button => {
    button.addEventListener('click', function () {
      const grade = this.getAttribute('data-grade');
      selectedGrade = grade;

      // 移除其他按钮的选中状态
      document.querySelectorAll('#grade-buttons button').forEach(btn => {
        btn.classList.remove('selected');
      });

      // 添加当前按钮的选中状态
      this.classList.add('selected');

      // 发送评分请求
      fetch('/grading/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCSRFToken()
        },
        body: `action=save_grade&grade=${grade}&file_path=${encodeURIComponent(currentFile)}`
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            showMessage('success', data.message);
          } else {
            showMessage('error', data.message);
          }
        })
        .catch(error => {
          console.error('Error saving grade:', error);
          showMessage('error', '保存评分失败');
        });
    });
  });
}

// 显示消息
function showMessage(type, message) {
  const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
  const icon = type === 'success' ? 'mdi-check-circle' : 'mdi-alert';

  const messageElement = document.createElement('div');
  messageElement.className = `alert ${alertClass} alert-dismissible fade show message-popup`;
  messageElement.innerHTML = `
        <i class="mdi ${icon}"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

  document.body.appendChild(messageElement);

  // 3秒后自动消失
  setTimeout(() => {
    messageElement.remove();
  }, 3000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
  initTree();
  initGradeButtons();
}); 