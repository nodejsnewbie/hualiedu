import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function TenantAdminDashboard() {
  const [data, setData] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    const loadData = async () => {
      const response = await apiFetch('/grading/api/tenant-dashboard/')
      const result = await response.json().catch(() => null)
      if (!response.ok || (result && result.status !== 'success')) {
        setMessage((result && result.message) || '加载数据失败')
        return
      }
      setData(result)
    }
    loadData()
  }, [])

  if (message) {
    return (
      <div className="min-h-screen">
        <div className="mx-auto w-full max-w-3xl px-4 py-8">
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {message}
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen">
        <div className="mx-auto w-full max-w-3xl px-4 py-8">
          <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
            加载中...
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto w-full max-w-4xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">租户管理员</h1>
          <p className="mt-1 text-sm text-slate-500">查看租户资源概览。</p>
        </header>

        <section className="card-surface p-5">
          <h2 className="text-lg font-semibold text-slate-900">{data.tenant.name}</h2>
          <p className="mt-1 text-sm text-slate-500">{data.tenant.description}</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
              <div className="text-xs text-slate-500">用户数</div>
              <div className="mt-2 text-3xl font-semibold text-slate-900">{data.user_count}</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
              <div className="text-xs text-slate-500">仓库数</div>
              <div className="mt-2 text-3xl font-semibold text-slate-900">{data.repository_count}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
