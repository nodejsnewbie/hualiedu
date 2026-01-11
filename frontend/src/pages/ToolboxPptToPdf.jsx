import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'secondary'
}

export default function ToolboxPptToPdf() {
  const [sourceDirectory, setSourceDirectory] = useState('')
  const [outputDirectory, setOutputDirectory] = useState('')
  const [tasks, setTasks] = useState([])
  const [loadingTasks, setLoadingTasks] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [browseTarget, setBrowseTarget] = useState('source')
  const [currentPath, setCurrentPath] = useState('/')
  const [items, setItems] = useState([])
  const [dirError, setDirError] = useState('')
  const [dirLoading, setDirLoading] = useState(false)

  const loadTasks = async () => {
    setLoadingTasks(true)
    try {
      const response = await apiFetch('/toolbox/api/tasks/?limit=10')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载任务失败')
      }
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err.message || '加载任务失败')
    } finally {
      setLoadingTasks(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const openModal = (target) => {
    setBrowseTarget(target)
    const seed =
      target === 'source'
        ? sourceDirectory || '/'
        : outputDirectory || '/'
    setCurrentPath(seed)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setItems([])
    setDirError('')
  }

  const loadDirectory = async (path) => {
    setDirLoading(true)
    setDirError('')
    try {
      const response = await apiFetch(`/toolbox/api/browse-directory/?path=${encodeURIComponent(path)}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status !== 'success') {
        throw new Error((data && data.message) || '加载目录失败')
      }
      setCurrentPath(data.data.current_path)
      setItems(data.data.items || [])
    } catch (err) {
      setDirError(err.message || '加载目录失败')
    } finally {
      setDirLoading(false)
    }
  }

  useEffect(() => {
    if (modalOpen) {
      loadDirectory(currentPath || '/')
    }
  }, [modalOpen])

  const parentPath = useMemo(() => {
    if (!currentPath || currentPath === '/') return null
    const idx = currentPath.lastIndexOf('/')
    if (idx <= 0) return '/'
    return currentPath.slice(0, idx)
  }, [currentPath])

  const handleSelectDirectory = () => {
    if (browseTarget === 'source') {
      setSourceDirectory(currentPath)
    } else {
      setOutputDirectory(currentPath)
    }
    closeModal()
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setMessage('')
    try {
      const response = await apiFetch('/toolbox/api/tasks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          task_type: 'ppt_to_pdf',
          source_directory: sourceDirectory,
          output_directory: outputDirectory,
        }),
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '创建任务失败')
      }
      setMessage('任务已创建，正在后台转换')
      setSourceDirectory('')
      setOutputDirectory('')
      await loadTasks()
    } catch (err) {
      setError(err.message || '创建任务失败')
    }
  }

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item">
                <Link to="/toolbox">工具箱</Link>
              </li>
              <li className="breadcrumb-item active">PPT 转 PDF</li>
            </ol>
          </nav>
          <h1 className="mb-4">PPT 转 PDF</h1>
        </div>
      </div>

      <div className="row">
        <div className="col-md-8">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">批量转换设置</h5>
            </div>
            <div className="card-body">
              {error ? <div className="alert alert-danger">{error}</div> : null}
              {message ? <div className="alert alert-success">{message}</div> : null}
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="source_directory" className="form-label">
                    源目录路径
                  </label>
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      id="source_directory"
                      value={sourceDirectory}
                      onChange={(event) => setSourceDirectory(event.target.value)}
                      placeholder="例如: D:\\files\\ppt"
                      required
                    />
                    <button
                      className="btn btn-outline-secondary"
                      type="button"
                      onClick={() => openModal('source')}
                    >
                      选择目录
                    </button>
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="output_directory" className="form-label">
                    输出目录路径
                  </label>
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      id="output_directory"
                      value={outputDirectory}
                      onChange={(event) => setOutputDirectory(event.target.value)}
                      placeholder="例如: D:\\files\\pdf"
                      required
                    />
                    <button
                      className="btn btn-outline-secondary"
                      type="button"
                      onClick={() => openModal('output')}
                    >
                      选择目录
                    </button>
                  </div>
                </div>

                <div className="alert alert-info">
                  <ul className="mb-0">
                    <li>自动扫描源目录下的 .ppt/.pptx 文件</li>
                    <li>转换后 PDF 保存在输出目录</li>
                    <li>需要确保已安装 LibreOffice</li>
                  </ul>
                </div>

                <button type="submit" className="btn btn-primary btn-lg">
                  开始转换
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">最近任务</h5>
              <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadTasks}>
                刷新
              </button>
            </div>
            <div className="card-body">
              {loadingTasks ? (
                <div className="alert alert-info">正在加载任务...</div>
              ) : tasks.length === 0 ? (
                <p className="text-muted text-center">暂无任务记录</p>
              ) : (
                tasks.map((task) => (
                  <div key={task.id} className="border-bottom pb-2 mb-2">
                    <div className="d-flex justify-content-between align-items-center">
                      <span className={`badge bg-${statusBadgeClass(task.status)}`}>
                        {task.status_display}
                      </span>
                      <small className="text-muted">
                        {new Date(task.created_at).toLocaleString()}
                      </small>
                    </div>
                    <div className="mt-1">
                      <small className="text-muted">{task.task_type_display}</small>
                    </div>
                    <div className="progress mt-1" style={{ height: '6px' }}>
                      <div
                        className="progress-bar"
                        role="progressbar"
                        style={{ width: `${task.progress_percentage}%` }}
                        aria-valuenow={task.progress_percentage}
                        aria-valuemin="0"
                        aria-valuemax="100"
                      />
                    </div>
                    <div className="mt-1">
                      <small className="text-muted">
                        {task.processed_files}/{task.total_files} 文件
                      </small>
                    </div>
                    <div className="mt-2">
                      <Link to={`/toolbox/tasks/${task.id}`} className="btn btn-sm btn-outline-primary">
                        查看详情
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="card mt-3">
            <div className="card-header">
              <h5 className="mb-0">系统要求</h5>
            </div>
            <div className="card-body">
              <ul className="list-unstyled mb-0">
                <li>LibreOffice 已安装</li>
                <li>目标目录有读写权限</li>
                <li>磁盘空间充足</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {modalOpen ? (
        <>
          <div className="modal fade show d-block" tabIndex="-1" role="dialog">
            <div className="modal-dialog modal-lg" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">选择目录</h5>
                  <button type="button" className="btn-close" aria-label="Close" onClick={closeModal} />
                </div>
                <div className="modal-body">
                  <div className="input-group mb-3">
                    <span className="input-group-text">当前路径</span>
                    <input type="text" className="form-control" value={currentPath} readOnly />
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => parentPath && loadDirectory(parentPath)}
                      disabled={!parentPath}
                    >
                      上一级
                    </button>
                  </div>
                  {dirError ? <div className="alert alert-danger">{dirError}</div> : null}
                  {dirLoading ? (
                    <div className="text-center">正在加载...</div>
                  ) : (
                    <div className="list-group">
                      {items.map((item) => (
                        <button
                          key={item.path}
                          type="button"
                          className="list-group-item list-group-item-action"
                          onClick={() => item.type === 'directory' && loadDirectory(item.path)}
                        >
                          {item.type === 'directory' ? '[DIR] ' : '[FILE] '}
                          {item.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={closeModal}>
                    取消
                  </button>
                  <button type="button" className="btn btn-primary" onClick={handleSelectDirectory}>
                    选择当前目录
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show" />
        </>
      ) : null}
    </div>
  )
}
