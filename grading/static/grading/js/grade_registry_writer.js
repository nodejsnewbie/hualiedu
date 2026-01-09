/**
 * 作业成绩写入成绩登分册 - JavaScript交互
 * 
 * 功能：
 * 1. 工具箱模块：目录选择和提交逻辑
 * 2. 作业评分系统：登分按钮点击事件
 * 3. 进度显示更新
 * 4. 结果报告渲染
 */

(function() {
    'use strict';

    // 全局变量
    let selectedRepository = null;
    let selectedDirectory = null;
    let registryFileName = null;

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

    // 初始化目录树
    function initDirectoryTree(repositoryId) {
        console.log('初始化目录树，仓库ID:', repositoryId);
        
        // 清空目录树
        $('#directory-tree').html('<p class="text-muted text-center mt-5">加载中...</p>');
        
        // 加载目录树数据
        $.ajax({
            url: '/grading/get_directory_tree/',
            method: 'GET',
            data: {
                repo_id: repositoryId
            },
            success: function(response) {
                if (response.status === 'success') {
                    renderDirectoryTree(response.tree_data);
                } else {
                    $('#directory-tree').html(`<div class="alert alert-danger">${response.message}</div>`);
                }
            },
            error: function(xhr, status, error) {
                console.error('加载目录树失败:', error);
                $('#directory-tree').html('<div class="alert alert-danger">加载目录树失败，请重试</div>');
            }
        });
    }

    // 渲染目录树
    function renderDirectoryTree(treeData) {
        console.log('渲染目录树，数据:', treeData);
        
        // 销毁现有的树
        if ($('#directory-tree').jstree(true)) {
            $('#directory-tree').jstree('destroy');
        }
        
        // 清空容器
        $('#directory-tree').empty();
        
        // 初始化 jstree
        $('#directory-tree').jstree({
            'core': {
                'data': treeData,
                'check_callback': true,
                'multiple': false,
                'themes': {
                    'responsive': true,
                    'dots': true,
                    'icons': true
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
            'plugins': ['types', 'wholerow']
        }).on('select_node.jstree', function(e, data) {
            // 只允许选择文件夹
            if (data.node.type === 'folder') {
                onDirectorySelected(data.node);
            } else {
                // 取消选择文件节点
                $('#directory-tree').jstree('deselect_node', data.node);
            }
        });
    }

    // 目录选择事件处理
    function onDirectorySelected(node) {
        console.log('选择目录:', node);
        
        selectedDirectory = node.id;
        
        // 显示选中目录信息
        $('#selected-dir-path').text(selectedDirectory);
        $('#selected-dir-card').show();
        
        // 检查成绩登分册
        checkGradeRegistry(selectedDirectory);
    }

    // 检查成绩登分册
    function checkGradeRegistry(directoryPath) {
        console.log('检查成绩登分册:', directoryPath);
        
        $('#registry-file-name').text('检测中...').removeClass('text-success text-danger');
        $('#start-write-btn').prop('disabled', true);
        
        $.ajax({
            url: '/grading/check_grade_registry/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            data: {
                directory: directoryPath,
                repo_id: selectedRepository
            },
            success: function(response) {
                if (response.found) {
                    registryFileName = response.file_name;
                    $('#registry-file-name')
                        .text(response.file_name)
                        .addClass('text-success');
                    $('#start-write-btn').prop('disabled', false);
                } else {
                    $('#registry-file-name')
                        .text('未找到成绩登分册')
                        .addClass('text-danger');
                    $('#start-write-btn').prop('disabled', true);
                }
            },
            error: function(xhr, status, error) {
                console.error('检查成绩登分册失败:', error);
                $('#registry-file-name')
                    .text('检查失败')
                    .addClass('text-danger');
                $('#start-write-btn').prop('disabled', true);
            }
        });
    }

    // 开始写入
    function startWrite() {
        console.log('开始写入成绩');
        
        if (!selectedRepository || !selectedDirectory) {
            alert('请先选择仓库和目录');
            return;
        }
        
        // 隐藏选择卡片，显示进度卡片
        $('#selected-dir-card').hide();
        $('#progress-card').show();
        $('#result-card').hide();
        
        // 重置进度
        updateProgress(0, '准备中...');
        
        // 发送请求
        $.ajax({
            url: '/grading/grade-registry-writer/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            data: {
                class_directory: selectedDirectory,
                repository_id: selectedRepository
            },
            success: function(response) {
                if (response.success) {
                    // 显示结果
                    displayResult(response.data);
                } else {
                    alert('写入失败: ' + (response.error || '未知错误'));
                    resetUI();
                }
            },
            error: function(xhr, status, error) {
                console.error('写入失败:', error);
                alert('写入失败: ' + error);
                resetUI();
            }
        });
    }

    // 更新进度
    function updateProgress(percentage, text, currentFile) {
        $('#progress-bar').css('width', percentage + '%').attr('aria-valuenow', percentage);
        $('#progress-percentage').text(percentage + '%');
        $('#progress-text').text(text);
        
        if (currentFile) {
            $('#current-file-name').text(currentFile);
        }
    }

    // 显示结果
    function displayResult(data) {
        console.log('显示结果:', data);
        
        // 隐藏进度卡片，显示结果卡片
        $('#progress-card').hide();
        $('#result-card').show();
        
        // 更新摘要
        const summary = data.summary || {};
        $('#total-files').text(summary.total_files || 0);
        $('#success-count').text(summary.success_count || 0);
        $('#failed-count').text(summary.failed_count || 0);
        $('#skipped-count').text(summary.skipped_count || 0);
        
        // 更新详细结果
        const details = data.details || {};
        
        // 成功列表
        if (details.success && details.success.length > 0) {
            $('#success-count-text').text(details.success.length);
            let successHtml = '';
            details.success.forEach(function(item) {
                successHtml += `
                    <tr>
                        <td>${item.file || '-'}</td>
                        <td>${item.student || '-'}</td>
                        <td>${item.homework || '-'}</td>
                        <td><span class="badge bg-success">${item.grade || '-'}</span></td>
                    </tr>
                `;
            });
            $('#success-list').html(successHtml);
            $('#success-section').show();
        } else {
            $('#success-section').hide();
        }
        
        // 失败列表
        if (details.failed && details.failed.length > 0) {
            $('#failed-count-text').text(details.failed.length);
            let failedHtml = '';
            details.failed.forEach(function(item) {
                failedHtml += `
                    <tr>
                        <td>${item.file || '-'}</td>
                        <td class="text-danger">${item.error || '-'}</td>
                    </tr>
                `;
            });
            $('#failed-list').html(failedHtml);
            $('#failed-section').show();
        } else {
            $('#failed-section').hide();
        }
        
        // 跳过列表
        if (details.skipped && details.skipped.length > 0) {
            $('#skipped-count-text').text(details.skipped.length);
            let skippedHtml = '';
            details.skipped.forEach(function(item) {
                skippedHtml += `
                    <tr>
                        <td>${item.file || '-'}</td>
                        <td class="text-warning">${item.reason || '-'}</td>
                    </tr>
                `;
            });
            $('#skipped-list').html(skippedHtml);
            $('#skipped-section').show();
        } else {
            $('#skipped-section').hide();
        }
        
        // 根据结果更新标题颜色
        if (summary.failed_count > 0) {
            $('#result-header').removeClass('bg-success').addClass('bg-warning');
        } else {
            $('#result-header').removeClass('bg-warning').addClass('bg-success');
        }
    }

    // 重置UI
    function resetUI() {
        $('#progress-card').hide();
        $('#result-card').hide();
        $('#selected-dir-card').show();
    }

    // 重新写入
    function newWrite() {
        $('#result-card').hide();
        $('#selected-dir-card').show();
        
        // 清空选择
        selectedDirectory = null;
        registryFileName = null;
        
        // 取消目录树选择
        if ($('#directory-tree').jstree(true)) {
            $('#directory-tree').jstree('deselect_all');
        }
    }

    // 页面加载完成后初始化
    $(document).ready(function() {
        console.log('Grade Registry Writer JS 已加载');
        
        // 仓库选择事件
        $('#repository-select').on('change', function() {
            const repoId = $(this).val();
            if (repoId) {
                selectedRepository = repoId;
                initDirectoryTree(repoId);
                
                // 重置选择状态
                selectedDirectory = null;
                registryFileName = null;
                $('#selected-dir-card').hide();
                $('#progress-card').hide();
                $('#result-card').hide();
            } else {
                selectedRepository = null;
                $('#directory-tree').html('<p class="text-muted text-center mt-5">请先选择仓库</p>');
                $('#selected-dir-card').hide();
            }
        });
        
        // 开始写入按钮
        $('#start-write-btn').on('click', startWrite);
        
        // 重新写入按钮
        $('#new-write-btn').on('click', newWrite);
    });

    // 导出函数供外部使用
    window.GradeRegistryWriter = {
        updateProgress: updateProgress,
        displayResult: displayResult
    };
})();
