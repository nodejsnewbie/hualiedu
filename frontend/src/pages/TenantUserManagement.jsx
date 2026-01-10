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
      setMessage((data && data.message) || 'Failed to load users')
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
      setMessage((data && data.message) || 'Failed to add user')
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
      setMessage((data && data.message) || 'Failed to update user')
      return
    }
    setEditing(null)
    loadUsers()
  }

  const removeUser = async (profileId, username) => {
    if (!window.confirm(`Remove user "${username}" from tenant?`)) {
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
      setMessage((data && data.message) || 'Failed to remove user')
      return
    }
    loadUsers()
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Add User</h5>
          </div>
          <div className="card-body">
            {message ? <div className="alert alert-info">{message}</div> : null}
            {tenant ? <div className="alert alert-secondary">Tenant: {tenant.name}</div> : null}
            <form onSubmit={addUser}>
              <div className="mb-3">
                <label className="form-label">Username</label>
                <input className="form-control" name="username" value={form.username} onChange={handleChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Repo Base Dir</label>
                <input className="form-control" name="repo_base_dir" value={form.repo_base_dir} onChange={handleChange} />
              </div>
              <div className="form-check mb-3">
                <input className="form-check-input" type="checkbox" name="is_tenant_admin" checked={form.is_tenant_admin} onChange={handleChange} id="tenantAdminCheck" />
                <label className="form-check-label" htmlFor="tenantAdminCheck">
                  Tenant Admin
                </label>
              </div>
              <button className="btn btn-primary w-100" type="submit">
                Add User
              </button>
            </form>
          </div>
        </div>
        {editing ? (
          <div className="card mt-3">
            <div className="card-header">
              <h6 className="mb-0">Edit User</h6>
            </div>
            <div className="card-body">
              <form onSubmit={updateUser}>
                <div className="mb-3">
                  <label className="form-label">Username</label>
                  <input className="form-control" value={editing.username} disabled />
                </div>
                <div className="mb-3">
                  <label className="form-label">Repo Base Dir</label>
                  <input className="form-control" value={editing.repo_base_dir || ''} onChange={(event) => setEditing({ ...editing, repo_base_dir: event.target.value })} />
                </div>
                <div className="form-check mb-3">
                  <input className="form-check-input" type="checkbox" checked={editing.is_tenant_admin} onChange={(event) => setEditing({ ...editing, is_tenant_admin: event.target.checked })} id="editTenantAdmin" />
                  <label className="form-check-label" htmlFor="editTenantAdmin">
                    Tenant Admin
                  </label>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" type="submit">
                    Save
                  </button>
                  <button className="btn btn-outline-secondary" type="button" onClick={() => setEditing(null)}>
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Users</h5>
          </div>
          <div className="card-body">
            {users.length === 0 ? (
              <div className="alert alert-secondary">No users found.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Tenant Admin</th>
                      <th>Repo Base Dir</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.profile_id}>
                        <td>{user.username}</td>
                        <td>{user.is_tenant_admin ? 'Yes' : 'No'}</td>
                        <td>{user.repo_base_dir || '-'}</td>
                        <td>
                          <div className="d-flex gap-2">
                            <button className="btn btn-outline-primary btn-sm" onClick={() => setEditing(user)}>
                              Edit
                            </button>
                            <button className="btn btn-outline-danger btn-sm" onClick={() => removeUser(user.profile_id, user.username)}>
                              Remove
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
        </div>
      </div>
    </div>
  )
}
