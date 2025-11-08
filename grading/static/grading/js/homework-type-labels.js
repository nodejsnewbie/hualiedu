// 作业类型标签管理
// 这个文件专门处理作业类型标签的显示和修改

// 为作业文件夹添加类型标签
window.addHomeworkTypeLabels = function() {
    console.log('Adding homework type labels...');
    const tree = jQuery('#directory-tree').jstree(true);
    if (!tree) {
        console.log('Tree not initialized');
        return;
    }
    
    // 递归函数：为所有文件夹节点添加标签
    function addLabelToNode(nodeId) {
        const node = tree.get_node(nodeId);
        if (!node || node.type !== 'folder') return;
        
        // 检查节点是否有作业类型数据
        if (node.data && node.data.homework_type && node.data.homework_type_display) {
            const homeworkType = node.data.homework_type;
            const homeworkTypeDisplay = node.data.homework_type_display;
            
            console.log('Found homework node:', nodeId, 'Type:', homeworkType, 'Display:', homeworkTypeDisplay);
            
            // 使用jstree API获取节点的DOM元素
            const nodeElement = tree.get_node(nodeId, true);
            
            if (nodeElement && nodeElement.length > 0) {
                // 查找anchor元素
                const anchorElement = nodeElement.children('a.jstree-anchor');
                
                if (anchorElement.length > 0) {
                    // 检查是否已经添加过标签
                    if (anchorElement.find('.homework-type-badge').length === 0) {
                        // 添加类型标签
                        const badgeClass = homeworkType === 'lab_report' ? 'bg-info' : 'bg-secondary';
                        const badge = jQuery('<span>')
                            .addClass('badge')
                            .addClass(badgeClass)
                            .addClass('ms-2')
                            .addClass('homework-type-badge')
                            .attr('data-node-id', nodeId)
                            .attr('data-homework-type', homeworkType)
                            .css({
                                'font-size': '0.7em',
                                'cursor': 'pointer'
                            })
                            .attr('title', '点击修改作业类型')
                            .text(homeworkTypeDisplay);
                        
                        anchorElement.append(badge);
                        console.log('Badge added for node:', nodeId);
                    }
                }
            }
        }
        
        // 递归处理子节点
        if (node.children && node.children.length > 0) {
            node.children.forEach(function(childId) {
                addLabelToNode(childId);
            });
        }
    }
    
    // 从根节点开始递归处理
    const rootNodes = tree.get_node('#').children;
    console.log('Root nodes:', rootNodes);
    
    rootNodes.forEach(function(nodeId) {
        addLabelToNode(nodeId);
    });
    
    // 绑定点击事件
    jQuery(document).off('click', '.homework-type-badge').on('click', '.homework-type-badge', function(e) {
        e.stopPropagation();
        const nodeId = jQuery(this).data('node-id');
        const currentType = jQuery(this).data('homework-type');
        console.log('Badge clicked:', nodeId, currentType);
        window.showHomeworkTypeModal(nodeId, currentType);
    });
    
    console.log('Homework type labels added');
};

// 显示作业类型修改模态框
window.showHomeworkTypeModal = function(nodeId, currentType) {
    const tree = jQuery('#directory-tree').jstree(true);
    const node = tree.get_node(nodeId);
    
    if (!node) return;
    
    // 创建模态框HTML - 简化版，自动保存
    const modalHtml = `
        <div class="modal fade" id="homeworkTypeModal" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">修改作业类型</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-2"><strong>作业：</strong>${node.text}</p>
                        <div class="mb-2">
                            <select class="form-select" id="homeworkTypeSelect">
                                <option value="normal" ${currentType === 'normal' ? 'selected' : ''}>普通作业</option>
                                <option value="lab_report" ${currentType === 'lab_report' ? 'selected' : ''}>实验报告</option>
                            </select>
                        </div>
                        <div id="savingStatus" class="text-muted small" style="display: none;">
                            <i class="bi bi-hourglass-split"></i> 保存中...
                        </div>
                        <div id="savedStatus" class="text-success small" style="display: none;">
                            <i class="bi bi-check-circle"></i> 已保存
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除旧的模态框
    jQuery('#homeworkTypeModal').remove();
    
    // 添加新的模态框
    jQuery('body').append(modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('homeworkTypeModal'));
    modal.show();
    
    // 绑定下拉框变化事件 - 自动保存
    jQuery('#homeworkTypeSelect').off('change').on('change', function() {
        const newType = jQuery(this).val();
        
        // 显示保存中状态
        jQuery('#savedStatus').hide();
        jQuery('#savingStatus').show();
        
        // 调用更新函数
        window.updateHomeworkType(nodeId, node.text, newType, modal);
    });
};

// 更新作业类型
window.updateHomeworkType = function(nodeId, folderName, homeworkType, modal) {
    console.log('updateHomeworkType called with:', {
        nodeId: nodeId,
        folderName: folderName,
        homeworkType: homeworkType,
        currentCourse: window.currentCourse
    });
    
    if (!window.currentCourse) {
        console.error('currentCourse is not set!');
        alert('系统错误：无法获取当前课程信息。请刷新页面后重试。');
        return;
    }
    
    console.log('更新作业类型:', {
        course: window.currentCourse,
        folder: folderName,
        type: homeworkType
    });
    
    jQuery.ajax({
        url: '/grading/api/update-homework-type/',
        method: 'POST',
        headers: {
            'X-CSRFToken': window.getCSRFToken()
        },
        data: {
            course_name: window.currentCourse,
            folder_name: folderName,
            homework_type: homeworkType
        },
        success: function(response) {
            if (response.success) {
                console.log('作业类型已更新:', response);
                
                // 隐藏保存中状态
                jQuery('#savingStatus').hide();
                
                // 显示保存成功状态
                jQuery('#savedStatus').show();
                
                // 更新节点数据
                const tree = jQuery('#directory-tree').jstree(true);
                const node = tree.get_node(nodeId);
                if (node) {
                    node.data.homework_type = response.homework.homework_type;
                    node.data.homework_type_display = response.homework.homework_type_display;
                }
                
                // 清除所有标签
                jQuery('.homework-type-badge').remove();
                
                // 重新渲染标签
                window.addHomeworkTypeLabels();
                
                // 1秒后自动关闭模态框
                setTimeout(function() {
                    modal.hide();
                }, 1000);
            } else {
                // 隐藏保存中状态
                jQuery('#savingStatus').hide();
                alert('更新失败：' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('更新作业类型失败:', error);
            console.error('XHR状态:', xhr.status);
            console.error('XHR响应:', xhr.responseText);
            console.error('状态文本:', xhr.statusText);
            
            // 隐藏保存中状态
            jQuery('#savingStatus').hide();
            
            let errorMessage = '更新失败';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            } else if (xhr.responseText) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.message) {
                        errorMessage = response.message;
                    }
                } catch (e) {
                    errorMessage = xhr.responseText;
                }
            }
            
            alert('更新失败：' + errorMessage);
        }
    });
};
