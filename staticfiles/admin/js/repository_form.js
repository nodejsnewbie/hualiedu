function generateNameFromUrl(url) {
    if (!url) return '';
    
    // 移除 .git 后缀
    url = url.replace(/\.git$/, '');
    
    // 如果是 SSH 格式
    if (url.startsWith('git@')) {
        // 获取最后一个冒号后的部分
        const repoPart = url.split(':').pop();
        // 获取最后一个斜杠后的部分
        return repoPart.split('/').pop();
    }
    
    // 如果是 HTTPS 格式
    if (url.startsWith('http://') || url.startsWith('https://')) {
        // 移除协议和域名部分
        const path = url.split('://').pop().split('/').pop();
        return path;
    }
    
    return url;
}

function updateRepoName(url) {
    if (!url) return;
    
    const nameInput = document.querySelector('input[name="name"]');
    if (!nameInput) return;
    
    // 只有当名称输入框为空时才自动填充
    if (!nameInput.value) {
        const generatedName = generateNameFromUrl(url);
        nameInput.value = generatedName;
    }
}

// 页面加载完成后，如果 URL 字段已有值，自动填充名称
document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.querySelector('input[name="url"]');
    if (urlInput && urlInput.value) {
        updateRepoName(urlInput.value);
    }
    
    // 添加 URL 输入框的监听器
    urlInput.addEventListener('input', function() {
        updateRepoName(this.value);
    });
}); 