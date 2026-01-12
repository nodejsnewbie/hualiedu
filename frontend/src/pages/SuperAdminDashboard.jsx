import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function SuperAdminDashboard() {
  const [tenants, setTenants] = useState([])
  const [stats, setStats] = useState({ total_users: 0, active_tenants: 0 })
  const [form, setForm] = useState({ name: '', description: '' })
  const [editing, setEditing] = useState(null)
  const [message, setMessage] = useState('')

  const loadTenants = async () => {
    const response = await apiFetch('/grading/api/tenants/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '加载租户失败')
      return
    }
    setTenants(data.tenants || [])
    setStats({ total_users: data.total_users || 0, active_tenants: data.active_tenants || 0 })
  }

  useEffect(() => {
    loadTenants()
  }, [])

  const handleCreate = async (event) => {
    event.preventDefault()
    const payload = new URLSearchParams(form)
    const response = await apiFetch('/grading/super-admin/tenants/create/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '创建租户失败')
      return
    }
    setForm({ name: '', description: '' })
    loadTenants()
  }

  const handleUpdate = async (event) => {
    event.preventDefault()
    if (!editing) return
    const payload = new URLSearchParams({
      tenant_id: editing.id,
      name: editing.name,
      description: editing.description || '',
      is_active: editing.is_active ? 'true' : 'false',
    })
    const response = await apiFetch('/grading/super-admin/tenants/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '更新租户失败')
      return
    }
    setEditing(null)
    loadTenants()
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">超级管理员</h1>
          <p className="mt-1 text-sm text-slate-500">创建与管理租户信息。</p>
        </header>

        {message ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">创建租户</h2>
            <form className="mt-4 space-y-4" onSubmit={handleCreate}>
              <div>
                <label className="text-sm font-medium text-slate-700">名称</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  rows="3"
                  value={form.description}
                  onChange={(event) => setForm({ ...form, description: event.target.value })}
                />
              </div>
              <button
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                type="submit"
              >
                创建租户
              </button>
            </form>
            <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              <div>用户总数：{stats.total_users}</div>
              <div>活跃租户：{stats.active_tenants}</div>
            </div>
          </section>

          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">租户列表</h2>
            {tenants.length === 0 ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无租户。
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">名称</th>
                      <th className="px-4 py-2 text-left font-medium">用户数</th>
                      <th className="px-4 py-2 text-left font-medium">状态</th>
                      <th className="px-4 py-2 text-left font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {tenants.map((tenant) => (
                      <tr key={tenant.id} className="text-slate-700">
                        <td className="px-4 py-2 font-medium text-slate-800">{tenant.name}</td>
                        <td className="px-4 py-2">{tenant.user_count}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              tenant.is_active
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {tenant.is_active ? '活跃' : '停用'}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          <button
                            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                            onClick={() => setEditing(tenant)}
                          >
                            编辑
                          </button>
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
            <h2 className="text-base font-semibold text-slate-800">编辑租户</h2>
            <form className="mt-4 space-y-3" onSubmit={handleUpdate}>
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  value={editing.name}
                  onChange={(event) => setEditing({ ...editing, name: event.target.value })}
                />
                <input
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  value={editing.description || ''}
                  onChange={(event) => setEditing({ ...editing, description: event.target.value })}
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                  type="checkbox"
                  checked={editing.is_active}
                  onChange={(event) => setEditing({ ...editing, is_active: event.target.checked })}
                />
                活跃
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
