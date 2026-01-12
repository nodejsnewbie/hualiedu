/**
 * Assignment Management JavaScript
 * 
 * Handles:
 * - Dynamic form field switching for storage types (Requirement 2.2)
 * - File upload progress display (Requirement 9.5, 9.6)
 * - Error message display (Requirement 3.5)
 * - API calls renamed from repository to assignment
 */

// ==================== Assignment Form Management ====================

/**
 * Initialize assignment form with dynamic field switching
 */
function initAssignmentForm() {
    console.log('Initializing assignment form...');
    
    // Storage type selector click event
    $('.storage-type-option').click(function() {
        const type = $(this).data('type');
        const radio = $(this).find('input[type="radio"]');
        
        // Update selected state
        $('.storage-type-option').removeClass('selected');
        $(this).addClass('selected');
        radio.prop('checked', true);
        
        // Show corresponding configuration fields (Requirement 2.2)
        switchStorageTypeFields(type);
        
        // Clear storage type error
        $('#storageTypeError').hide();
    });
    
    // Path preview
    updatePathPreview();

    // Fetch branches button
    $('#fetchBranchesBtn').on('click', function () {
        fetchGitBranches();
    });

    // Clear branches when URL changes
    $('#gitUrl, #gitUsername, #gitPassword').on('input', function () {
        resetBranchSelect();
    });
    
    // Form submission
    $('#assignmentForm').submit(function(e) {
        e.preventDefault();
        submitAssignmentForm(this);
    });
    
    // Clear validation on input
    $('input, select, textarea').on('blur', function() {
        if ($(this).val()) {
            $(this).removeClass('is-invalid');
        }
    });
}

/**
 * Switch storage type fields dynamically (Requirement 2.2)
 * @param {string} type - Storage type ('git' or 'filesystem')
 */
function switchStorageTypeFields(type) {
    console.log('Switching storage type fields to:', type);
    
    // Hide all field groups
    $('.field-group').removeClass('active');
    
    if (type === 'git') {
        // Show Git fields
        $('#gitFields').addClass('active');
        $('#gitUrl').attr('required', true);
        console.log('Git fields displayed');
    } else if (type === 'filesystem') {
        // Show filesystem fields
        $('#filesystemFields').addClass('active');
        $('#gitUrl').removeAttr('required');
        updatePathPreview();
        console.log('Filesystem fields displayed');
    }
}

/**
 * Load classes for selected course
 * @param {string} courseId - Course ID
 */
/**
 * Update path preview for filesystem storage
 */
function updatePathPreview() {
    $('#pathPreview').html('<i class="bi bi-folder"></i> 课程目录/班级目录/<span class="text-muted">&lt;作业次数&gt;/</span>');
}

function resetBranchSelect() {
    const select = $('#gitBranch');
    select.empty();
    select.append('<option value="">请先获取分支</option>');
    $('#gitBranchHelp')
        .removeClass('text-danger')
        .html('<i class="bi bi-info-circle"></i> 从远程仓库分支列表中选择');
}

function fetchGitBranches() {
    const gitUrl = $('#gitUrl').val().trim();
    const gitUsername = $('#gitUsername').val().trim();
    const gitPassword = $('#gitPassword').val();

    if (!gitUrl) {
        showErrorMessage('请先填写Git仓库URL');
        return;
    }

    $('#fetchBranchesBtn').prop('disabled', true).text('加载中...');
    const formData = new FormData();
    formData.append('git_url', gitUrl);
    if (gitUsername || gitPassword) {
        formData.append('git_username', gitUsername);
        formData.append('git_password', gitPassword);
    }

    $.ajax({
        url: '/grading/api/git-branches/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            if (response.status === 'success') {
                const branches = response.branches || [];
                const defaultBranch = response.default_branch || branches[0] || '';
                const select = $('#gitBranch');
                select.empty();
                branches.forEach(function (branch) {
                    select.append(`<option value="${branch}">${branch}</option>`);
                });
                if (defaultBranch) {
                    select.val(defaultBranch);
                }
                $('#gitBranchHelp')
                    .removeClass('text-danger')
                    .html('<i class="bi bi-info-circle"></i> 从远程仓库分支列表中选择');
            } else {
                $('#gitBranchHelp')
                    .addClass('text-danger')
                    .text(response.message || '获取分支失败');
                resetBranchSelect();
            }
        },
        error: function (xhr) {
            const response = xhr.responseJSON;
            $('#gitBranchHelp')
                .addClass('text-danger')
                .text(response && response.message ? response.message : '获取分支失败');
            resetBranchSelect();
        },
        complete: function () {
            $('#fetchBranchesBtn').prop('disabled', false).text('获取分支');
        },
    });
}

