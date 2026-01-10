import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'

const emptyForm = {
  repo_url: '',
  name: '',
  description: '',
  git_username: '',
  git_password: '',
  ssh_public_key: '',
}

export default function RepositoryManagement() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)

  const isGitUrl = useMemo(() => {
    const value = form.repo_url.trim()
    return value.startsWith('http://') || value.startsWith('https://') || value.startsWith('git@')
  }, [form.repo_url])

  const loadRepos = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/grading/api/repositories/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to load repositories')
      }
      setRepos(data.repositories || [])
    } catch (err) {
      setError(err.message || 'Failed to load repositories')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('repo_url', form.repo_url.trim())
      if (form.name.trim()) {
        payload.append('name', form.name.trim())
      }
      if (form.description.trim()) {
        payload.append('description', form.description.trim())
      }
      if (form.git_username.trim()) {
        payload.append('git_username', form.git_username.trim())
      }
      if (form.git_password) {
        payload.append('git_password', form.git_password)
      }
      if (form.ssh_public_key.trim()) {
        payload.append('ssh_public_key', form.ssh_public_key.trim())
      }

      const response = await apiFetch('/grading/add-repository/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to add repository')
      }
      setForm(emptyForm)
      loadRepos()
    } catch (err) {
      setError(err.message || 'Failed to add repository')
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (repo) => {
    setEditing({
      id: repo.id,
      name: repo.name || '',
      description: repo.description || '',
      git_url: repo.path || '',
      git_branch: repo.branch || '',
      git_username: '',
      git_password: '',
    })
  }

  const handleUpdate = async (event) => {
    event.preventDefault()
    if (!editing) {
      return
    }
    setSaving(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('repository_id', editing.id)
      payload.append('name', editing.name || '')
      payload.append('description', editing.description || '')
      payload.append('git_url', editing.git_url || '')
      payload.append('git_branch', editing.git_branch || '')
      if (editing.git_username) {
        payload.append('git_username', editing.git_username)
      }
      if (editing.git_password) {
        payload.append('git_password', editing.git_password)
      }

      const response = await apiFetch('/grading/update-repository/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to update repository')
      }
      setEditing(null)
      loadRepos()
    } catch (err) {
      setError(err.message || 'Failed to update repository')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (repo) => {
    if (!window.confirm(`Delete repository "${repo.name}"?`)) {
      return
    }
    const response = await apiFetch('/grading/delete-repository/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || 'Failed to delete repository')
      return
    }
    loadRepos()
  }

  const handleSync = async (repo) => {
    const response = await apiFetch('/grading/sync-repository/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    window.alert((data && data.message) || 'Sync finished')
    loadRepos()
  }

  const handleValidate = async (repo) => {
    const response = await apiFetch('/grading/validate-directory-structure/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    window.alert((data && data.message) || 'Validation finished')
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Add Repository</h5>
          </div>
          <div className="card-body">
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label" htmlFor="repo_url">
                  Repository URL
                </label>
                <input
                  id="repo_url"
                  name="repo_url"
                  className="form-control"
                  value={form.repo_url}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="name">
                  Name
                </label>
                <input
                  id="name"
                  name="name"
                  className="form-control"
                  value={form.name}
                  onChange={handleChange}
                />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="description">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  className="form-control"
                  rows="3"
                  value={form.description}
                  onChange={handleChange}
                />
              </div>
              {isGitUrl ? (
                <>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="git_username">
                      Git Username (optional)
                    </label>
                    <input
                      id="git_username"
                      name="git_username"
                      className="form-control"
                      value={form.git_username}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="git_password">
                      Git Password / Token (optional)
                    </label>
                    <input
                      id="git_password"
                      name="git_password"
                      type="password"
                      className="form-control"
                      value={form.git_password}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label" htmlFor="ssh_public_key">
                      SSH Public Key (optional)
                    </label>
                    <textarea
                      id="ssh_public_key"
                      name="ssh_public_key"
                      className="form-control"
                      rows="3"
                      value={form.ssh_public_key}
                      onChange={handleChange}
                    />
                  </div>
                </>
              ) : null}
              <button className="btn btn-primary w-100" type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Repository'}
              </button>
            </form>
          </div>
        </div>
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Repositories</h5>
            <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadRepos}>
              Refresh
            </button>
          </div>
          <div className="card-body">
            {loading ? <div className="alert alert-info">Loading...</div> : null}
            {!loading && repos.length === 0 ? (
              <div className="alert alert-secondary">No repositories found.</div>
            ) : null}
            <div className="d-flex flex-column gap-3">
              {repos.map((repo) => (
                <div key={repo.id} className="border rounded p-3 bg-white">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 className="mb-1">{repo.name}</h6>
                      <div className="text-muted small">{repo.path}</div>
                      <div className="text-muted small">
                        {repo.type === 'git' ? 'Git' : 'Filesystem'}{' '}
                        {repo.last_sync ? `· Last sync ${repo.last_sync}` : ''}
                      </div>
                    </div>
                    <div className="d-flex gap-2 flex-wrap">
                      {repo.can_sync ? (
                        <button className="btn btn-outline-success btn-sm" onClick={() => handleSync(repo)}>
                          Sync
                        </button>
                      ) : null}
                      <button className="btn btn-outline-info btn-sm" onClick={() => handleValidate(repo)}>
                        Validate
                      </button>
                      <button className="btn btn-outline-primary btn-sm" onClick={() => handleEdit(repo)}>
                        Edit
                      </button>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => handleDelete(repo)}>
                        Delete
                      </button>
                    </div>
                  </div>
                  {repo.description ? <div className="text-muted mt-2">{repo.description}</div> : null}
                </div>
              ))}
            </div>
          </div>
        </div>

        {editing ? (
          <div className="card mt-4">
            <div className="card-header">
              <h6 className="mb-0">Edit Repository</h6>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpdate}>
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input
                    className="form-control"
                    value={editing.name}
                    onChange={(event) => setEditing({ ...editing, name: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    value={editing.description || ''}
                    onChange={(event) => setEditing({ ...editing, description: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git URL</label>
                  <input
                    className="form-control"
                    value={editing.git_url || ''}
                    onChange={(event) => setEditing({ ...editing, git_url: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git Branch</label>
                  <input
                    className="form-control"
                    value={editing.git_branch || ''}
                    onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git Username</label>
                  <input
                    className="form-control"
                    value={editing.git_username || ''}
                    onChange={(event) => setEditing({ ...editing, git_username: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git Password</label>
                  <input
                    className="form-control"
                    type="password"
                    value={editing.git_password || ''}
                    onChange={(event) => setEditing({ ...editing, git_password: event.target.value })}
                  />
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" type="submit" disabled={saving}>
                    {saving ? 'Updating...' : 'Update'}
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
    </div>
  )
}
