import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function TenantManagement() {
  const [tenants, setTenants] = useState([])
  const [message, setMessage] = useState('')

  const loadTenants = async () => {
    const response = await apiFetch('/grading/api/tenants/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '加载租户失败')
      return
    }
    setTenants(data.tenants || [])
  }

  useEffect(() => {
    loadTenants()
  }, [])

  return (
    <div className="min-h-screen">
      <div className="page-shell max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">租户管理</h1>
          <p className="mt-1 text-sm text-slate-500">查看租户状态与描述。</p>
        </header>

        {message ? (
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        ) : null}

        <section className="card-surface p-5">
          {tenants.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              暂无租户。
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-slate-600">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">名称</th>
                    <th className="px-4 py-2 text-left font-medium">描述</th>
                    <th className="px-4 py-2 text-left font-medium">状态</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {tenants.map((tenant) => (
                    <tr key={tenant.id} className="text-slate-700">
                      <td className="px-4 py-2 font-medium text-slate-800">{tenant.name}</td>
                      <td className="px-4 py-2">{tenant.description || '-'}</td>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
