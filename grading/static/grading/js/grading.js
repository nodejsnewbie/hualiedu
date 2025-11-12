// 立即执行的测试代码
console.log('=== grading.js 文件已加载 ===');
console.log('当前时间:', new Date().toLocaleString());

// 全局变量
let currentFile = '';
let selectedGrade = 'B';  // 设置默认评分为 B
let gradeMode = 'letter';  // 评分方式：'letter' 或 'text'
var currentFilePath = null;
let pendingGrade = null;  // 待确认的评分
let currentRepoId = null;  // 当前选择的仓库ID
let currentCourse = null;  // 当前选择的课程
let isLabCourse = false;  // 是否为实验课
let isFileLocked = false;  // 当前文件是否被锁定（格式错误）

// 将关键变量暴露到window对象，供其他脚本使用
window.currentCourse = null;
window.currentRepoId = null;

// 获取 CSRF Token
window.getCSRFToken = function() {
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
window.setGradeButtonState = function(grade) {
  console.log('=== 设置评分按钮状态开始 ===');
  console.log('目标评分:', grade);
  console.log('评分按钮总数:', $('.grade-button').length);

  // 验证评分参数
  if (!grade) {
    console.error('评分参数为空');
    return;
  }

  // 移除所有评分按钮的active状态
  $('.grade-button').removeClass('active');
  console.log('已移除所有评分按钮的active状态');

  // 查找目标按钮
  const targetButton = $(`.grade-button[data-grade="${grade}"]`);
  console.log('目标评分按钮:', targetButton.length, targetButton.text());

  if (targetButton.length === 0) {
    console.error('未找到目标评分按钮:', grade);
    console.log('可用的评分按钮:');
    $('.grade-button').each(function() {
      console.log('-', $(this).data('grade'), ':', $(this).text());
    });
    return;
  }

  // 设置目标按钮为active状态
  targetButton.addClass('active');
  console.log('已设置目标按钮为active状态');

  // 更新全局变量
  selectedGrade = grade;

  console.log('=== 评分按钮状态设置完成 ===');
  console.log('当前评分:', selectedGrade);
}

// 切换评分方式
window.switchGradeMode = function(mode) {
  console.log('=== 切换评分方式开始 ===');
  console.log('目标模式:', mode);
  console.log('当前评分方式按钮数量:', $('.grade-mode-btn').length);
  console.log('字母评分按钮组:', $('#letter-grade-buttons').length);
  console.log('文字评分按钮组:', $('#text-grade-buttons').length);

  // 验证模式参数
  if (mode !== 'letter' && mode !== 'text') {
    console.error('无效的评分模式:', mode);
    return;
  }

  gradeMode = mode;

  // 更新按钮状态
  $('.grade-mode-btn').removeClass('active');
  const targetButton = $(`.grade-mode-btn[data-mode="${mode}"]`);
  console.log('目标按钮:', targetButton.length, targetButton.text());

  if (targetButton.length === 0) {
    console.error('未找到目标按钮:', mode);
    return;
  }

  targetButton.addClass('active');

  // 显示/隐藏对应的评分按钮组
  if (mode === 'letter') {
    console.log('切换到字母评分方式');

    // 隐藏文字评分按钮组
    $('#text-grade-buttons').hide();
    console.log('文字评分按钮组已隐藏');

    // 显示字母评分按钮组
    $('#letter-grade-buttons').show();
    console.log('字母评分按钮组已显示');

    // 验证显示状态
    console.log('字母评分按钮组显示状态:', $('#letter-grade-buttons').is(':visible'));
    console.log('文字评分按钮组显示状态:', $('#text-grade-buttons').is(':visible'));

    // 设置默认评分
    if (!selectedGrade || !['A', 'B', 'C', 'D', 'E'].includes(selectedGrade)) {
      console.log('设置默认字母评分: B');
      selectedGrade = 'B';
    } else {
      console.log('保持当前字母评分:', selectedGrade);
    }

    // 设置按钮状态
    setGradeButtonState(selectedGrade);

  } else if (mode === 'text') {
    console.log('切换到文字评分方式');

    // 隐藏字母评分按钮组
    $('#letter-grade-buttons').hide();
    console.log('字母评分按钮组已隐藏');

    // 显示文字评分按钮组
    $('#text-grade-buttons').show();
    console.log('文字评分按钮组已显示');

    // 验证显示状态
    console.log('字母评分按钮组显示状态:', $('#letter-grade-buttons').is(':visible'));
    console.log('文字评分按钮组显示状态:', $('#text-grade-buttons').is(':visible'));

    // 设置默认评分
    if (!selectedGrade || !['优秀', '良好', '中等', '及格', '不及格'].includes(selectedGrade)) {
      console.log('设置默认文字评分: 良好');
      selectedGrade = '良好';
    } else {
      console.log('保持当前文字评分:', selectedGrade);
    }

    // 设置按钮状态
    setGradeButtonState(selectedGrade);
  }

  console.log('=== 评分方式切换完成 ===');
  console.log('当前评分:', selectedGrade);
  console.log('评分方式:', gradeMode);

  // 验证显示一致性
  validateGradeModeDisplay();
}

// 检查教师评价按钮状态
function checkTeacherCommentButton() {
  const button = $('#teacher-comment-btn');
  console.log('Teacher comment button check:');
  console.log('- Element exists:', button.length > 0);
  console.log('- Disabled state:', button.prop('disabled'));
  console.log('- Current file path:', currentFilePath);
  console.log('- Button text:', button.text());
}

// 启用教师评价按钮
function enableTeacherCommentButton() {
  console.log('Enabling teacher comment button');
  // 检查文件是否被锁定
  if (isFileLocked) {
    console.log('文件已锁定，不启用教师评价按钮');
    return;
  }
  $('#teacher-comment-btn').prop('disabled', false);
  checkTeacherCommentButton();
}

// 禁用教师评价按钮
function disableTeacherCommentButton() {
  console.log('Disabling teacher comment button');
  $('#teacher-comment-btn').prop('disabled', true);
  checkTeacherCommentButton();
}

// 启用AI评分按钮
function enableAiScoreButton() {
  console.log('=== 启用AI评分按钮 ===');
  console.log('按钮元素:', $('#ai-score-btn').length);
  console.log('启用前状态:', $('#ai-score-btn').prop('disabled'));
  // 检查文件是否被锁定
  if (isFileLocked) {
    console.log('文件已锁定，不启用AI评分按钮');
    return;
  }
  $('#ai-score-btn').prop('disabled', false);
  console.log('启用后状态:', $('#ai-score-btn').prop('disabled'));
  console.log('按钮文本:', $('#ai-score-btn').text());
}

// 禁用AI评分按钮
function disableAiScoreButton() {
  console.log('Disabling AI score button');
  $('#ai-score-btn').prop('disabled', true);
}

// 验证评分方式显示一致性
window.validateGradeModeDisplay = function() {
  console.log('=== 验证评分方式显示一致性 ===');
  console.log('当前评分方式:', gradeMode);
  console.log('当前评分:', selectedGrade);

  // 检查评分方式按钮状态
  const letterButton = $('.grade-mode-btn[data-mode="letter"]');
  const textButton = $('.grade-mode-btn[data-mode="text"]');
  console.log('字母评分按钮active状态:', letterButton.hasClass('active'));
  console.log('文字评分按钮active状态:', textButton.hasClass('active'));

  // 检查评分按钮组显示状态
  const letterGroupVisible = $('#letter-grade-buttons').is(':visible');
  const textGroupVisible = $('#text-grade-buttons').is(':visible');
  console.log('字母评分按钮组显示状态:', letterGroupVisible);
  console.log('文字评分按钮组显示状态:', textGroupVisible);

  // 检查评分按钮状态
  const activeGradeButton = $('.grade-button.active');
  console.log('当前激活的评分按钮:', activeGradeButton.length, activeGradeButton.text());

  // 验证一致性
  let isConsistent = true;

  if (gradeMode === 'letter') {
    if (!letterButton.hasClass('active')) {
      console.error('字母评分方式但按钮未激活');
      isConsistent = false;
    }
    if (!letterGroupVisible) {
      console.error('字母评分方式但按钮组未显示');
      isConsistent = false;
    }
    if (textGroupVisible) {
      console.error('字母评分方式但文字按钮组仍显示');
      isConsistent = false;
    }
  } else if (gradeMode === 'text') {
    if (!textButton.hasClass('active')) {
      console.error('文字评分方式但按钮未激活');
      isConsistent = false;
    }
    if (!textGroupVisible) {
      console.error('文字评分方式但按钮组未显示');
      isConsistent = false;
    }
    if (letterGroupVisible) {
      console.error('文字评分方式但字母按钮组仍显示');
      isConsistent = false;
    }
  }

  console.log('评分方式显示一致性:', isConsistent);
  return isConsistent;
}

// 处理评分信息
window.handleGradeInfo = function(gradeInfo) {
    console.log('=== 处理评分信息开始 ===');
    console.log('评分信息:', gradeInfo);
    console.log('当前评分方式:', gradeMode);
    console.log('当前评分:', selectedGrade);

    // 检查文件是否被锁定
    if (gradeInfo.locked) {
        console.log('文件已被锁定，禁用所有评分功能');
        // 设置全局锁定状态
        isFileLocked = true;
        
        // 禁用所有评分按钮
        $('.grade-button').prop('disabled', true).addClass('disabled');
        $('.grade-mode-btn').prop('disabled', true).addClass('disabled');
        $('#add-grade-to-file').prop('disabled', true);
        $('#cancel-grade').prop('disabled', true);
        $('#teacher-comment-btn').prop('disabled', true);
        $('#ai-score-btn').prop('disabled', true);
        
        // 显示锁定提示（使用固定ID以便后续检查）
        const lockMessage = '<div id="file-lock-warning" class="alert alert-danger mt-3"><i class="bi bi-lock-fill"></i> <strong>此文件因格式错误已被锁定</strong><br>不允许修改评分和评价。如需解锁，请让学生重新提交正确格式的作业。</div>';
        // 移除旧的锁定提示（如果存在）
        $('#file-lock-warning').remove();
        // 在文件内容前添加锁定提示
        $('#file-content').prepend(lockMessage);
        return;
    } else {
        // 如果文件未锁定，移除可能存在的锁定提示
        isFileLocked = false;
        $('#file-lock-warning').remove();
        // 启用评分方式切换按钮
        $('.grade-mode-btn').prop('disabled', false).removeClass('disabled');
    }

    if (gradeInfo.has_grade && gradeInfo.grade) {
        // 文件已有评分，设置按钮状态
        console.log('文件已有评分:', gradeInfo.grade, '类型:', gradeInfo.grade_type);

        // 更新全局变量
        selectedGrade = gradeInfo.grade;
        gradeMode = gradeInfo.grade_type || 'letter';

        // 根据评分类型切换评分方式
        if (gradeInfo.grade_type === 'letter') {
            switchGradeMode('letter');
        } else if (gradeInfo.grade_type === 'text') {
            switchGradeMode('text');
        }

        // 设置评分按钮状态
        setGradeButtonState(gradeInfo.grade);

        console.log('评分按钮状态已更新，当前评分:', selectedGrade, '评分方式:', gradeMode);
    } else {
        // 文件没有评分，保持用户当前的评分方式选择
        console.log('文件没有评分，保持当前评分方式:', gradeMode);

        // 保持当前的评分方式，不重置
        // 如果当前没有选择评分方式，才使用默认值
        if (!gradeMode) {
            console.log('没有评分方式，使用默认字母评分');
            gradeMode = 'letter';
            selectedGrade = 'B';
        } else {
            console.log('保持当前评分方式:', gradeMode);
            // 根据当前评分方式设置默认评分
            if (gradeMode === 'letter') {
                selectedGrade = selectedGrade || 'B';
                console.log('字母评分方式，默认评分:', selectedGrade);
            } else if (gradeMode === 'text') {
                selectedGrade = selectedGrade || '良好';
                console.log('文字评分方式，默认评分:', selectedGrade);
            }
        }

        // 应用当前的评分方式
        switchGradeMode(gradeMode);
        setGradeButtonState(selectedGrade);

        console.log('保持当前评分方式完成，当前评分:', selectedGrade, '评分方式:', gradeMode);
    }

    // 验证显示一致性
    validateGradeModeDisplay();
    console.log('=== 处理评分信息结束 ===');
}

// 处理文件内容显示
window.handleFileContent = function(response) {
    console.log('=== handleFileContent 开始 ===');
    console.log('响应对象:', response);
    console.log('文件内容容器元素数量:', $('#file-content').length);
    
    if (response.status === 'success') {
        const fileContent = $('#file-content');
        console.log('找到文件内容容器，准备清空');
        fileContent.empty();
        console.log('文件内容容器已清空，准备显示内容，类型:', response.type);

        switch (response.type) {
            case 'text':
                // 文本文件
                // 对HTML内容进行转义以防止XSS攻击
                const escapedContent = $('<div>').text(response.content).html();
                fileContent.html(`<pre class="border p-3 bg-light" style="white-space: pre-wrap; word-wrap: break-word; max-height: 600px; overflow-y: auto;">${escapedContent}</pre>`);
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

        // 处理评分信息
        console.log('=== 处理文件内容响应中的评分信息 ===');
        console.log('评分信息:', response.grade_info);
        console.log('当前评分方式:', gradeMode);
        console.log('当前评分:', selectedGrade);

        if (response.grade_info) {
            handleGradeInfo(response.grade_info);
        } else {
            console.log('响应中没有评分信息，保持当前评分方式');
            // 如果没有评分信息，保持当前的评分方式选择
            if (!gradeMode) {
                console.log('没有评分方式，使用默认字母评分');
                gradeMode = 'letter';
                selectedGrade = 'B';
            } else {
                console.log('保持当前评分方式:', gradeMode);
                // 根据当前评分方式设置默认评分
                if (gradeMode === 'letter') {
                    selectedGrade = selectedGrade || 'B';
                    console.log('字母评分方式，默认评分:', selectedGrade);
                } else if (gradeMode === 'text') {
                    selectedGrade = selectedGrade || '良好';
                    console.log('文字评分方式，默认评分:', selectedGrade);
                }
            }

            // 应用当前的评分方式
            switchGradeMode(gradeMode);
            setGradeButtonState(selectedGrade);
            console.log('保持当前评分方式完成，当前评分:', selectedGrade, '评分方式:', gradeMode);
        }
        console.log('=== 处理文件内容响应中的评分信息结束 ===');
    } else {
        $('#file-content').html(`<div class="alert alert-danger">${response.message}</div>`);
    }
}

// 加载文件内容
window.loadFile = function(path) {
    console.log('Loading file:', path);
    showLoading();
    
    // 重置锁定状态（将在handleGradeInfo中根据实际情况更新）
    isFileLocked = false;
    
    // 统一路径格式，使用正斜杠
    const normalizedPath = path.replace(/\\/g, '/');
    currentFilePath = normalizedPath;

    // 禁用教师评价按钮，直到文件加载完成
    disableTeacherCommentButton();

    // 禁用AI评分按钮，直到文件加载完成
    disableAiScoreButton();

    // 禁用确定按钮，直到文件加载完成
    $('#add-grade-to-file').prop('disabled', true);

    // 获取当前文件所在目录
    const dirPath = normalizedPath.substring(0, normalizedPath.lastIndexOf('/'));
    if (!dirPath) {
        console.error('Invalid directory path for:', path);
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

    // 准备请求数据
    const requestData = {
        path: normalizedPath
    };
    
    // 如果有当前仓库ID和课程，添加到请求中
    if (currentRepoId) {
        requestData.repo_id = currentRepoId;
    }
    if (currentCourse) {
        requestData.course = currentCourse;
    }
    
    console.log('Loading file with data:', requestData);

    $.ajax({
        url: '/grading/get_file_content/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: requestData,
        success: function(response) {
            clearTimeout(timeout);
            console.log('=== 文件内容加载成功 ===');
            console.log('响应状态:', response.status);
            console.log('响应类型:', response.type);
            console.log('响应内容长度:', response.content ? response.content.length : 0);
            console.log('完整响应:', response);
            
            handleFileContent(response);

            // 启用教师评价按钮
            enableTeacherCommentButton();

            // 启用AI评分按钮
            enableAiScoreButton();

            // 启用确定按钮（如果文件未锁定）
            if (!isFileLocked) {
                $('#add-grade-to-file').prop('disabled', false);
            }
        },
        error: function(xhr, status, error) {
            clearTimeout(timeout);
            console.error('Error loading file:', error);
            console.error('XHR status:', xhr.status);
            console.error('XHR response:', xhr.responseText);
            showError('加载文件失败：' + (error || '未知错误'));

            // 禁用教师评价按钮
            disableTeacherCommentButton();

            // 禁用AI评分按钮
            disableAiScoreButton();

            // 禁用确定按钮
            $('#add-grade-to-file').prop('disabled', true);
        },
        complete: function() {
            clearTimeout(timeout);
            hideLoading();
        }
    });
}

// 保存评分
window.saveGrade = function(grade) {
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

// 获取所有文件节点（按目录树顺序）
window.getAllFileNodes = function() {
    const tree = $('#directory-tree').jstree(true);
    const fileNodes = [];
    
    // 深度优先遍历树，按显示顺序收集文件节点
    function traverseNode(nodeId) {
        const node = tree.get_node(nodeId);
        if (!node) return;
        
        // 如果是文件节点，添加到列表
        if (node.type === 'file') {
            fileNodes.push(node);
            console.log('收集文件节点:', node.id, node.text);
        }
        
        // 递归遍历子节点
        if (node.children && node.children.length > 0) {
            node.children.forEach(childId => {
                traverseNode(childId);
            });
        }
    }
    
    // 从根节点开始遍历
    traverseNode('#');
    
    console.log('总共收集到', fileNodes.length, '个文件节点');
    return fileNodes;
}

// 获取当前文件在文件列表中的索引
window.getCurrentFileIndex = function() {
    const fileNodes = getAllFileNodes();
    const currentFile = $('#directory-tree').jstree('get_selected', true)[0];
    console.log('当前选中的文件:', currentFile ? currentFile.id : 'none');
    if (!currentFile) return -1;
    const index = fileNodes.findIndex(node => node.id === currentFile.id);
    console.log('当前文件索引:', index);
    return index;
}

// 导航到上一个文件
window.navigateToPrevFile = function() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();

    if (currentIndex > 0) {
        const prevNode = fileNodes[currentIndex - 1];
        console.log('导航到上一个文件:', prevNode.text);
        // 保存当前评分方式状态
        const savedGradeMode = gradeMode;
        const savedSelectedGrade = selectedGrade;
        console.log('保存的评分方式:', savedGradeMode, '评分:', savedSelectedGrade);
        
        // 选择节点会触发文件加载
        $('#directory-tree').jstree('select_node', prevNode.id);
        
        // 文件加载后，如果文件没有评分，恢复之前的评分方式
        // 这会在 handleFileContent 中自动处理
    }
}

// 导航到下一个文件
window.navigateToNextFile = function() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();

    if (currentIndex < fileNodes.length - 1) {
        const nextNode = fileNodes[currentIndex + 1];
        console.log('导航到下一个文件:', nextNode.text);
        // 保存当前评分方式状态
        const savedGradeMode = gradeMode;
        const savedSelectedGrade = selectedGrade;
        console.log('保存的评分方式:', savedGradeMode, '评分:', savedSelectedGrade);
        
        // 选择节点会触发文件加载
        $('#directory-tree').jstree('select_node', nextNode.id);
        
        // 文件加载后，如果文件没有评分，恢复之前的评分方式
        // 这会在 handleFileContent 中自动处理
    }
}

// 更新导航按钮状态和文件位置显示
window.updateNavigationButtons = function() {
    const fileNodes = getAllFileNodes();
    const currentIndex = getCurrentFileIndex();
    const totalFiles = fileNodes.length;

    // 更新按钮禁用状态
    $('#prev-file').prop('disabled', currentIndex <= 0);
    $('#next-file').prop('disabled', currentIndex >= totalFiles - 1);
    
    // 更新文件位置显示（如"3/10"）
    if (currentIndex >= 0 && totalFiles > 0) {
        $('#current-file-index').text(currentIndex + 1);  // 显示从1开始的索引
        $('#total-files').text(totalFiles);
    } else {
        $('#current-file-index').text('0');
        $('#total-files').text('0');
    }
    
    console.log('导航状态已更新 - 当前文件:', currentIndex + 1, '/', totalFiles);
}

// 注意：文件选择时的导航按钮更新已在 initTree() 函数中的 jstree 初始化时处理
// 这里不需要重复绑定事件

// 修改addGradeToFile函数，在评分后自动导航到下一个文件
window.addGradeToFile = function(grade) {
    console.log('=== 添加评分到文件 ===');
    console.log('评分:', grade);
    console.log('评分方式:', gradeMode);
    console.log('当前文件路径:', currentFilePath);

    if (!currentFilePath) {
        showError('请先选择要评分的文件');
        return;
    }

    if (!grade) {
        showError('请先选择一个评分');
        return;
    }

    showLoading();
    
    // 准备请求数据
    const requestData = {
        path: currentFilePath,
        grade: grade,
        grade_type: gradeMode  // 添加评分方式参数
    };
    
    // 如果有当前仓库ID和课程，添加到请求中
    if (currentRepoId) {
        requestData.repo_id = currentRepoId;
    }
    if (currentCourse) {
        requestData.course = currentCourse;
    }
    
    console.log('请求数据:', requestData);
    console.log('后端将自动判断作业类型');
    
    $.ajax({
        url: '/grading/add_grade_to_file/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: requestData,
        success: function(response) {
            console.log('Grade added successfully:', response);
            if (response.status === 'success') {
                // 检查是否有警告信息
                let alertClass = 'alert-success';
                let alertMessage = '评分已成功保存';
                
                if (response.data && response.data.warning) {
                    alertClass = 'alert-warning';
                    alertMessage = response.data.warning;
                    console.warn('Warning:', response.data.warning);
                }
                
                const alertHtml = `
                    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                        ${alertMessage}
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
                    console.log('当前索引:', currentIndex);
                    console.log('下一个文件节点:', nextNode.id, nextNode.text);
                    console.log('下一个文件路径:', nextNode.data ? nextNode.data.path : 'undefined');
                    
                    // 使用 jstree 的 select_node 方法选中下一个文件
                    // 这会触发 select_node 事件，自动调用 loadFile
                    $('#directory-tree').jstree('select_node', nextNode.id);
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
window.cancelGrade = function() {
    if (!currentFilePath) {
        showError('请先选择要评分的文件');
        return;
    }

    showLoading();
    
    // 准备请求数据
    const requestData = {
        path: currentFilePath
    };
    
    // 如果有当前仓库ID和课程，添加到请求中
    if (currentRepoId) {
        requestData.repo_id = currentRepoId;
    }
    if (currentCourse) {
        requestData.course = currentCourse;
    }
    
    console.log('撤销评分请求数据:', requestData);
    
    $.ajax({
        url: '/grading/remove_grade/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: requestData,
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
window.initTree = function() {
    console.log('Initializing tree...');
    console.log('Initial tree data:', window.initialTreeData);

    // 确保 initialTreeData 是数组
    const initialData = Array.isArray(window.initialTreeData) ? window.initialTreeData : [];
    console.log('Processed initial data:', initialData);

    // 确保jQuery可用
    if (typeof jQuery === 'undefined') {
        console.error('jQuery 未加载，无法初始化文件树');
        return;
    }
    const $ = jQuery;
    
    // 首先检查目录树容器是否存在
    const $treeContainer = $('#directory-tree');
    if ($treeContainer.length === 0) {
        console.error('目录树容器 #directory-tree 未找到');
        return;
    }
    
    // 销毁现有的树（如果存在）
    if ($treeContainer.jstree(true)) {
        try {
            $treeContainer.jstree(true).destroy();
        } catch (e) {
            console.error('销毁现有树时出错:', e);
        }
    }

    // 清空目录树容器，确保没有残留内容影响初始化
    $treeContainer.empty();
    
    // 如果没有数据，不初始化 jstree，只显示提示信息
    if (initialData.length === 0) {
        $treeContainer.html('<p class="text-muted">请选择仓库和课程</p>');
        return;
    }
    
    // 显示加载状态
    $treeContainer.html('<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');

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
        'plugins': ['types', 'wholerow', 'state', 'contextmenu'],
        'contextmenu': {
            'items': function(node) {
                // 安全检查：确保 node 存在且有效
                if (!node || !node.id) {
                    return {};
                }
                
                var items = {};
                if (node.type === 'folder') {
                    items.batchAiScore = {
                        "label": "<i class='bi bi-robot'></i> 批量AI评分",
                        "action": function(obj) {
                            handleBatchAiScore(node.id);
                        }
                    };
                }
                return items;
            }
        },
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
    try {
        $('#directory-tree').jstree(treeConfig)
            .on('ready.jstree', function() {
                console.log('Tree initialized');
                
                // 为作业文件夹添加类型标签
                if (typeof window.addHomeworkTypeLabels === 'function') {
                    window.addHomeworkTypeLabels();
                }
                
                // 树初始化完成后，如果有初始选中的节点，加载其内容
                const selectedNodes = $('#directory-tree').jstree('get_selected');
                if (selectedNodes.length > 0) {
                    const node = $('#directory-tree').jstree('get_node', selectedNodes[0]);
                    if (node && node.type === 'file') {
                        loadFile(node.id);
                    }
                }
            })
            .on('select_node.jstree', function(e, data) {
        // 处理文件节点
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
            // 更新导航按钮状态和文件位置显示
            updateNavigationButtons();
            
            // 禁用批量登分按钮（选中的是文件，不是文件夹）
            $('#batch-grade-btn').prop('disabled', true)
                .attr('title', '请先选择作业文件夹（非文件）')
                .html('<i class="bi bi-tasks"></i> 批量登分');
            currentHomeworkFolder = null;
            currentHomeworkId = null;
        } else if (data.node.type === 'folder') {
            // 处理文件夹节点 - 更新批量登分按钮
            updateBatchGradeButton(data.node.id, data.node.id);
        }
    });
    } catch (error) {
        console.error('初始化 jstree 时出错:', error);
        $('#directory-tree').html('<div class="alert alert-warning">目录树初始化失败，请刷新页面重试</div>');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('Document ready, initializing tree...');

    // 基本检查
    console.log('jQuery版本:', $.fn.jquery);
    console.log('页面标题:', document.title);

    // 检查教师评价按钮的初始状态
    console.log('Initial teacher comment button disabled state:', $('#teacher-comment-btn').prop('disabled'));
    console.log('Teacher comment button element:', $('#teacher-comment-btn').length);

    // 确保教师评价按钮初始状态为禁用
    disableTeacherCommentButton();

    // 确保AI评分按钮初始状态为禁用
    disableAiScoreButton();

    // 初始化批量登分按钮为禁用状态
    console.log('=== 初始化批量登分按钮 ===');
    console.log('按钮元素数量:', $('#batch-grade-btn').length);
    console.log('初始disabled状态:', $('#batch-grade-btn').prop('disabled'));
    $('#batch-grade-btn').prop('disabled', true)
        .attr('title', '请先选择作业文件夹（非文件）')
        .html('<i class="bi bi-tasks"></i> 批量登分');
    console.log('设置后disabled状态:', $('#batch-grade-btn').prop('disabled'));
    console.log('按钮文本:', $('#batch-grade-btn').text());

    // 设置初始树数据
    if (window.initialTreeData) {
        console.log('Initial tree data:', window.initialTreeData);
        initTree();
    } else {
        console.error('No initial tree data available');
    }

    // 设置默认评分按钮状态（仅在页面初始化时）
    console.log('=== 页面初始化评分状态 ===');
    console.log('初始化前字母评分按钮组显示状态:', $('#letter-grade-buttons').is(':visible'));
    console.log('初始化前文字评分按钮组显示状态:', $('#text-grade-buttons').is(':visible'));

    // 初始化默认状态（如果还没有设置的话）
    if (!gradeMode) {
        console.log('初始化默认评分方式: letter');
        gradeMode = 'letter';
        selectedGrade = 'B';
    } else {
        console.log('保持现有评分方式:', gradeMode, '评分:', selectedGrade);
    }

    // 设置默认评分方式
    switchGradeMode(gradeMode);

    console.log('初始化后字母评分按钮组显示状态:', $('#letter-grade-buttons').is(':visible'));
    console.log('初始化后文字评分按钮组显示状态:', $('#text-grade-buttons').is(':visible'));

    // 评分模式按钮事件绑定（防止HTML onclick未定义问题）
    $(document).off('click', '.grade-mode-btn').on('click', '.grade-mode-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var mode = $(this).data('mode');
        if (typeof window.switchGradeMode === 'function') {
            window.switchGradeMode(mode);
        } else {
            console.error('window.switchGradeMode 未定义');
        }
    });

    // 检查按钮是否存在
    console.log('=== 评分方式按钮检查 ===');
    console.log('评分方式按钮总数:', $('.grade-mode-btn').length);
    $('.grade-mode-btn').each(function(index) {
        console.log(`按钮 ${index}:`, $(this).text(), 'data-mode:', $(this).data('mode'));
    });

    // 检查所有相关元素
    console.log('=== DOM元素检查 ===');
    console.log('字母评分按钮组元素:', $('#letter-grade-buttons')[0]);
    console.log('文字评分按钮组元素:', $('#text-grade-buttons')[0]);
    console.log('字母评分按钮组HTML:', $('#letter-grade-buttons').html());
    console.log('文字评分按钮组HTML:', $('#text-grade-buttons').html());
    console.log('字母评分按钮组CSS display:', $('#letter-grade-buttons').css('display'));
    console.log('文字评分按钮组CSS display:', $('#text-grade-buttons').css('display'));

    // 检查评分方式切换功能是否正常
    console.log('=== 评分方式切换功能检查 ===');
    console.log('字母等级按钮:', $('.grade-mode-btn[data-mode="letter"]').length);
    console.log('文字等级按钮:', $('.grade-mode-btn[data-mode="text"]').length);
    console.log('字母评分按钮组:', $('#letter-grade-buttons').length);
    console.log('文字评分按钮组:', $('#text-grade-buttons').length);

    // 检查按钮组的显示状态
    console.log('字母评分按钮组显示状态:', $('#letter-grade-buttons').is(':visible'));
    console.log('文字评分按钮组显示状态:', $('#text-grade-buttons').is(':visible'));

    // 绑定评分按钮点击事件（使用事件委托，避免重复绑定）
    $(document).off('click', '.grade-button').on('click', '.grade-button', function() {
        // 检查文件是否被锁定
        if (isFileLocked) {
            console.log('文件已锁定，不允许评分');
            showError('此文件因格式错误已被锁定，不允许修改评分');
            return;
        }
        
        const grade = $(this).data('grade');
        console.log('评分按钮被点击:', grade);
        
        // 更新按钮状态
        $('.grade-button').removeClass('active');
        $(this).addClass('active');
        selectedGrade = grade;
        
        // 立即保存评分并转到下一个文件
        addGradeToFile(grade);
    });

    // 绑定确定按钮点击事件（使用事件委托，避免重复绑定）
    $(document).off('click', '#add-grade-to-file').on('click', '#add-grade-to-file', function() {
        console.log('确定按钮被点击，当前选中评分:', selectedGrade);
        
        // 检查文件是否被锁定
        if (isFileLocked) {
            console.log('文件已锁定，不允许评分');
            showError('此文件因格式错误已被锁定，不允许修改评分');
            return;
        }
        
        if (!currentFilePath) {
            showError('请先选择要评分的文件');
            return;
        }

        if (!selectedGrade) {
            showError('请先选择评分');
            return;
        }

        // 保存评分并转到下一个文件
        addGradeToFile(selectedGrade);
    });

    // 绑定撤销按钮点击事件
    $(document).on('click', '#cancel-grade', function() {
        // 检查文件是否被锁定
        if (isFileLocked) {
            console.log('文件已锁定，不允许撤销评分');
            showError('此文件因格式错误已被锁定，不允许修改评分');
            return;
        }
        cancelGrade();
    });

    // 绑定导航按钮事件
    $(document).on('click', '#prev-file', function() {
        navigateToPrevFile();
    });

    $(document).on('click', '#next-file', function() {
        navigateToNextFile();
    });

    // 绑定教师评价按钮点击事件
    $(document).on('click', '#teacher-comment-btn', function() {
        console.log('教师评价按钮被点击，当前文件路径:', currentFilePath);
        if (currentFilePath) {
            // 直接显示模态框，评价内容会在模态框显示时自动加载
            $('#teacherCommentModal').modal('show');
        } else {
            alert('请先选择文件');
        }
    });

    // 绑定保存教师评价按钮点击事件
    $(document).on('click', '#saveTeacherComment', function() {
        console.log('保存教师评价按钮被点击');
        saveTeacherComment();
    });

    // 新增：绑定AI评分按钮点击事件
    $(document).on('click', '#ai-score-btn', function() {
        console.log('=== AI评分按钮被点击 ===');
        console.log('当前文件路径:', currentFilePath);
        console.log('按钮状态:', $(this).prop('disabled'));
        console.log('按钮文本:', $(this).text());

        if (!currentFilePath) {
            alert('请先选择一个文件进行AI评分');
            return;
        }

        console.log('AI评分按钮被点击，文件路径:', currentFilePath);
        showLoading();

        // 禁用按钮防止重复点击
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 评分中...');

        $.ajax({
            url: '/grading/ai_score/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            data: {
                path: currentFilePath
            },
            success: function(response) {
                if (response.status === 'success') {
                    // 使用一个模态框或者alert来显示结果
                    alert(`AI评分完成！\n\n分数: ${response.score}\n等级: ${response.grade}\n\n评语:\n${response.comment}`);
                    // 刷新文件内容以显示新的评分和评语
                    loadFile(currentFilePath);
                } else {
                    showError('AI评分失败: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('AI评分请求失败:', error);
                let errorMessage = 'AI评分请求失败';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                    // 如果是已有评分的错误，显示弹出框
                    if (xhr.status === 400 && errorMessage.includes('已有评分')) {
                        showAiScoreAlertModal(errorMessage, currentFilePath);
                        return;
                    }
                } else if (xhr.status === 400) {
                    errorMessage = '请求参数错误';
                } else if (xhr.status === 500) {
                    errorMessage = '服务器内部错误';
                }
                showError(errorMessage);
            },
            complete: function() {
                // 恢复按钮状态（如果文件未锁定）
                if (!isFileLocked) {
                    $('#ai-score-btn').prop('disabled', false).html('<i class="bi bi-robot"></i> AI评分');
                } else {
                    $('#ai-score-btn').prop('disabled', true).html('<i class="bi bi-robot"></i> AI评分');
                }
                hideLoading();
            }
        });
    });

    // 模态框显示时自动加载评价内容和历史记录
    $('#teacherCommentModal').on('show.bs.modal', function() {
        console.log('=== 教师评价模态框显示 ===');
        console.log('当前文件路径:', currentFilePath);
        console.log('输入框元素:', $('#teacherCommentText').length);

        if (currentFilePath) {
            console.log('开始加载评价内容...');
            // 自动加载当前文件的评价内容到输入框
            loadTeacherComment(currentFilePath);
        } else {
            console.log('没有当前文件路径，清空输入框');
            $('#teacherCommentText').val('');
        }
        
        // 渲染历史评价
        CommentHistory.renderHistory('commentHistoryContainer');
    });

    // AI评分提示模态框事件处理
    $('#aiScoreAlertModal').on('show.bs.modal', function() {
        // 隐藏强制AI评分按钮（默认情况下）
        $('#forceAiScore').hide();
    });

    // 强制AI评分按钮点击事件
    $('#forceAiScore').on('click', function() {
        if (currentFilePath) {
            // 关闭模态框
            $('#aiScoreAlertModal').modal('hide');

            // 执行强制AI评分（这里可以添加一个特殊的参数来跳过检查）
            console.log('执行强制AI评分:', currentFilePath);
            // TODO: 实现强制AI评分功能
            alert('强制AI评分功能正在开发中...');
        }
    });
});

// 教师评价相关函数
window.loadTeacherComment = function(filePath) {
    console.log('加载教师评价，文件路径:', filePath);
    if (!filePath) {
        $('#teacherCommentText').val('');
        return;
    }

    // 准备请求数据
    const requestData = {
        file_path: filePath
    };
    
    // 如果有当前仓库ID和课程，添加到请求中
    if (currentRepoId) {
        requestData.repo_id = currentRepoId;
    }
    if (currentCourse) {
        requestData.course = currentCourse;
    }
    
    console.log('获取教师评价请求数据:', requestData);

    $.ajax({
        url: '/grading/get_teacher_comment/',
        method: 'GET',
        data: requestData,
        success: function(response) {
            console.log('=== 获取教师评价响应 ===');
            console.log('响应内容:', response);
            console.log('响应类型:', typeof response);
            console.log('响应success字段:', response.success);
            console.log('响应comment字段:', response.comment);

            if (response.success) {
                console.log('获取评价成功，准备更新显示');
                const commentText = response.comment || '';
                console.log('评价文本:', commentText);
                console.log('输入框元素存在:', $('#teacherCommentText').length > 0);

                // 将评价内容载入到输入框中，方便直接修改
                $('#teacherCommentText').val(commentText);

                console.log('评价内容已载入到输入框');
                console.log('输入框当前值:', $('#teacherCommentText').val());

                // 如果评价内容为空或"暂无评价"，显示提示信息
                if (!commentText || commentText === '暂无评价') {
                    console.log('文件中没有找到评价内容，显示提示信息');
                    $('#teacherCommentText').attr('placeholder', '文件中没有找到评价内容，请在此输入新的评价...');
                }
            } else {
                console.error('获取评价失败:', response.message);
                alert('获取评价失败: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('获取教师评价失败:', error);
            console.error('XHR状态:', xhr.status);
            console.error('XHR响应:', xhr.responseText);
            alert('获取评价失败: ' + error);
        }
    });
}

// 评价历史管理（缓存评分和评价的组合）
window.CommentHistory = {
    storageKey: 'teacher_grade_comment_history',
    maxItems: 10,  // 增加到10条
    
    // 获取历史记录
    getHistory: function() {
        try {
            const history = localStorage.getItem(this.storageKey);
            return history ? JSON.parse(history) : [];
        } catch (e) {
            console.error('读取评价历史失败:', e);
            return [];
        }
    },
    
    // 添加评分和评价到历史
    addGradeComment: function(grade, comment) {
        if (!comment || !comment.trim()) return;
        
        // 如果没有提供评分，使用当前选中的评分
        if (!grade) {
            grade = selectedGrade || 'B';
        }
        
        let history = this.getHistory();
        
        // 创建记录对象
        const record = {
            grade: grade,
            comment: comment.trim(),
            timestamp: new Date().getTime()
        };
        
        // 移除重复的评价（相同评价内容）
        history = history.filter(item => item.comment !== comment.trim());
        
        // 添加到开头
        history.unshift(record);
        
        // 只保留最近的记录
        history = history.slice(0, this.maxItems);
        
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(history));
            console.log('评分和评价已添加到历史:', grade, comment);
        } catch (e) {
            console.error('保存评价历史失败:', e);
        }
    },
    
    // 渲染历史评价按钮
    renderHistory: function(containerId) {
        const history = this.getHistory();
        const container = $(`#${containerId}`);
        
        if (!container.length) {
            console.error('历史评价容器不存在:', containerId);
            return;
        }
        
        container.empty();
        
        if (history.length === 0) {
            container.html('<small class="text-muted">暂无历史评价</small>');
            return;
        }
        
        container.append('<small class="text-muted d-block mb-2">最近使用的评价（点击快速填入评价和评分）：</small>');
        
        history.forEach((record, index) => {
            const displayText = record.comment.length > 30 ? record.comment.substring(0, 30) + '...' : record.comment;
            const btn = $('<button>')
                .addClass('btn btn-sm btn-outline-secondary me-2 mb-2')
                .attr('type', 'button')
                .html(`<span class="badge bg-primary me-1">${record.grade}</span>${displayText}`)
                .attr('title', `评分: ${record.grade}\n评价: ${record.comment}`)
                .on('click', function() {
                    // 填入评价
                    $('#teacherCommentText').val(record.comment);
                    // 设置评分（按评论对应的评分打分）
                    selectedGrade = record.grade;
                    setGradeButtonState(record.grade);
                    console.log('已填入历史记录 - 评分:', record.grade, '评价:', record.comment);
                });
            container.append(btn);
        });
    }
};

window.saveTeacherComment = function() {
    const comment = $('#teacherCommentText').val().trim();
    console.log('保存教师评价，内容:', comment);

    if (!comment) {
        alert('请输入评价内容');
        return;
    }

    if (!currentFilePath) {
        alert('请先选择文件');
        return;
    }

    // 如果没有选择评分，使用默认评分
    if (!selectedGrade) {
        selectedGrade = gradeMode === 'letter' ? 'B' : '良好';
        setGradeButtonState(selectedGrade);
        console.log('未选择评分，使用默认评分:', selectedGrade);
    }

    // 准备请求数据
    const requestData = {
        file_path: currentFilePath,
        comment: comment,
        grade: selectedGrade  // 添加评分到请求中
    };
    
    // 如果有当前仓库ID和课程，添加到请求中
    if (currentRepoId) {
        requestData.repo_id = currentRepoId;
    }
    if (currentCourse) {
        requestData.course = currentCourse;
    }
    
    console.log('保存教师评价请求数据:', requestData);

    $.ajax({
        url: '/grading/save_teacher_comment/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: requestData,
        success: function(response) {
            console.log('=== 保存教师评价响应 ===');
            console.log('响应内容:', response);
            console.log('响应类型:', typeof response);
            console.log('响应success字段:', response.success);

            if (response.success) {
                console.log('保存成功，准备刷新评价显示');
                
                // 添加到历史记录（包含评分和评价）
                CommentHistory.addGradeComment(selectedGrade, comment);

                // 延迟一点时间再加载评价，确保文件写入完成
                setTimeout(function() {
                    console.log('开始重新加载教师评价');
                    loadTeacherComment(currentFilePath);

                    // 重新加载文件内容，确保评分方式显示正确
                    console.log('重新加载文件内容以更新评分方式显示');
                    loadFile(currentFilePath);
                }, 500);

                $('#teacherCommentModal').modal('hide');
                
                // 自动跳转到下一个文件
                navigateToNextFile();
            } else {
                console.error('保存失败:', response.message);
                alert('保存失败: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('保存教师评价失败:', error);
            console.error('XHR状态:', xhr.status);
            console.error('XHR响应:', xhr.responseText);
            alert('保存失败，请重试');
        }
    });
}


// 为作业文件夹添加类型标签
function addHomeworkTypeLabels() {
    const tree = $('#directory-tree').jstree(true);
    if (!tree) return;
    
    // 获取所有根节点（作业文件夹）
    const rootNodes = tree.get_node('#').children;
    
    rootNodes.forEach(nodeId => {
        const node = tree.get_node(nodeId);
        if (node && node.type === 'folder' && node.data) {
            const homeworkType = node.data.homework_type;
            const homeworkTypeDisplay = node.data.homework_type_display;
            
            if (homeworkType && homeworkTypeDisplay) {
                // 获取节点的DOM元素
                const nodeElement = $('#' + nodeId.replace(/[^a-zA-Z0-9]/g, '\\$&') + '_anchor');
                
                if (nodeElement.length > 0) {
                    // 添加类型标签
                    const badgeClass = homeworkType === 'lab_report' ? 'bg-info' : 'bg-secondary';
                    const badge = `<span class="badge ${badgeClass} ms-2 homework-type-badge" 
                                        data-node-id="${nodeId}" 
                                        data-homework-type="${homeworkType}"
                                        style="font-size: 0.7em; cursor: pointer;"
                                        title="点击修改作业类型">
                                        ${homeworkTypeDisplay}
                                   </span>`;
                    
                    // 检查是否已经添加过标签
                    if (nodeElement.find('.homework-type-badge').length === 0) {
                        nodeElement.append(badge);
                    }
                }
            }
        }
    });
    
    // 绑定点击事件
    $(document).off('click', '.homework-type-badge').on('click', '.homework-type-badge', function(e) {
        e.stopPropagation();
        const nodeId = $(this).data('node-id');
        const currentType = $(this).data('homework-type');
        showHomeworkTypeModal(nodeId, currentType);
    });
}

// 显示作业类型修改模态框
function showHomeworkTypeModal(nodeId, currentType) {
    const tree = $('#directory-tree').jstree(true);
    const node = tree.get_node(nodeId);
    
    if (!node) return;
    
    // 创建模态框HTML
    const modalHtml = `
        <div class="modal fade" id="homeworkTypeModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">修改作业类型</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>作业文件夹：</strong>${node.text}</p>
                        <div class="mb-3">
                            <label class="form-label">作业类型</label>
                            <select class="form-select" id="homeworkTypeSelect">
                                <option value="normal" ${currentType === 'normal' ? 'selected' : ''}>普通作业</option>
                                <option value="lab_report" ${currentType === 'lab_report' ? 'selected' : ''}>实验报告</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="saveHomeworkType">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除旧的模态框
    $('#homeworkTypeModal').remove();
    
    // 添加新的模态框
    $('body').append(modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('homeworkTypeModal'));
    modal.show();
    
    // 绑定保存按钮事件
    $('#saveHomeworkType').off('click').on('click', function() {
        const newType = $('#homeworkTypeSelect').val();
        updateHomeworkType(nodeId, node.text, newType, modal);
    });
}

// 更新作业类型
function updateHomeworkType(nodeId, folderName, homeworkType, modal) {
    if (!currentCourse) {
        alert('请先选择课程');
        return;
    }
    
    console.log('更新作业类型:', {
        course: currentCourse,
        folder: folderName,
        type: homeworkType
    });
    
    $.ajax({
        url: '/grading/api/update-homework-type/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: {
            course_name: currentCourse,
            folder_name: folderName,
            homework_type: homeworkType
        },
        success: function(response) {
            if (response.success) {
                console.log('作业类型已更新:', response);
                
                // 更新节点数据
                const tree = $('#directory-tree').jstree(true);
                const node = tree.get_node(nodeId);
                if (node) {
                    node.data.homework_type = response.homework.homework_type;
                    node.data.homework_type_display = response.homework.homework_type_display;
                }
                
                // 关闭模态框
                modal.hide();
                
                // 重新渲染标签
                setTimeout(() => {
                    addHomeworkTypeLabels();
                }, 300);
                
                // 显示成功提示
                alert('作业类型已更新为：' + response.homework.homework_type_display);
            } else {
                alert('更新失败：' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('更新作业类型失败:', error);
            alert('更新失败，请重试');
        }
    });
}

// ==================== 批量登分功能 ====================

// 全局变量：当前选中的作业文件夹
let currentHomeworkFolder = null;
let currentHomeworkId = null;
let currentHomeworkRelativePath = null;

// 批量登分按钮点击事件
$(document).on('click', '#batch-grade-btn', function() {
    console.log('批量登分按钮被点击');
    
    if (!currentHomeworkFolder || !currentHomeworkId) {
        alert('请先选择一个作业文件夹');
        return;
    }
    
    if (!currentCourse) {
        alert('请先选择课程');
        return;
    }
    
    // 确认对话框
    const confirmMsg = `确定要对作业"${currentHomeworkFolder}"进行批量登分吗？\n\n` +
                      `系统将自动读取所有学生作业中的成绩，并写入到班级成绩登记表中。`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    // 显示加载状态
    const $btn = $(this);
    const originalText = $btn.html();
    $btn.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> 处理中...');
    
    // 调用批量登分API
    $.ajax({
        url: `/grading/homework/${currentHomeworkId}/batch-grade-to-registry/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: {
            relative_path: currentHomeworkRelativePath || ''
        },
        success: function(response) {
            if (response.success) {
                const summary = response.data.summary;
                const details = response.data.details;
                let message = `批量登分完成！\n\n`;
                message += `作业：${response.data.homework_name}\n`;
                message += `课程：${response.data.course_name}\n`;
                message += `班级：${response.data.class_name}\n\n`;
                message += `总文件数：${summary.total}\n`;
                message += `成功：${summary.success}\n`;
                message += `失败：${summary.failed}\n`;
                message += `跳过：${summary.skipped}\n`;
                
                if (summary.failed > 0 && details.failed_files && details.failed_files.length > 0) {
                    message += `\n失败的文件：\n`;
                    details.failed_files.forEach(file => {
                        message += `- ${file.student_name || file.file}: ${file.error}\n`;
                    });
                }
                
                alert(message);
            } else {
                alert('批量登分失败：' + (response.message || response.error || '未知错误'));
            }
        },
        error: function(xhr, status, error) {
            console.error('批量登分失败:', error);
            let errorMsg = '批量登分失败';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg += '：' + xhr.responseJSON.message;
            }
            alert(errorMsg);
        },
        complete: function() {
            // 恢复按钮状态
            $btn.prop('disabled', false).html(originalText);
        }
    });
});

// 当选择作业文件夹时，更新批量登分按钮状态
function updateBatchGradeButton(folderPath, folderId) {
    console.log('=== 更新批量登分按钮状态 ===');
    console.log('文件夹路径:', folderPath);
    console.log('文件夹ID:', folderId);
    console.log('当前课程:', currentCourse);
    
    if (!folderPath || !currentCourse) {
        console.log('条件不满足，禁用按钮');
        $('#batch-grade-btn').prop('disabled', true)
            .attr('title', '请先选择作业文件夹（非文件）')
            .html('<i class="bi bi-tasks"></i> 批量登分');
        currentHomeworkFolder = null;
        currentHomeworkId = null;
        currentHomeworkRelativePath = null;
        console.log('按钮已禁用，文本已重置');
        return;
    }
    
    // 从路径中提取作业文件夹名称
    const pathParts = folderPath.split('/');
    const folderName = pathParts[pathParts.length - 1];
    
    console.log('路径分割结果:', pathParts);
    console.log('提取的文件夹名称:', folderName);
    console.log('当前课程名称:', currentCourse);
    
    // 查询作业信息
    $.ajax({
        url: '/grading/api/homework-info/',
        method: 'GET',
        data: {
            course_name: currentCourse,
            homework_folder: folderName
        },
        success: function(response) {
            if (response.success && response.homework) {
                currentHomeworkFolder = folderName;
                currentHomeworkId = response.homework.id;

                let relativePath = folderPath;
                if (currentCourse) {
                    const coursePrefix = `${currentCourse}/`;
                    if (!folderPath.startsWith(coursePrefix)) {
                        relativePath = `${currentCourse}/${folderPath}`;
                    }
                }
                currentHomeworkRelativePath = relativePath;

                $('#batch-grade-btn').prop('disabled', false)
                    .attr('title', `对作业"${folderName}"进行批量登分`)
                    .html(`<i class="bi bi-tasks"></i> 批量登分 (${folderName})`);
                console.log('作业信息已加载:', response.homework);
            } else {
                $('#batch-grade-btn').prop('disabled', true)
                    .attr('title', '该文件夹不是有效的作业文件夹')
                    .html('<i class="bi bi-tasks"></i> 批量登分');
                currentHomeworkFolder = null;
                currentHomeworkId = null;
                currentHomeworkRelativePath = null;
                console.log('未找到作业信息');
            }
        },
        error: function(xhr, status, error) {
            console.error('查询作业信息失败:', error);
            $('#batch-grade-btn').prop('disabled', true)
                .attr('title', '查询作业信息失败')
                .html('<i class="bi bi-tasks"></i> 批量登分');
            currentHomeworkFolder = null;
            currentHomeworkId = null;
            currentHomeworkRelativePath = null;
        }
    });
}

// 注意：select_node.jstree 事件已在 initTree() 函数中的 jstree 初始化时绑定
// 这里不需要重复绑定
