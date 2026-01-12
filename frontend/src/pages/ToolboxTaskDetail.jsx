import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  if (status === 'processing') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

const statusLabel = (status) => {
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'processing') return '处理中'
  if (status === 'pending') return '等待中'
  return status || ''
}

export default function ToolboxTaskDetail() {
  const { taskId } = useParams()
  const [task, setTask] = useState(null)
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  const loadDetail = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch(`/toolbox/api/tasks/${taskId}/`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载任务失败')
      }
      setTask(data.task)
      setLogs(data.logs || [])
    } catch (err) {
      setError(err.message || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDetail()
  }, [taskId])

  useEffect(() => {
    if (!task || task.status !== 'processing') return undefined
    const interval = setInterval(async () => {
      const response = await apiFetch(`/toolbox/api/tasks/${taskId}/status/`)
      const data = await response.json().catch(() => null)
      if (response.ok && data && data.status === 'success') {
        setTask((prev) => ({ ...(prev || {}), ...data.data }))
        if (data.data.status !== 'processing') {
          clearInterval(interval)
          loadDetail()
        }
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [task, taskId])

  const deleteTask = async () => {
    setMessage('')
    const confirmed = window.confirm('确定要删除该任务吗？')
    if (!confirmed) return
    const response = await apiFetch(`/toolbox/api/tasks/${taskId}/delete/`, { method: 'POST' })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '删除任务失败')
      return
    }
    setMessage('任务已删除')
  }

  if (loading) {
    return (
      <div className="min-h-screen">
        <div className="mx-auto w-full max-w-4xl px-4 py-8">
          <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
            正在加载任务...
          </div>
        </div>
      </div>
    )
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
            <Link to="/toolbox/tasks" className="hover:text-slate-700">
              任务列表
            </Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700">任务详情</span>
          </nav>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-2xl font-semibold text-slate-900">任务详情</h1>
            <div className="flex flex-wrap gap-2">
              <Link
                to="/toolbox/tasks"
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                返回列表
              </Link>
              <button
                type="button"
                className="rounded-lg border border-rose-200 px-4 py-2 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                onClick={deleteTask}
              >
                删除任务
              </button>
            </div>
          </div>
        </div>

        {error ? (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}
        {message ? (
          <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {message}
          </div>
        ) : null}

        {!task ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            任务不存在。
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <div className="space-y-6">
              <section className="card-surface p-5">
                <h2 className="text-base font-semibold text-slate-800">任务信息</h2>
                <div className="mt-4 grid gap-4 md:grid-cols-2 text-sm text-slate-700">
                  <div className="space-y-2">
                    <p>
                      <span className="font-semibold text-slate-600">任务类型：</span>
                      {task.task_type_display}
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">任务状态：</span>
                      <span className={`ml-2 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(task.status)}`}>
                        {statusLabel(task.status)}
                      </span>
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">创建时间：</span>
                      {new Date(task.created_at).toLocaleString()}
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">更新时间：</span>
                      {new Date(task.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p>
                      <span className="font-semibold text-slate-600">源目录：</span>
                      <span className="break-all text-slate-800">{task.source_directory}</span>
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">输出目录：</span>
                      <span className="break-all text-slate-800">{task.output_directory}</span>
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">总文件数：</span>
                      {task.total_files}
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">已处理：</span>
                      {task.processed_files}
                    </p>
                  </div>
                </div>
                {task.error_message ? (
                  <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {task.error_message}
                  </div>
                ) : null}
              </section>

              <section className="card-surface p-5">
                <h2 className="text-base font-semibold text-slate-800">转换进度</h2>
                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
                    <div className="text-2xl font-semibold text-slate-900">{task.total_files}</div>
                    <div className="text-xs text-slate-500">总文件数</div>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
                    <div className="text-2xl font-semibold text-emerald-600">{task.success_files}</div>
                    <div className="text-xs text-slate-500">成功转换</div>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
                    <div className="text-2xl font-semibold text-rose-600">{task.failed_files}</div>
                    <div className="text-xs text-slate-500">转换失败</div>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
                    <span>总体进度</span>
                    <span>{task.progress_percentage}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-900"
                      style={{ width: `${task.progress_percentage}%` }}
                      role="progressbar"
                      aria-valuenow={task.progress_percentage}
                      aria-valuemin="0"
                      aria-valuemax="100"
                    />
                  </div>
                </div>
              </section>

              <section className="card-surface p-5">
                <h2 className="text-base font-semibold text-slate-800">转换日志</h2>
                {logs.length === 0 ? (
                  <div className="mt-4 text-sm text-slate-500">暂无转换日志。</div>
                ) : (
                  <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                    <table className="min-w-full text-xs">
                      <thead className="bg-slate-100 text-slate-600">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">文件名</th>
                          <th className="px-3 py-2 text-left font-medium">状态</th>
                          <th className="px-3 py-2 text-left font-medium">时间</th>
                          <th className="px-3 py-2 text-left font-medium">错误信息</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {logs.map((log) => (
                          <tr key={log.id} className="text-slate-700">
                            <td className="px-3 py-2">{log.file_name}</td>
                            <td className="px-3 py-2">
                              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(log.status)}`}>
                                {log.status_display}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-xs text-slate-500">
                              {new Date(log.created_at).toLocaleTimeString()}
                            </td>
                            <td className="px-3 py-2 text-xs text-slate-500">{log.error_message || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>

            <div className="space-y-6">
              <section className="card-surface p-5">
                <h2 className="text-base font-semibold text-slate-800">实时状态</h2>
                <div className="mt-4 space-y-2 text-sm text-slate-700">
                  <p>
                    <span className="font-semibold text-slate-600">当前状态：</span>
                    <span className={`ml-2 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(task.status)}`}>
                      {statusLabel(task.status)}
                    </span>
                  </p>
                  <p>
                    <span className="font-semibold text-slate-600">进度：</span>
                    {task.progress_percentage}%
                  </p>
                  <p>
                    <span className="font-semibold text-slate-600">已处理：</span>
                    {task.processed_files}/{task.total_files}
                  </p>
                </div>
              </section>

              <section className="card-surface p-5">
                <h2 className="text-base font-semibold text-slate-800">操作指南</h2>
                <ul className="mt-3 space-y-2 text-xs text-slate-500">
                  <li>转换完成后 PDF 保存在输出目录。</li>
                  <li>任务处理中会自动刷新状态。</li>
                  <li>失败时请确认 LibreOffice 安装情况。</li>
                </ul>
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