/**
 * Submit assignment form with validation
 * @param {HTMLFormElement} form - Form element
 */
function submitAssignmentForm(form) {
    // Clear previous validation state
    $('.is-invalid').removeClass('is-invalid');
    $('#validationAlert').hide();
    
    // Validate required fields
    let isValid = true;
    let errorMessage = '';
    
    
    // Validate storage type
    const storageType = $('input[name="storage_type"]:checked').val();
    if (!storageType) {
        $('#storageTypeError').show();
        isValid = false;
        errorMessage = errorMessage || '请选择提交方式';
    }
    
    // If Git storage, validate Git URL (Requirement 2.2)
    if (storageType === 'git') {
        const gitUrl = $('#gitUrl').val().trim();
        const gitBranch = $('#gitBranch').val();
        if (!gitUrl) {
            $('#gitUrl').addClass('is-invalid');
            isValid = false;
            errorMessage = errorMessage || '请输入Git仓库URL';
        } else if (!isValidUrl(gitUrl)) {
            $('#gitUrl').addClass('is-invalid');
            isValid = false;
            errorMessage = errorMessage || '请输入有效的Git仓库URL';
        }
        if (!gitBranch) {
            $('#gitBranch').addClass('is-invalid');
            isValid = false;
            errorMessage = errorMessage || '请选择分支';
        }
    }

    // If filesystem storage, validate base path
    if (storageType === 'filesystem') {
        const basePath = $('#basePath').val().trim();
        if (!basePath) {
            $('#basePath').addClass('is-invalid');
            isValid = false;
            errorMessage = errorMessage || '请输入存储路径';
        }
    }
    
    if (!isValid) {
        showErrorMessage(errorMessage);
        return false;
    }
    
    // Disable submit button to prevent duplicate submission
    const submitBtn = $('#submitBtn');
    submitBtn.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> 创建中...');
    
    // Submit form
    const formData = new FormData(form);
    
    $.ajax({
        url: $(form).attr('action') || '/grading/assignment/create/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.status === 'success') {
                // Show success message
                showSuccessMessage('作业配置创建成功！');
                // Redirect to list page
                setTimeout(function() {
                    window.location.href = '/grading/assignment/list/';
                }, 1000);
            } else {
                showErrorMessage(response.message || '创建失败，请重试');
                submitBtn.prop('disabled', false).html('<i class="bi bi-check-circle"></i> 创建作业配置');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON;
            // Display friendly error message (Requirement 3.5)
            const errorMsg = response && response.message ? response.message : '请求失败，请检查网络连接';
            showErrorMessage(errorMsg);
            submitBtn.prop('disabled', false).html('<i class="bi bi-check-circle"></i> 创建作业配置');
        }
    });
}

/**
 * Validate URL format
 * @param {string} url - URL to validate
 * @returns {boolean} - True if valid
 */
function isValidUrl(url) {
    const pattern = /^(https?|git|ssh):\/\/.+/i;
    return pattern.test(url);
}

// ==================== Student Submission Management ====================

/**
 * Initialize student submission page
 */
