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
    <div className="min-h-screen">
      <div className="page-shell">
        <div className="mb-6">
          <nav className="text-xs text-slate-500">
            <Link to="/toolbox" className="hover:text-slate-700">
              工具箱
            </Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700">批量解压缩</span>
          </nav>
          <h1 className="mt-3 text-2xl font-semibold text-slate-900">批量解压缩</h1>
          <p className="mt-2 text-sm text-slate-500">
            指定目录后，将按压缩文件名创建子目录并解压。
          </p>
        </div>

        <section className="card-surface p-5">
          <h2 className="text-base font-semibold text-slate-800">解压设置</h2>
          {error ? (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
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
                  placeholder="例如：D:\\files\\archives"
                  required
                />
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                  onClick={openModal}
                >
                  选择目录
                </button>
              </div>
            </div>
            <div>
              <label htmlFor="file_type" className="text-sm font-medium text-slate-700">
                解压类型
              </label>
              <select
                id="file_type"
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                value={fileType}
                onChange={(event) => setFileType(event.target.value)}
              >
                <option value="all">全部</option>
                <option value="zip">ZIP</option>
                <option value="rar">RAR</option>
              </select>
            </div>
            <button
              type="submit"
              className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              disabled={loading}
            >
              {loading ? '处理中...' : '开始解压'}
            </button>
          </form>
        </section>

        {result ? (
          <section className="mt-6 card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">执行结果</h2>
            <div className="mt-3 text-sm text-slate-600">
              目录：<span className="break-all text-slate-800">{result.source_directory}</span>
            </div>
            <div className="mt-1 text-sm text-slate-600">
              类型：<span className="font-semibold text-slate-800">{result.file_type === 'all' ? '全部' : result.file_type.toUpperCase()}</span>
            </div>
            <div className="mt-3 text-sm text-slate-600">
              共发现 {result.total_files} 个压缩文件，成功 {result.success_count} 个，失败 {result.error_count} 个。
            </div>

            {result.processed && result.processed.length ? (
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-xs">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">压缩文件</th>
                      <th className="px-3 py-2 text-left font-medium">解压目录</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.processed.map((item) => (
                      <tr key={item.file_name} className="text-slate-700">
                        <td className="px-3 py-2 break-all">{item.file_name}</td>
                        <td className="px-3 py-2 break-all">{item.extract_dir}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {result.errors && result.errors.length ? (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-rose-600">失败详情（{result.errors.length}）</h3>
                <div className="mt-2 space-y-2">
                  {result.errors.map((item) => (
                    <div key={item.file_name} className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                      <div className="font-semibold break-all">{item.file_name}</div>
                      <div className="mt-1 text-rose-500">{item.error}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
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
      ) : null}
    </div>
  )
}
