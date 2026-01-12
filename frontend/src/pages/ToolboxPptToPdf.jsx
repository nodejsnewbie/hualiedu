import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  if (status === 'processing') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-600'
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
    const seed = target === 'source' ? sourceDirectory || '/' : outputDirectory || '/'
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
    <div className="min-h-screen">
      <div className="page-shell">
        <div className="mb-6">
          <nav className="text-xs text-slate-500">
            <Link to="/toolbox" className="hover:text-slate-700">
              工具箱
            </Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700">PPT 转 PDF</span>
          </nav>
          <h1 className="mt-3 text-2xl font-semibold text-slate-900">PPT 转 PDF</h1>
        </div>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">批量转换设置</h2>
            {error ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}
            {message ? (
              <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {message}
              </div>
            ) : null}

            <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="source_directory" className="text-sm font-medium text-slate-700">
                  源目录路径
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  <input
                    type="text"
                    className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    id="source_directory"
                    value={sourceDirectory}
                    onChange={(event) => setSourceDirectory(event.target.value)}
                    placeholder="例如：D:\\files\\ppt"
                    required
                  />
                  <button
                    className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                    type="button"
                    onClick={() => openModal('source')}
                  >
                    选择目录
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="output_directory" className="text-sm font-medium text-slate-700">
                  输出目录路径
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  <input
                    type="text"
                    className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    id="output_directory"
                    value={outputDirectory}
                    onChange={(event) => setOutputDirectory(event.target.value)}
                    placeholder="例如：D:\\files\\pdf"
                    required
                  />
                  <button
                    className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                    type="button"
                    onClick={() => openModal('output')}
                  >
                    选择目录
                  </button>
                </div>
              </div>

              <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-sky-700">
                <ul className="list-disc space-y-1 pl-4">
                  <li>自动扫描源目录中的 .ppt/.pptx 文件。</li>
                  <li>转换后的 PDF 保存在输出目录。</li>
                  <li>需确保已安装 LibreOffice。</li>
                </ul>
              </div>

              <button
                type="submit"
                className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                开始转换
              </button>
            </form>
          </section>

          <div className="space-y-6">
            <section className="card-surface p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold text-slate-800">最近任务</h2>
                <button
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                  type="button"
                  onClick={loadTasks}
                >
                  刷新
                </button>
              </div>
              <div className="mt-4">
                {loadingTasks ? (
                  <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
                    正在加载任务...
                  </div>
                ) : tasks.length === 0 ? (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    暂无任务记录。
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                      <div key={task.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                        <div className="flex items-center justify-between">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(task.status)}`}>
                            {task.status_display}
                          </span>
                          <span className="text-xs text-slate-500">
                            {new Date(task.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-slate-600">{task.task_type_display}</div>
                        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white">
                          <div
                            className="h-full rounded-full bg-slate-900"
                            style={{ width: `${task.progress_percentage}%` }}
                            role="progressbar"
                            aria-valuenow={task.progress_percentage}
                            aria-valuemin="0"
                            aria-valuemax="100"
                          />
                        </div>
                        <div className="mt-2 text-xs text-slate-500">
                          {task.processed_files}/{task.total_files} 文件
                        </div>
                        <Link
                          to={`/toolbox/tasks/${task.id}`}
                          className="mt-2 inline-flex rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-white"
                        >
                          查看详情
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

            <section className="card-surface p-5">
              <h2 className="text-base font-semibold text-slate-800">系统要求</h2>
              <ul className="mt-3 space-y-2 text-xs text-slate-500">
                <li>已安装 LibreOffice</li>
                <li>目标目录有读写权限</li>
                <li>磁盘空间充足</li>
              </ul>
            </section>
          </div>
        </div>
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-10">
          <div className="w-full max-w-3xl rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-800">选择目录</h3>
              <button
                type="button"
                className="text-sm text-slate-500 hover:text-slate-700"
                onClick={closeModal}
              >
                关闭
              </button>
            </div>
            <div className="px-6 py-5">
              <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                <span className="font-semibold text-slate-700">当前路径：</span>
                <span className="flex-1 break-all">{currentPath}</span>
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-white"
                  onClick={() => parentPath && loadDirectory(parentPath)}
                  disabled={!parentPath}
                >
                  上一级
                </button>
              </div>

              {dirError ? (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {dirError}
                </div>
              ) : null}
              {dirLoading ? (
                <div className="mt-4 text-center text-sm text-slate-500">正在加载...</div>
              ) : (
                <div className="mt-4 space-y-2">
                  {items.map((item) => (
                    <button
                      key={item.path}
                      type="button"
                      className="flex w-full items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      onClick={() => item.type === 'directory' && loadDirectory(item.path)}
                    >
                      <span>
                        {item.type === 'directory' ? '[DIR]' : '[FILE]'} {item.name}
                      </span>
                      <span className="text-xs text-slate-400">{item.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                onClick={closeModal}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800"
                onClick={handleSelectDirectory}
              >
                选择当前目录
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
