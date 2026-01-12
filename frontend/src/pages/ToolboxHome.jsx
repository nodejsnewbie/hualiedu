import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  if (status === 'processing') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

export default function ToolboxHome() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTasks = async () => {
    setLoading(true)
    setError('')
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
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  return (
    <div className="min-h-screen">
      <div className="page-shell">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">工具箱</h1>
          <p className="mt-1 text-sm text-slate-500">常用作业与文件处理工具入口。</p>
        </header>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">PPT 转 PDF</h2>
            <p className="mt-2 text-sm text-slate-500">批量将目录中的 PPT 文件转换为 PDF。</p>
            <Link
              to="/toolbox/ppt-to-pdf"
              className="mt-4 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              开始转换
            </Link>
          </div>

          <div className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">任务管理</h2>
            <p className="mt-2 text-sm text-slate-500">查看并管理转换任务。</p>
            <Link
              to="/toolbox/tasks"
              className="mt-4 inline-flex rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              查看任务
            </Link>
          </div>

          <div className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">作业成绩写入</h2>
            <p className="mt-2 text-sm text-slate-500">将作业成绩写入成绩登记册。</p>
            <Link
              to="/toolbox/assignment-grade-import"
              className="mt-4 inline-flex rounded-lg border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50"
            >
              立即写入
            </Link>
          </div>

          <div className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">批量解压缩</h2>
            <p className="mt-2 text-sm text-slate-500">按压缩文件名自动创建目录并解压。</p>
            <Link
              to="/toolbox/batch-unzip"
              className="mt-4 inline-flex rounded-lg border border-amber-200 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:border-amber-300 hover:bg-amber-50"
            >
              开始解压
            </Link>
          </div>
        </div>

        <section className="mt-8 card-surface p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-slate-800">最近任务</h2>
              <p className="mt-1 text-xs text-slate-500">最近 10 条任务记录。</p>
            </div>
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
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
                      <th className="px-4 py-2 text-left font-medium">创建时间</th>
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
                              aria-valuenow={task.progress_percentage}
                              aria-valuemin="0"
                              aria-valuemax="100"
                              role="progressbar"
                            />
                          </div>
                          <div className="mt-1 text-xs text-slate-500">{task.progress_percentage}%</div>
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-500">
                          {new Date(task.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-2">
                          <Link
                            to={`/toolbox/tasks/${task.id}`}
                            className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                          >
                            查看
                          </Link>
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
