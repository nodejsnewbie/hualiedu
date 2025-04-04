document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.querySelector('input[type="file"][name="ssh_key_file"]');
  if (fileInput) {
    // 获取默认路径
    const defaultPath = fileInput.getAttribute('data-initial-path');

    // 创建一个隐藏的 input 元素来存储实际的文件路径
    const pathInput = document.createElement('input');
    pathInput.type = 'hidden';
    pathInput.name = 'ssh_key_file_path';
    fileInput.parentNode.appendChild(pathInput);

    // 监听文件选择事件
    fileInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (file) {
        // 如果选择了文件，将完整路径保存到隐藏输入框
        pathInput.value = file.path || `${defaultPath}/${file.name}`;
      } else {
        pathInput.value = '';
      }
    });

    // 尝试设置默认目录
    try {
      fileInput.webkitdirectory = false;  // 禁用目录选择模式
      if ('showPicker' in fileInput) {
        const originalClick = fileInput.onclick;
        fileInput.onclick = async function (e) {
          e.preventDefault();
          try {
            const handle = await window.showOpenFilePicker({
              startIn: defaultPath,
              types: [
                {
                  description: 'SSH 私钥文件',
                  accept: {
                    'application/x-pem-file': ['.pem', '.key'],
                    'text/plain': ['.*']
                  }
                }
              ]
            });
            const file = await handle[0].getFile();
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            pathInput.value = `${defaultPath}/${file.name}`;
            fileInput.dispatchEvent(new Event('change'));
          } catch (err) {
            if (originalClick) originalClick.call(fileInput, e);
          }
        };
      }
    } catch (e) {
      console.warn('高级文件选择器API不可用，将使用标准文件选择器');
    }
  }
}); 