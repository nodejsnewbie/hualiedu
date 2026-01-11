document.addEventListener('DOMContentLoaded', function () {
  // 创建目录选择按钮
  const repoBaseDirInput = document.querySelector('#id_repo_base_dir');
  const browseButton = document.createElement('button');
  browseButton.type = 'button';
  browseButton.className = 'button';
  browseButton.innerHTML = '<i class="fas fa-folder-open"></i> 浏览目录';
  browseButton.style.marginLeft = '10px';
  repoBaseDirInput.parentNode.insertBefore(browseButton, repoBaseDirInput.nextSibling);

  // 创建模态对话框
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'directoryModal';
  modal.innerHTML = `
          <div class="modal-dialog modal-lg">
              <div class="modal-content">
                  <div class="modal-header">
                      <h5 class="modal-title">选择仓库基础目录</h5>
                      <button type="button" class="close" data-dismiss="modal">&times;</button>
                  </div>
                  <div class="modal-body">
                      <div class="alert alert-info">
                          请选择一个相对路径作为仓库基础目录。建议选择用户主目录下的目录。
                      </div>
                      <div class="current-path mb-3">
                          <strong>当前路径：</strong>
                          <span id="currentPath"></span>
                      </div>
                      <div class="directory-list" style="max-height: 400px; overflow-y: auto;">
                          <div class="list-group" id="directoryList"></div>
                      </div>
                      <div class="selected-path mt-3">
                          <strong>已选择路径：</strong>
                          <span id="selectedPath"></span>
                      </div>
                  </div>
                  <div class="modal-footer">
                      <button type="button" class="btn btn-secondary" data-dismiss="modal">取消</button>
                      <button type="button" class="btn btn-primary" id="confirmSelection">确认选择</button>
                  </div>
              </div>
          </div>
      `;
  document.body.appendChild(modal);

  // 加载目录内容
  function loadDirectory(path = '') {
    fetch(`/admin/grading/globalconfig/browse-directory/?dir=${encodeURIComponent(path)}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }

        // 更新当前路径显示
        document.getElementById('currentPath').textContent = data.current_path;

        // 清空目录列表
        const directoryList = document.getElementById('directoryList');
        directoryList.innerHTML = '';

        // 添加返回上级目录按钮
        if (path) {
          const parentDir = path.split('/').slice(0, -1).join('/');
          const parentItem = document.createElement('a');
          parentItem.href = '#';
          parentItem.className = 'list-group-item list-group-item-action';
          parentItem.innerHTML = '<i class="fas fa-level-up-alt"></i> 返回上级目录';
          parentItem.onclick = (e) => {
            e.preventDefault();
            loadDirectory(parentDir);
          };
          directoryList.appendChild(parentItem);
        }

        // 添加目录项
        data.items.forEach(item => {
          const listItem = document.createElement('a');
          listItem.href = '#';
          listItem.className = 'list-group-item list-group-item-action';
          listItem.innerHTML = `<i class="fas fa-folder"></i> ${item.name}`;
          listItem.onclick = (e) => {
            e.preventDefault();
            loadDirectory(item.path);
          };
          directoryList.appendChild(listItem);
        });
      })
      .catch(error => {
        console.error('加载目录失败:', error);
        alert('加载目录失败，请重试');
      });
  }

  // 打开模态对话框
  browseButton.onclick = function () {
    $('#directoryModal').modal('show');
    loadDirectory();
  };

  // 确认选择
  document.getElementById('confirmSelection').onclick = function () {
    const currentPath = document.getElementById('currentPath').textContent;
    const homeDir = '/Users/linyuan';  // 替换为实际的用户主目录
    let relativePath = currentPath;

    if (currentPath.startsWith(homeDir)) {
      relativePath = '~' + currentPath.slice(homeDir.length);
    }

    repoBaseDirInput.value = relativePath;
    $('#directoryModal').modal('hide');
  };

  // 监听目录选择
  document.getElementById('directoryList').addEventListener('click', function (e) {
    const currentPath = document.getElementById('currentPath').textContent;
    const homeDir = '/Users/linyuan';  // 替换为实际的用户主目录
    let relativePath = currentPath;

    if (currentPath.startsWith(homeDir)) {
      relativePath = '~' + currentPath.slice(homeDir.length);
    }

    document.getElementById('selectedPath').textContent = relativePath;
  });
});
