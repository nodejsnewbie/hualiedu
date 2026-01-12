import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function SemesterManagement() {
  const [semesters, setSemesters] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [form, setForm] = useState({ name: '', start_date: '', end_date: '', is_active: false })
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  const loadSemesters = async () => {
    setError('')
    const response = await apiFetch('/grading/api/semesters/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '加载学期失败')
      return
    }
    setSemesters(data.semesters || [])
    setDashboard(data.dashboard_info || null)
  }

  useEffect(() => {
    loadSemesters()
  }, [])

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const submitSemester = async (event) => {
    event.preventDefault()
    setError('')
    const payload = new URLSearchParams({
      name: form.name,
      start_date: form.start_date,
      end_date: form.end_date,
      is_active: form.is_active ? 'true' : 'false',
    })
    const response = await apiFetch('/grading/api/semesters/create/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '创建学期失败')
      return
    }
    setForm({ name: '', start_date: '', end_date: '', is_active: false })
    loadSemesters()
  }

  const saveEdit = async (event) => {
    event.preventDefault()
    if (!editing) return
    const payload = new URLSearchParams({
      name: editing.name,
      start_date: editing.start_date,
      end_date: editing.end_date,
      is_active: editing.is_active ? 'true' : 'false',
    })
    const response = await apiFetch(`/grading/api/semesters/${editing.id}/update/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '更新学期失败')
      return
    }
    setEditing(null)
    loadSemesters()
  }

  const deleteSemester = async (semester) => {
    if (!window.confirm(`删除学期“${semester.name}”？`)) {
      return
    }
    const response = await apiFetch(`/grading/api/semesters/${semester.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ force_delete: 'false' }),
    })
    const data = await response.json().catch(() => null)
    if (response.status === 409 && data && data.status === 'warning') {
      if (!window.confirm(`学期包含 ${data.courses_count} 门课程，是否强制删除？`)) {
        return
      }
      const retry = await apiFetch(`/grading/api/semesters/${semester.id}/delete/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ force_delete: 'true' }),
      })
      const retryData = await retry.json().catch(() => null)
      if (!retry.ok || (retryData && retryData.status !== 'success')) {
        setError((retryData && retryData.message) || '删除学期失败')
        return
      }
    } else if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '删除学期失败')
      return
    }
    loadSemesters()
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">学期管理</h1>
          <p className="mt-1 text-sm text-slate-500">创建与维护学期信息。</p>
        </header>

        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">创建学期</h2>
            <form className="mt-4 space-y-4" onSubmit={submitSemester}>
              <div>
                <label className="text-sm font-medium text-slate-700">名称</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">开始日期</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  type="date"
                  name="start_date"
                  value={form.start_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">结束日期</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  type="date"
                  name="end_date"
                  value={form.end_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                  type="checkbox"
                  name="is_active"
                  checked={form.is_active}
                  onChange={handleChange}
                />
                设为当前学期
              </label>
              <button
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                type="submit"
              >
                创建学期
              </button>
            </form>

            {dashboard ? (
              <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <div>学期总数：{dashboard.total_semesters}</div>
                <div>激活学期：{dashboard.active_semesters}</div>
              </div>
            ) : null}
          </section>

          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">学期列表</h2>
            {semesters.length === 0 ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无学期。
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">名称</th>
                      <th className="px-4 py-2 text-left font-medium">日期</th>
                      <th className="px-4 py-2 text-left font-medium">状态</th>
                      <th className="px-4 py-2 text-left font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {semesters.map((semester) => (
                      <tr key={semester.id} className="text-slate-700">
                        <td className="px-4 py-2 font-medium text-slate-800">{semester.name}</td>
                        <td className="px-4 py-2">
                          {semester.start_date} - {semester.end_date}
                        </td>
                        <td className="px-4 py-2">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              semester.is_active
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {semester.is_active ? '激活' : '未激活'}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex flex-wrap gap-2">
                            <button
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                              onClick={() => setEditing(semester)}
                            >
                              编辑
                            </button>
                            <button
                              className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                              onClick={() => deleteSemester(semester)}
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
          </section>
        </div>

        {editing ? (
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">编辑学期</h2>
            <form className="mt-4 space-y-3" onSubmit={saveEdit}>
              <div className="grid gap-3 md:grid-cols-3">
                <input
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  value={editing.name}
                  onChange={(event) => setEditing({ ...editing, name: event.target.value })}
                />
                <input
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  type="date"
                  value={editing.start_date}
                  onChange={(event) => setEditing({ ...editing, start_date: event.target.value })}
                />
                <input
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  type="date"
                  value={editing.end_date}
                  onChange={(event) => setEditing({ ...editing, end_date: event.target.value })}
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                  type="checkbox"
                  checked={editing.is_active}
                  onChange={(event) => setEditing({ ...editing, is_active: event.target.checked })}
                />
                设为当前学期
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                  type="submit"
                >
                  保存
                </button>
                <button
                  className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                  type="button"
                  onClick={() => setEditing(null)}
                >
                  取消
                </button>
              </div>
            </form>
          </section>
        ) : null}
      </div>
    </div>
  )
}
