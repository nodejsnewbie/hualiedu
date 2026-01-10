import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function TenantManagement() {
  const [tenants, setTenants] = useState([])
  const [message, setMessage] = useState('')

  const loadTenants = async () => {
    const response = await apiFetch('/grading/api/tenants/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || 'Failed to load tenants')
      return
    }
    setTenants(data.tenants || [])
  }

  useEffect(() => {
    loadTenants()
  }, [])

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Tenant Management</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}
        {tenants.length === 0 ? (
          <div className="alert alert-secondary">No tenants found.</div>
        ) : (
          <div className="table-responsive">
            <table className="table table-sm">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((tenant) => (
                  <tr key={tenant.id}>
                    <td>{tenant.name}</td>
                    <td>{tenant.description || '-'}</td>
                    <td>{tenant.is_active ? 'Active' : 'Inactive'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
