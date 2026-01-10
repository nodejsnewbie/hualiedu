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
        setMessage((result && result.message) || 'Failed to load dashboard')
        return
      }
      setData(result)
    }
    loadData()
  }, [])

  if (message) {
    return <div className="alert alert-danger">{message}</div>
  }

  if (!data) {
    return <div className="alert alert-info">Loading...</div>
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Tenant Admin Dashboard</h4>
      </div>
      <div className="card-body">
        <h5>{data.tenant.name}</h5>
        <p className="text-muted">{data.tenant.description}</p>
        <div className="row g-3">
          <div className="col-md-4">
            <div className="border rounded p-3 text-center">
              <div className="small text-muted">Users</div>
              <div className="fs-4">{data.user_count}</div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="border rounded p-3 text-center">
              <div className="small text-muted">Repositories</div>
              <div className="fs-4">{data.repository_count}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
