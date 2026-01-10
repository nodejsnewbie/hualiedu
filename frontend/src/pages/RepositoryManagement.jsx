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
        throw new Error((data && data.message) || '加载仓库失败')
      }
      setRepos(data.repositories || [])
    } catch (err) {
      setError(err.message || '加载仓库失败')
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
        throw new Error((data && data.message) || '新增仓库失败')
      }
      setForm(emptyForm)
      loadRepos()
    } catch (err) {
      setError(err.message || '新增仓库失败')
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
        throw new Error((data && data.message) || '更新仓库失败')
      }
      setEditing(null)
      loadRepos()
    } catch (err) {
      setError(err.message || '更新仓库失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (repo) => {
    if (!window.confirm(`确定删除仓库 "${repo.name}" 吗？`)) {
      return
    }
    const response = await apiFetch('/grading/delete-repository/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || '删除仓库失败')
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
    window.alert((data && data.message) || '同步完成')
    loadRepos()
  }

  const handleValidate = async (repo) => {
    const response = await apiFetch('/grading/validate-directory-structure/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    window.alert((data && data.message) || '校验完成')
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">新增仓库</h5>
          </div>
          <div className="card-body">
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label" htmlFor="repo_url">
                  仓库地址
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
                  名称
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
                  描述
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
                      Git 用户名（可选）
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
                      Git 密码 / Token（可选）
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
                      SSH 公钥（可选）
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
              {saving ? '保存中...' : '保存仓库'}
              </button>
            </form>
          </div>
        </div>
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">仓库列表</h5>
            <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadRepos}>
              刷新
            </button>
          </div>
          <div className="card-body">
            {loading ? <div className="alert alert-info">加载中...</div> : null}
            {!loading && repos.length === 0 ? (
              <div className="alert alert-secondary">暂无仓库。</div>
            ) : null}
            <div className="d-flex flex-column gap-3">
              {repos.map((repo) => (
                <div key={repo.id} className="border rounded p-3 bg-white">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 className="mb-1">{repo.name}</h6>
                      <div className="text-muted small">{repo.path}</div>
                      <div className="text-muted small">
                        {repo.type === 'git' ? 'Git' : '文件系统'}{' '}
                        {repo.last_sync ? `· 最近同步 ${repo.last_sync}` : ''}
                      </div>
                    </div>
                    <div className="d-flex gap-2 flex-wrap">
                      {repo.can_sync ? (
                        <button className="btn btn-outline-success btn-sm" onClick={() => handleSync(repo)}>
                          同步
                        </button>
                      ) : null}
                      <button className="btn btn-outline-info btn-sm" onClick={() => handleValidate(repo)}>
                        校验
                      </button>
                      <button className="btn btn-outline-primary btn-sm" onClick={() => handleEdit(repo)}>
                        编辑
                      </button>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => handleDelete(repo)}>
                        删除
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
              <h6 className="mb-0">编辑仓库</h6>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpdate}>
                <div className="mb-3">
                  <label className="form-label">名称</label>
                  <input
                    className="form-control"
                    value={editing.name}
                    onChange={(event) => setEditing({ ...editing, name: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">描述</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    value={editing.description || ''}
                    onChange={(event) => setEditing({ ...editing, description: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 地址</label>
                  <input
                    className="form-control"
                    value={editing.git_url || ''}
                    onChange={(event) => setEditing({ ...editing, git_url: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 分支</label>
                  <input
                    className="form-control"
                    value={editing.git_branch || ''}
                    onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 用户名</label>
                  <input
                    className="form-control"
                    value={editing.git_username || ''}
                    onChange={(event) => setEditing({ ...editing, git_username: event.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 密码</label>
                  <input
                    className="form-control"
                    type="password"
                    value={editing.git_password || ''}
                    onChange={(event) => setEditing({ ...editing, git_password: event.target.value })}
                  />
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" type="submit" disabled={saving}>
                    {saving ? '更新中...' : '更新'}
                  </button>
                  <button className="btn btn-outline-secondary" type="button" onClick={() => setEditing(null)}>
                    取消
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