function initStudentSubmission() {
    console.log('Initializing student submission page...');
    
    // Course selection
    $('#studentCourse').change(function() {
        const courseId = $(this).val();
        if (courseId) {
            loadAssignmentDirectories(courseId);
        } else {
            $('#assignmentDirectories').html('<p class="text-muted">请先选择课程</p>');
        }
    });
    
    // Create new assignment directory button
    $(document).on('click', '.create-assignment-btn', function() {
        const courseId = $('#studentCourse').val();
        if (courseId) {
            createAssignmentDirectory(courseId);
        }
    });
    
    // File upload
    $('#assignmentFile').change(function() {
        const file = this.files[0];
        if (file) {
            validateAndPreviewFile(file);
        }
    });
    
    // Upload button
    $('#uploadBtn').click(function() {
        uploadAssignmentFile();
    });
}

/**
 * Load assignment directories for course
 * @param {string} courseId - Course ID
 */
function loadAssignmentDirectories(courseId) {
    $('#assignmentDirectories').html('<div class="text-center"><div class="spinner-border" role="status"></div></div>');
    
    $.ajax({
        url: '/grading/api/student/assignment-directories/',
        method: 'GET',
        data: { course_id: courseId },
        success: function(response) {
            if (response.success) {
                renderAssignmentDirectories(response.directories);
            } else {
                showErrorMessage(response.error || '加载作业目录失败');
                $('#assignmentDirectories').html('<p class="text-danger">加载失败</p>');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON;
            const errorMsg = response && response.error ? response.error : '加载作业目录失败，请稍后重试';
            showErrorMessage(errorMsg);
            $('#assignmentDirectories').html('<p class="text-danger">加载失败</p>');
        }
    });
}

/**
 * Render assignment directories
 * @param {Array} directories - List of directories
 */
function renderAssignmentDirectories(directories) {
    const container = $('#assignmentDirectories');
    container.empty();
    
    if (directories.length === 0) {
        container.html(`
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> 还没有作业目录，点击下方按钮创建第一个作业
            </div>
        `);
    } else {
        const list = $('<div class="list-group"></div>');
        directories.forEach(function(dir) {
            const item = $(`
                <div class="list-group-item list-group-item-action" data-dir="${dir.name}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-folder"></i> ${dir.name}
                            ${dir.has_submission ? '<span class="badge bg-success ms-2">已提交</span>' : ''}
                        </div>
                        <button class="btn btn-sm btn-primary upload-to-dir-btn" data-dir="${dir.name}">
                            <i class="bi bi-upload"></i> 上传作业
                        </button>
                    </div>
                </div>
            `);
            list.append(item);
        });
        container.append(list);
    }
    
    // Add create button
    container.append(`
        <div class="mt-3">
            <button class="btn btn-outline-primary create-assignment-btn">
                <i class="bi bi-plus-circle"></i> 创建新作业
            </button>
        </div>
    `);
    
    // Bind upload button click
    $('.upload-to-dir-btn').click(function() {
        const dirName = $(this).data('dir');
        $('#selectedDirectory').val(dirName);
        $('#uploadSection').show();
        $('html, body').animate({
            scrollTop: $('#uploadSection').offset().top - 100
        }, 500);
    });
}

/**
 * Create new assignment directory (Requirement 9.3, 9.4)
 * @param {string} courseId - Course ID
 */
function createAssignmentDirectory(courseId) {
    $.ajax({
        url: '/grading/api/student/create-assignment-directory/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        data: { course_id: courseId },
        success: function(response) {
            if (response.success) {
                showSuccessMessage(`作业目录 "${response.directory_name}" 创建成功！`);
                // Reload directories
                loadAssignmentDirectories(courseId);
            } else {
                showErrorMessage(response.error || '创建作业目录失败');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON;
            const errorMsg = response && response.error ? response.error : '创建作业目录失败，请稍后重试';
            showErrorMessage(errorMsg);
        }
    });
}

/**
 * Validate and preview file (Requirement 9.6)
 * @param {File} file - File to validate
 */
function validateAndPreviewFile(file) {
    // Validate file format
    const allowedExtensions = ['.docx', '.pdf', '.zip', '.txt', '.jpg', '.png'];
    const fileName = file.name.toLowerCase();
    const fileExt = fileName.substring(fileName.lastIndexOf('.'));
    
    if (!allowedExtensions.includes(fileExt)) {
        showErrorMessage(`不支持的文件格式。允许的格式：${allowedExtensions.join(', ')}`);
        $('#assignmentFile').val('');
        $('#filePreview').hide();
        return false;
    }
    
    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showErrorMessage('文件大小超过限制（最大 10MB）');
        $('#assignmentFile').val('');
        $('#filePreview').hide();
        return false;
    }
    
    // Show file preview
    $('#filePreview').html(`
        <div class="alert alert-info">
            <i class="bi bi-file-earmark"></i> 
            <strong>${file.name}</strong> 
            (${formatFileSize(file.size)})
        </div>
    `).show();
    
    return true;
}

/**
 * Upload assignment file with progress (Requirement 9.5, 9.6)
 */
function uploadAssignmentFile() {
    const fileInput = $('#assignmentFile')[0];
    const file = fileInput.files[0];
    const directory = $('#selectedDirectory').val();
    const courseId = $('#studentCourse').val();
    
    if (!file) {
        showErrorMessage('请选择要上传的文件');
        return;
    }
    
    if (!directory) {
        showErrorMessage('请选择作业目录');
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('directory', directory);
    formData.append('course_id', courseId);
    
    // Disable upload button
    const uploadBtn = $('#uploadBtn');
    uploadBtn.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> 上传中...');
    
    // Show progress bar (Requirement 9.5)
    $('#uploadProgress').show();
    updateUploadProgress(0);
    
    // Upload file with progress tracking
    $.ajax({
        url: '/grading/api/student/upload-assignment/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
            const xhr = new window.XMLHttpRequest();
            // Upload progress
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    updateUploadProgress(percentComplete);
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            if (response.success) {
                updateUploadProgress(100);
                showSuccessMessage('作业上传成功！');
                // Clear form
                $('#assignmentFile').val('');
                $('#filePreview').hide();
                $('#uploadSection').hide();
                // Reload directories
                loadAssignmentDirectories(courseId);
                // Hide progress after delay
                setTimeout(function() {
                    $('#uploadProgress').fadeOut();
                }, 2000);
            } else {
                showErrorMessage(response.error || '上传失败，请重试');
                $('#uploadProgress').hide();
            }
            uploadBtn.prop('disabled', false).html('<i class="bi bi-upload"></i> 上传作业');
        },
        error: function(xhr) {
            const response = xhr.responseJSON;
            const errorMsg = response && response.error ? response.error : '上传失败，请检查网络连接';
            showErrorMessage(errorMsg);
            $('#uploadProgress').hide();
            uploadBtn.prop('disabled', false).html('<i class="bi bi-upload"></i> 上传作业');
        }
    });
}

/**
 * Update upload progress bar
 * @param {number} percent - Progress percentage (0-100)
 */
function updateUploadProgress(percent) {
    const progressBar = $('#uploadProgressBar');
    progressBar.css('width', percent + '%');
    progressBar.attr('aria-valuenow', percent);
    progressBar.text(percent + '%');
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ==================== Error and Success Messages ====================

/**
 * Show error message (Requirement 3.5)
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    $('#validationMessage').text(message);
    $('#validationAlert').removeClass('alert-success').addClass('alert-danger').fadeIn();
    
    // Scroll to top
    $('html, body').animate({
        scrollTop: $('#validationAlert').offset().top - 100
    }, 500);
    
    // Auto hide after 5 seconds
    setTimeout(function() {
        $('#validationAlert').fadeOut();
    }, 5000);
}

/**
 * Show success message
 * @param {string} message - Success message
 */
function showSuccessMessage(message) {
    $('#validationMessage').text(message);
    $('#validationAlert').removeClass('alert-danger').addClass('alert-success').fadeIn();
    
    // Auto hide after 3 seconds
    setTimeout(function() {
        $('#validationAlert').fadeOut();
    }, 3000);
}

/**
 * Get CSRF token from cookie
 * @returns {string} - CSRF token
 */
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

// ==================== Initialization ====================

$(document).ready(function() {
    // Initialize based on page type
    if ($('#assignmentForm').length) {
        initAssignmentForm();
    }
    
    if ($('#studentSubmissionPage').length) {
        initStudentSubmission();
    }
});
