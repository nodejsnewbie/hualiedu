if (typeof jQuery === 'undefined' && typeof django !== 'undefined') {
  jQuery = django.jQuery;
}

(function ($) {
  $(document).ready(function () {
    console.log('SSH Key Input script loaded');

    $('.select-ssh-key').each(function () {
      const button = $(this);
      const wrapper = button.closest('.ssh-key-file-input-wrapper');
      const fileInput = wrapper.find('input[type="file"]');
      const fileNameSpan = wrapper.find('.ssh-key-file-name');
      const sshKeyTextarea = $('textarea[name="ssh_key"]');

      console.log('Elements found:', {
        button: button.length,
        fileInput: fileInput.length,
        fileNameSpan: fileNameSpan.length,
        sshKeyTextarea: sshKeyTextarea.length
      });

      button.on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.val('');
        fileInput.trigger('click');
      });

      fileInput.on('change', function () {
        const file = this.files[0];
        if (file) {
          console.log('File selected:', file.name);
          fileNameSpan.text(file.name).addClass('success');

          const reader = new FileReader();
          reader.onload = function (e) {
            const content = e.target.result;
            console.log('File content read, length:', content.length);

            if (!isValidSSHKey(content)) {
              showError('无效的 SSH 私钥格式，请确保上传的是有效的 SSH 私钥文件');
              fileInput.val('');
              fileNameSpan.text('').removeClass('success');
              return;
            }

            sshKeyTextarea.val(content);
            console.log('Content set to textarea');
          };

          reader.onerror = function (error) {
            console.error('Error reading file:', error);
            showError('读取文件失败：' + error);
            fileInput.val('');
            fileNameSpan.text('').removeClass('success');
          };

          reader.readAsText(file);
        } else {
          fileNameSpan.text('').removeClass('success');
        }
      });

      if (fileInput.val()) {
        fileNameSpan.text(fileInput.val().split('\\').pop().split('/').pop()).addClass('success');
      }
    });

    function isValidSSHKey(content) {
      const trimmedContent = content.trim();
      return trimmedContent.startsWith('-----BEGIN') &&
        trimmedContent.endsWith('PRIVATE KEY-----') &&
        trimmedContent.includes('KEY-----');
    }

    function showError(message) {
      $('.ssh-key-error').remove();

      const errorDiv = $('<div class="ssh-key-error"></div>')
        .text(message)
        .css({
          'color': '#ba2121',
          'margin-top': '5px',
          'font-size': '13px',
          'padding': '8px',
          'background-color': '#fff0f0',
          'border': '1px solid #ffcfcf',
          'border-radius': '4px',
          'margin-bottom': '10px'
        });

      wrapper.after(errorDiv);

      setTimeout(function () {
        errorDiv.fadeOut(function () {
          $(this).remove();
        });
      }, 5000);
    }

    $('#globalconfig_form').on('submit', function (e) {
      e.preventDefault();

      if (confirm('是否要立即克隆所有未克隆的仓库？')) {
        $(this).append('<input type="hidden" name="_clone_repositories" value="1">');
      }

      this.submit();
    });
  });
})(jQuery);
