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
      setMessage((data && data.message) || 'Failed to load tenants')
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
      setMessage((data && data.message) || 'Failed to create tenant')
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
      setMessage((data && data.message) || 'Failed to update tenant')
      return
    }
    setEditing(null)
    loadTenants()
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Create Tenant</h5>
          </div>
          <div className="card-body">
            {message ? <div className="alert alert-info">{message}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label">Name</label>
                <input className="form-control" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Description</label>
                <textarea className="form-control" rows="3" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
              </div>
              <button className="btn btn-primary w-100" type="submit">
                Create Tenant
              </button>
            </form>
          </div>
        </div>
        <div className="card mt-3">
          <div className="card-header">
            <h6 className="mb-0">Stats</h6>
          </div>
          <div className="card-body">
            <div>Total users: {stats.total_users}</div>
            <div>Active tenants: {stats.active_tenants}</div>
          </div>
        </div>
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Tenants</h5>
          </div>
          <div className="card-body">
            {tenants.length === 0 ? (
              <div className="alert alert-secondary">No tenants found.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Users</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tenants.map((tenant) => (
                      <tr key={tenant.id}>
                        <td>{tenant.name}</td>
                        <td>{tenant.user_count}</td>
                        <td>
                          {tenant.is_active ? (
                            <span className="badge bg-success">Active</span>
                          ) : (
                            <span className="badge bg-secondary">Inactive</span>
                          )}
                        </td>
                        <td>
                          <button className="btn btn-outline-primary btn-sm" onClick={() => setEditing(tenant)}>
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {editing ? (
          <div className="card mt-3">
            <div className="card-header">
              <h6 className="mb-0">Edit Tenant</h6>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpdate}>
                <div className="row g-2">
                  <div className="col-md-6">
                    <input className="form-control" value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} />
                  </div>
                  <div className="col-md-6">
                    <input className="form-control" value={editing.description || ''} onChange={(event) => setEditing({ ...editing, description: event.target.value })} />
                  </div>
                  <div className="col-12">
                    <div className="form-check">
                      <input className="form-check-input" type="checkbox" checked={editing.is_active} onChange={(event) => setEditing({ ...editing, is_active: event.target.checked })} id="tenantActive" />
                      <label className="form-check-label" htmlFor="tenantActive">
                        Active
                      </label>
                    </div>
                  </div>
                  <div className="col-12 d-flex gap-2">
                    <button className="btn btn-primary" type="submit">
                      Save
                    </button>
                    <button className="btn btn-outline-secondary" type="button" onClick={() => setEditing(null)}>
                      Cancel
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
