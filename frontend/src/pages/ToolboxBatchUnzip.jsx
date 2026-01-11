import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

export default function ToolboxBatchUnzip() {
  const [sourceDirectory, setSourceDirectory] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [fileType, setFileType] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [currentPath, setCurrentPath] = useState('/')
  const [items, setItems] = useState([])
  const [dirError, setDirError] = useState('')
  const [dirLoading, setDirLoading] = useState(false)

  const parentPath = useMemo(() => {
    if (!currentPath || currentPath === '/') return null
    const idx = currentPath.lastIndexOf('/')
    if (idx <= 0) return '/'
    return currentPath.slice(0, idx)
  }, [currentPath])

  const openModal = () => {
    setCurrentPath(sourceDirectory || '/')
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

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const response = await apiFetch('/toolbox/api/batch-unzip/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ source_directory: sourceDirectory, file_type: fileType }),
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '解压失败')
      }
      setResult(data.result)
    } catch (err) {
      setError(err.message || '解压失败')
    } finally {
      setLoading(false)
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
              <li className="breadcrumb-item active">批量解压缩</li>
            </ol>
          </nav>
          <h1 className="mb-3">批量解压缩</h1>
          <p className="text-muted">
            指定目录后，会按压缩文件名创建子目录并解压。
          </p>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0">解压设置</h5>
        </div>
        <div className="card-body">
          {error ? <div className="alert alert-danger">{error}</div> : null}
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
                  placeholder="例如: D:\\files\\archives"
                  required
                />
                <button type="button" className="btn btn-outline-secondary" onClick={openModal}>
                  选择目录
                </button>
              </div>
            </div>
            <div className="mb-3">
              <label htmlFor="file_type" className="form-label">
                解压类型
              </label>
              <select
                id="file_type"
                className="form-select"
                value={fileType}
                onChange={(event) => setFileType(event.target.value)}
              >
                <option value="all">全部</option>
                <option value="zip">ZIP</option>
                <option value="rar">RAR</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '处理中...' : '开始解压'}
            </button>
          </form>
        </div>
      </div>

      {result ? (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">执行结果</h5>
          </div>
          <div className="card-body">
            <div className="mb-3">
              目录: <code>{result.source_directory}</code>
            </div>
            <div className="mb-3">
              类型: <strong>{result.file_type === 'all' ? '全部' : result.file_type.toUpperCase()}</strong>
            </div>
            <div className="mb-3">
              共发现 {result.total_files} 个压缩文件，成功 {result.success_count} 个，失败{' '}
              {result.error_count} 个。
            </div>

            {result.processed && result.processed.length ? (
              <div className="table-responsive mb-4">
                <table className="table table-striped align-middle">
                  <thead>
                    <tr>
                      <th>压缩文件</th>
                      <th>解压目录</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.processed.map((item) => (
                      <tr key={item.file_name}>
                        <td className="text-break">{item.file_name}</td>
                        <td className="text-break">{item.extract_dir}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {result.errors && result.errors.length ? (
              <div>
                <h6>失败详情（{result.errors.length}）</h6>
                <div className="list-group">
                  {result.errors.map((item) => (
                    <div key={item.file_name} className="list-group-item list-group-item-warning">
                      <strong className="text-break">{item.file_name}</strong>
                      <div className="small text-danger mt-1">{item.error}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

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
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      setSourceDirectory(currentPath)
                      closeModal()
                    }}
                  >
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
