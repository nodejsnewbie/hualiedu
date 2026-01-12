import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  if (status === 'processing') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

export default function ToolboxTaskList() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadTasks = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/toolbox/api/tasks/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载任务失败')
      }
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err.message || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const deleteTask = async (taskId) => {
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
    setTasks((prev) => prev.filter((task) => task.id !== taskId))
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
            <span className="text-slate-700">任务列表</span>
          </nav>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">任务列表</h1>
              <p className="mt-1 text-sm text-slate-500">查看全部转换任务。</p>
            </div>
            <Link
              to="/toolbox/ppt-to-pdf"
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              新建任务
            </Link>
          </div>
        </div>

        <section className="card-surface p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-800">全部转换任务</h2>
            <button
              className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              type="button"
              onClick={loadTasks}
            >
              刷新
            </button>
          </div>

          <div className="mt-4">
            {error ? (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}
            {message ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {message}
              </div>
            ) : null}
            {loading ? (
              <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
                正在加载任务...
              </div>
            ) : tasks.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无任务记录。
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">任务类型</th>
                      <th className="px-4 py-2 text-left font-medium">状态</th>
                      <th className="px-4 py-2 text-left font-medium">进度</th>
                      <th className="px-4 py-2 text-left font-medium">文件统计</th>
                      <th className="px-4 py-2 text-left font-medium">创建时间</th>
                      <th className="px-4 py-2 text-left font-medium">更新时间</th>
                      <th className="px-4 py-2 text-left font-medium"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {tasks.map((task) => (
                      <tr key={task.id} className="text-slate-700">
                        <td className="px-4 py-2 font-medium text-slate-800">{task.task_type_display}</td>
                        <td className="px-4 py-2">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(task.status)}`}>
                            {task.status_display}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          <div className="h-2 w-40 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-slate-900"
                              style={{ width: `${task.progress_percentage}%` }}
                              role="progressbar"
                              aria-valuenow={task.progress_percentage}
                              aria-valuemin="0"
                              aria-valuemax="100"
                            />
                          </div>
                          <div className="mt-1 text-xs text-slate-500">{task.progress_percentage}%</div>
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-600">
                          <div>总数：{task.total_files}</div>
                          <div>成功：<span className="text-emerald-600">{task.success_files}</span></div>
                          <div>失败：<span className="text-rose-600">{task.failed_files}</span></div>
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-500">
                          {new Date(task.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-500">
                          {new Date(task.updated_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex flex-wrap gap-2">
                            <Link
                              to={`/toolbox/tasks/${task.id}`}
                              className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                            >
                              详情
                            </Link>
                            <button
                              type="button"
                              className="rounded-lg border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                              onClick={() => deleteTask(task.id)}
                            >
                              删除
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
