// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  // 初始化函数
  function initSSHKeyInput() {
    console.log('SSH Key Input script loaded');

    // 获取所有相关元素
    const sshKeyTextarea = document.querySelector('textarea[name="ssh_key"]');
    const sshKeyFileInput = document.querySelector('input[name="ssh_key_file"]');

    if (!sshKeyTextarea) {
      console.error('SSH key textarea not found');
      return;
    }

    // 确保文本框可见
    sshKeyTextarea.style.display = 'block';
    sshKeyTextarea.style.width = '100%';
    sshKeyTextarea.style.height = '200px';
    sshKeyTextarea.style.fontFamily = 'monospace';
    sshKeyTextarea.style.marginBottom = '10px';

    // 处理文件上传
    function handleFileUpload(file) {
      if (!file) {
        console.log('No file selected');
        return;
      }

      console.log('Processing file:', file.name);
      const reader = new FileReader();

      reader.onload = function (e) {
        const content = e.target.result;
        console.log('File content read, length:', content.length);

        // 验证 SSH 密钥格式
        if (!isValidSSHKey(content)) {
          showError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件');
          sshKeyFileInput.value = '';
          sshKeyTextarea.value = '';
          return;
        }

        try {
          // 设置内容
          sshKeyTextarea.value = content;
          // 触发 change 事件
          const event = new Event('change', { bubbles: true });
          sshKeyTextarea.dispatchEvent(event);
          console.log('SSH key content set successfully');

        } catch (error) {
          console.error('Error setting textarea value:', error);
          showError('设置私钥内容失败');
        }
      };

      reader.onerror = function (error) {
        console.error('Error reading file:', error);
        showError('读取文件失败');
        sshKeyFileInput.value = '';
        sshKeyTextarea.value = '';
      };

      try {
        reader.readAsText(file);
      } catch (error) {
        console.error('Error starting file read:', error);
        showError('启动文件读取失败');
      }
    }

    // 绑定文件上传事件
    if (sshKeyFileInput) {
      sshKeyFileInput.onchange = function () {
        const file = this.files[0];
        handleFileUpload(file);
      };
    }

    // 验证 SSH 密钥格式
    function isValidSSHKey(content) {
      const trimmedContent = content.trim();
      return trimmedContent.startsWith('-----BEGIN') &&
        trimmedContent.endsWith('PRIVATE KEY-----') &&
        trimmedContent.includes('KEY-----');
    }

    // 显示错误信息
    function showError(message) {
      const existingError = document.querySelector('.ssh-key-error');
      if (existingError) {
        existingError.remove();
      }

      const errorDiv = document.createElement('div');
      errorDiv.className = 'ssh-key-error';
      errorDiv.textContent = message;
      Object.assign(errorDiv.style, {
        color: '#ba2121',
        marginTop: '5px',
        fontSize: '13px',
        padding: '8px',
        backgroundColor: '#fff0f0',
        border: '1px solid #ffcfcf',
        borderRadius: '4px',
        marginBottom: '10px'
      });

      const fileInput = document.querySelector('input[name="ssh_key_file"]');
      if (fileInput) {
        fileInput.parentNode.insertBefore(errorDiv, fileInput.nextSibling);
      }

      setTimeout(function () {
        errorDiv.style.opacity = '0';
        errorDiv.style.transition = 'opacity 0.5s';
        setTimeout(function () {
          if (errorDiv.parentNode) {
            errorDiv.remove();
          }
        }, 500);
      }, 5000);
    }

    // 监听文本框的值变化
    sshKeyTextarea.addEventListener('input', function () {
      if (this.value.trim()) {
        this.style.borderColor = '#28a745';
      } else {
        this.style.borderColor = '#ccc';
      }
    });

    // 如果文本框已有内容，更新状态
    if (sshKeyTextarea.value.trim()) {
      sshKeyTextarea.style.borderColor = '#28a745';
    }

    // 表单提交处理
    const form = document.getElementById('globalconfig_form');
    if (form) {
      form.onsubmit = function (e) {
        e.preventDefault();
        if (confirm('是否要立即克隆所有未克隆的仓库？')) {
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = '_clone_repositories';
          input.value = '1';
          this.appendChild(input);
        }
        this.submit();
      };
    }
  }

  // 初始化
  initSSHKeyInput();
});
