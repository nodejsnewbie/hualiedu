(function ($) {
  $(function () {
    console.log('SSH Key Input script loaded');

    // 为每个文件输入框添加点击事件
    $('.select-ssh-key').each(function () {
      const button = $(this);
      const wrapper = button.closest('.ssh-key-file-input-wrapper');
      const fileInput = wrapper.find('input[type="file"]');
      const fileNameSpan = wrapper.find('.ssh-key-file-name');

      // 点击按钮时触发文件选择
      button.on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.val(''); // 清除之前的选择
        fileInput.click();
      });

      // 当选择文件后更新显示
      fileInput.on('change', function () {
        const file = this.files[0];
        if (file) {
          fileNameSpan.text(file.name).addClass('success');
          // 自动填充文件内容到文本区域
          const reader = new FileReader();
          reader.onload = function (e) {
            $('textarea[name="ssh_key"]').val(e.target.result);
          };
          reader.readAsText(file);
        } else {
          fileNameSpan.text('').removeClass('success');
        }
      });

      // 如果有初始值，显示文件名
      if (fileInput.val()) {
        fileNameSpan.text(fileInput.val().split('\\').pop().split('/').pop()).addClass('success');
      }
    });
  });
})(django.jQuery);
