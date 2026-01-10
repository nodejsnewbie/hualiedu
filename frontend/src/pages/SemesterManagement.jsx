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
      setError((data && data.message) || 'Failed to load semesters')
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
      setError((data && data.message) || 'Failed to create semester')
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
      setError((data && data.message) || 'Failed to update semester')
      return
    }
    setEditing(null)
    loadSemesters()
  }

  const deleteSemester = async (semester) => {
    if (!window.confirm(`Delete semester "${semester.name}"?`)) {
      return
    }
    const response = await apiFetch(`/grading/api/semesters/${semester.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ force_delete: 'false' }),
    })
    const data = await response.json().catch(() => null)
    if (response.status === 409 && data && data.status === 'warning') {
      if (!window.confirm(`Semester has ${data.courses_count} courses. Force delete?`)) {
        return
      }
      const retry = await apiFetch(`/grading/api/semesters/${semester.id}/delete/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ force_delete: 'true' }),
      })
      const retryData = await retry.json().catch(() => null)
      if (!retry.ok || (retryData && retryData.status !== 'success')) {
        setError((retryData && retryData.message) || 'Failed to delete semester')
        return
      }
    } else if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || 'Failed to delete semester')
      return
    }
    loadSemesters()
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Create Semester</h5>
          </div>
          <div className="card-body">
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={submitSemester}>
              <div className="mb-3">
                <label className="form-label">Name</label>
                <input className="form-control" name="name" value={form.name} onChange={handleChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Start Date</label>
                <input className="form-control" type="date" name="start_date" value={form.start_date} onChange={handleChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">End Date</label>
                <input className="form-control" type="date" name="end_date" value={form.end_date} onChange={handleChange} required />
              </div>
              <div className="form-check mb-3">
                <input className="form-check-input" type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} id="semesterActive" />
                <label className="form-check-label" htmlFor="semesterActive">
                  Set as active
                </label>
              </div>
              <button className="btn btn-primary w-100" type="submit">
                Create Semester
              </button>
            </form>
          </div>
        </div>
        {dashboard ? (
          <div className="card mt-3">
            <div className="card-header">
              <h6 className="mb-0">Dashboard</h6>
            </div>
            <div className="card-body">
              <div className="small text-muted">Total semesters: {dashboard.total_semesters}</div>
              <div className="small text-muted">Active semesters: {dashboard.active_semesters}</div>
            </div>
          </div>
        ) : null}
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Semesters</h5>
          </div>
          <div className="card-body">
            {semesters.length === 0 ? (
              <div className="alert alert-secondary">No semesters found.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Dates</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {semesters.map((semester) => (
                      <tr key={semester.id}>
                        <td>{semester.name}</td>
                        <td>
                          {semester.start_date} - {semester.end_date}
                        </td>
                        <td>
                          {semester.is_active ? (
                            <span className="badge bg-success">Active</span>
                          ) : (
                            <span className="badge bg-secondary">Inactive</span>
                          )}
                        </td>
                        <td>
                          <div className="d-flex gap-2">
                            <button className="btn btn-outline-primary btn-sm" onClick={() => setEditing(semester)}>
                              Edit
                            </button>
                            <button className="btn btn-outline-danger btn-sm" onClick={() => deleteSemester(semester)}>
                              Delete
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
        {editing ? (
          <div className="card mt-3">
            <div className="card-header">
              <h6 className="mb-0">Edit Semester</h6>
            </div>
            <div className="card-body">
              <form onSubmit={saveEdit}>
                <div className="row g-2">
                  <div className="col-md-6">
                    <input className="form-control" value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} />
                  </div>
                  <div className="col-md-3">
                    <input className="form-control" type="date" value={editing.start_date} onChange={(event) => setEditing({ ...editing, start_date: event.target.value })} />
                  </div>
                  <div className="col-md-3">
                    <input className="form-control" type="date" value={editing.end_date} onChange={(event) => setEditing({ ...editing, end_date: event.target.value })} />
                  </div>
                  <div className="col-12">
                    <div className="form-check">
                      <input className="form-check-input" type="checkbox" checked={editing.is_active} onChange={(event) => setEditing({ ...editing, is_active: event.target.checked })} id="editActive" />
                      <label className="form-check-label" htmlFor="editActive">
                        Set as active
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
