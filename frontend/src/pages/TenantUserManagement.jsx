import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function TenantUserManagement() {
  const [users, setUsers] = useState([])
  const [tenant, setTenant] = useState(null)
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({ username: '', repo_base_dir: '', is_tenant_admin: false })
  const [editing, setEditing] = useState(null)

  const loadUsers = async () => {
    const response = await apiFetch('/grading/api/tenant-users/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '加载用户失败')
      return
    }
    setUsers(data.users || [])
    setTenant(data.tenant || null)
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const addUser = async (event) => {
    event.preventDefault()
    const payload = new URLSearchParams({
      username: form.username,
      repo_base_dir: form.repo_base_dir,
      is_tenant_admin: form.is_tenant_admin ? 'true' : 'false',
    })
    const response = await apiFetch('/grading/tenant-admin/users/add/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '添加用户失败')
      return
    }
    setForm({ username: '', repo_base_dir: '', is_tenant_admin: false })
    loadUsers()
  }

  const updateUser = async (event) => {
    event.preventDefault()
    if (!editing) return
    const payload = new URLSearchParams({
      profile_id: editing.profile_id,
      repo_base_dir: editing.repo_base_dir || '',
      is_tenant_admin: editing.is_tenant_admin ? 'true' : 'false',
    })
    const response = await apiFetch('/grading/tenant-admin/users/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '更新用户失败')
      return
    }
    setEditing(null)
    loadUsers()
  }

  const removeUser = async (profileId, username) => {
    if (!window.confirm(`移除用户“${username}”？`)) {
      return
    }
    const payload = new URLSearchParams({ profile_id: profileId })
    const response = await apiFetch('/grading/tenant-admin/users/remove/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '移除用户失败')
      return
    }
    loadUsers()
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">租户用户管理</h1>
          <p className="mt-1 text-sm text-slate-500">添加租户用户并配置权限。</p>
        </header>

        {message ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">添加用户</h2>
            {tenant ? (
              <div className="mt-2 text-xs text-slate-500">租户：{tenant.name}</div>
            ) : null}
            <form className="mt-4 space-y-4" onSubmit={addUser}>
              <div>
                <label className="text-sm font-medium text-slate-700">用户名</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">仓库根目录</label>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  name="repo_base_dir"
                  value={form.repo_base_dir}
                  onChange={handleChange}
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                  type="checkbox"
                  name="is_tenant_admin"
                  checked={form.is_tenant_admin}
                  onChange={handleChange}
                />
                租户管理员
              </label>
              <button
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                type="submit"
              >
                添加用户
              </button>
            </form>

            {editing ? (
              <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <h3 className="text-sm font-semibold text-slate-700">编辑用户</h3>
                <form className="mt-3 space-y-3" onSubmit={updateUser}>
                  <div>
                    <label className="text-xs font-medium text-slate-500">用户名</label>
                    <input
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2 text-sm text-slate-500"
                      value={editing.username}
                      disabled
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-500">仓库根目录</label>
                    <input
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                      value={editing.repo_base_dir || ''}
                      onChange={(event) => setEditing({ ...editing, repo_base_dir: event.target.value })}
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm text-slate-600">
                    <input
                      className="h-4 w-4 rounded border-slate-300 text-slate-900"
                      type="checkbox"
                      checked={editing.is_tenant_admin}
                      onChange={(event) => setEditing({ ...editing, is_tenant_admin: event.target.checked })}
                    />
                    租户管理员
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
              </div>
            ) : null}
          </section>

          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">用户列表</h2>
            {users.length === 0 ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无用户。
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">用户名</th>
                      <th className="px-4 py-2 text-left font-medium">租户管理员</th>
                      <th className="px-4 py-2 text-left font-medium">仓库根目录</th>
                      <th className="px-4 py-2 text-left font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {users.map((user) => (
                      <tr key={user.profile_id} className="text-slate-700">
                        <td className="px-4 py-2 font-medium text-slate-800">{user.username}</td>
                        <td className="px-4 py-2">{user.is_tenant_admin ? '是' : '否'}</td>
                        <td className="px-4 py-2">{user.repo_base_dir || '-'}</td>
                        <td className="px-4 py-2">
                          <div className="flex flex-wrap gap-2">
                            <button
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                              onClick={() => setEditing(user)}
                            >
                              编辑
                            </button>
                            <button
                              className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                              onClick={() => removeUser(user.profile_id, user.username)}
                            >
                              移除
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
      </div>
    </div>
  )
}
