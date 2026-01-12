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

const getRepoProtocol = (repoUrl) => {
  const trimmed = (repoUrl || '').trim()
  if (!trimmed) return ''
  if (/^git@[^:]+:/.test(trimmed)) return 'ssh'
  const match = trimmed.match(/^([a-z][a-z0-9+.-]*):\/\//i)
  return match ? match[1].toLowerCase() : ''
}

const getRepoType = (repo) => repo.repo_type || repo.type || ''

export default function RepositoryManagement() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [editBranches, setEditBranches] = useState([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [syncingId, setSyncingId] = useState(null)
  const [validatingId, setValidatingId] = useState(null)

  const protocol = useMemo(() => getRepoProtocol(form.repo_url), [form.repo_url])
  const showAuthFields = protocol === 'http' || protocol === 'https'
  const showSshFields = protocol === 'ssh'

  const loadRepos = async () => {
    setLoading(true)
    try {
      const response = await apiFetch('/grading/api/repositories/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载仓库失败')
      }
      setRepos(data.repositories || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  const resetForm = () => {
    setForm(emptyForm)
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSshFile = (event) => {
    const file = event.target.files && event.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (loadEvent) => {
      setForm((prev) => ({
        ...prev,
        ssh_public_key: (loadEvent.target && loadEvent.target.result) || '',
      }))
    }
    reader.readAsText(file)
  }

  const handleCreate = async () => {
    const repoUrl = form.repo_url.trim()
    if (!repoUrl) {
      window.alert('请输入仓库链接')
      return
    }
    setSaving(true)
    try {
      const payload = new FormData()
      payload.append('repo_url', repoUrl)
      if (form.name.trim()) payload.append('name', form.name.trim())
      if (form.description.trim()) payload.append('description', form.description.trim())
      if (showAuthFields) {
        payload.append('git_username', form.git_username.trim())
        payload.append('git_password', form.git_password)
      }
      if (showSshFields && form.ssh_public_key.trim()) {
        payload.append('ssh_public_key', form.ssh_public_key.trim())
      }

      const response = await apiFetch('/grading/add-repository/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        const message = (data && data.message) || '创建失败'
        window.alert(`错误：${message}`)
        return
      }
      window.alert('仓库创建成功')
      setShowAddModal(false)
      resetForm()
      loadRepos()
    } finally {
      setSaving(false)
    }
  }

  const openEdit = async (repo) => {
    setEditBranches([])
    const repoType = getRepoType(repo)
    const next = {
      id: repo.id,
      name: repo.name || '',
      description: repo.description || '',
      type: repoType,
      path: repo.filesystem_path || repo.path || '',
      git_url: repo.git_url || repo.path || '',
      git_branch: repo.git_branch || repo.branch || '',
      git_username: '',
      git_password: '',
    }
    setEditing(next)
    setShowEditModal(true)
    if (repoType === 'git') {
      try {
        const response = await apiFetch(`/grading/get-repository-branches/?repo_id=${repo.id}`)
        const data = await response.json().catch(() => null)
        if (response.ok && data && data.status === 'success') {
          setEditBranches(data.branches || [])
          if (!next.git_branch && data.current) {
            setEditing((prev) => ({ ...prev, git_branch: data.current }))
          }
        }
      } catch {
        setEditBranches([])
      }
    }
  }

  const handleUpdate = async () => {
    if (!editing) return
    setSaving(true)
    try {
      const payload = new FormData()
      payload.append('repository_id', editing.id)
      payload.append('name', editing.name || '')
      payload.append('description', editing.description || '')
      if (editing.type === 'git') {
        payload.append('git_url', editing.git_url || '')
        payload.append('git_branch', editing.git_branch || '')
        if (editing.git_username) payload.append('git_username', editing.git_username)
        if (editing.git_password) payload.append('git_password', editing.git_password)
      } else {
        payload.append('path', editing.path || '')
      }

      const response = await apiFetch('/grading/update-repository/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        window.alert(`错误：${(data && data.message) || '更新失败'}`)
        return
      }
      window.alert('仓库更新成功')
      setShowEditModal(false)
      setEditing(null)
      loadRepos()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (repo) => {
    if (!window.confirm(`确定要删除仓库“${repo.name}”吗？`)) return
    const response = await apiFetch('/grading/delete-repository/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert(`错误：${(data && data.message) || '删除失败'}`)
      return
    }
    window.alert('仓库删除成功')
    loadRepos()
  }

  const handleSync = async (repo) => {
    setSyncingId(repo.id)
    const response = await apiFetch('/grading/sync-repository/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    window.alert((data && data.message) || '同步完成')
    setSyncingId(null)
    loadRepos()
  }

  const handleValidate = async (repo) => {
    setValidatingId(repo.id)
    const response = await apiFetch('/grading/validate-directory-structure/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository_id: repo.id }),
    })
    const data = await response.json().catch(() => null)
    if (data && data.status === 'success') {
      window.alert(`OK：${data.message}`)
    } else {
      let message = `WARNING：${(data && data.message) || '验证失败'}`
      if (data && data.suggestions && data.suggestions.length > 0) {
        message += `\n\n建议修复步骤：\n${data.suggestions.join('\n')}`
      }
      window.alert(message)
    }
    setValidatingId(null)
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">仓库管理</h1>
            <p className="mt-1 text-sm text-slate-500">管理 Git 仓库或本地文件目录。</p>
          </div>
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
          >
            添加仓库
          </button>
        </header>

        <section className="card-surface p-5">
          {loading ? (
            <div className="py-10 text-center text-sm text-slate-500">加载中...</div>
          ) : repos.length === 0 ? (
            <div className="py-10 text-center text-slate-500">
              <p className="text-lg font-semibold text-slate-700">暂无仓库</p>
              <p className="mt-2 text-sm">点击“添加仓库”创建第一个仓库。</p>
            </div>
          ) : (
            <div className="space-y-4">
              {repos.map((repo) => {
                const repoType = getRepoType(repo)
                const typeLabel = repoType === 'git' ? 'GIT' : 'FILES'
                return (
                  <div
                    key={repo.id}
                    className="card-surface p-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-lg font-semibold text-slate-900">{repo.name}</h3>
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide ${
                              repoType === 'git'
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-sky-100 text-sky-700'
                            }`}
                          >
                            {typeLabel}
                          </span>
                          {repo.class_obj ? (
                            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                              {repo.class_obj.name}
                            </span>
                          ) : null}
                        </div>

                        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                          <span className="font-semibold text-slate-700">路径：</span>
                          <span className="break-all">{repo.path}</span>
                        </div>

                        {repo.description ? (
                          <p className="mt-3 text-sm text-slate-600">{repo.description}</p>
                        ) : null}

                        <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
                          <span>创建时间：{repo.created_at || '-'}</span>
                          {repo.last_sync ? <span>最近同步：{repo.last_sync}</span> : null}
                          {repoType === 'filesystem' && repo.allocated_space_mb ? (
                            <span>分配空间：{repo.allocated_space_mb}MB</span>
                          ) : null}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {repoType === 'git' ? (
                          <button
                            type="button"
                            onClick={() => handleSync(repo)}
                            disabled={syncingId === repo.id}
                            className="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {syncingId === repo.id ? '同步中...' : '同步'}
                          </button>
                        ) : null}
                        <button
                          type="button"
                          onClick={() => handleValidate(repo)}
                          disabled={validatingId === repo.id}
                          className="rounded-lg border border-sky-200 px-3 py-1.5 text-xs font-semibold text-sky-700 transition hover:border-sky-300 hover:bg-sky-50 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {validatingId === repo.id ? '验证中...' : '验证结构'}
                        </button>
                        <button
                          type="button"
                          onClick={() => openEdit(repo)}
                          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                        >
                          编辑
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(repo)}
                          className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      </div>

      {showAddModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-10">
          <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">添加仓库</h2>
                <p className="mt-1 text-xs text-slate-500">填写仓库地址并选择认证方式。</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false)
                  resetForm()
                }}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                关闭
              </button>
            </div>
            <div className="space-y-5 px-6 py-5">
              <div>
                <label className="text-sm font-medium text-slate-700">仓库链接</label>
                <input
                  type="url"
                  name="repo_url"
                  value={form.repo_url}
                  onChange={handleChange}
                  placeholder="https://github.com/user/repo.git 或 git@github.com:user/repo.git"
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
                <p className="mt-1 text-xs text-slate-400">系统将自动识别协议与仓库名称。</p>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">仓库名称</label>
                <input
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="留空则从链接自动识别"
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>

              {showAuthFields ? (
                <div>
                  <label className="text-sm font-medium text-slate-700">HTTPS 认证信息</label>
                  <div className="mt-2 grid gap-3 md:grid-cols-2">
                    <input
                      type="text"
                      name="git_username"
                      value={form.git_username}
                      onChange={handleChange}
                      placeholder="Git 用户名/账号"
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    />
                    <input
                      type="password"
                      name="git_password"
                      value={form.git_password}
                      onChange={handleChange}
                      placeholder="Git 密码/Token"
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">HTTPS 私有仓库需要提供认证信息。</p>
                </div>
              ) : null}

              {showSshFields ? (
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-slate-700">SSH 公钥</label>
                    <textarea
                      name="ssh_public_key"
                      rows="3"
                      value={form.ssh_public_key}
                      onChange={handleChange}
                      placeholder="粘贴 SSH 公钥，例如 ssh-ed25519 AAAA... user@host"
                      className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">或上传 .pub 文件</label>
                    <input
                      type="file"
                      name="ssh_public_key_file"
                      accept=".pub"
                      onChange={handleSshFile}
                      className="mt-2 w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                    />
                  </div>
                </div>
              ) : null}

              <div>
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  name="description"
                  rows="3"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="仓库描述（可选）"
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false)
                  resetForm()
                }}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleCreate}
                disabled={saving}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showEditModal && editing ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-10">
          <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">编辑仓库</h2>
                <p className="mt-1 text-xs text-slate-500">更新仓库信息与分支。</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false)
                  setEditing(null)
                }}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                关闭
              </button>
            </div>
            <div className="space-y-5 px-6 py-5">
              <div>
                <label className="text-sm font-medium text-slate-700">仓库名称</label>
                <input
                  type="text"
                  value={editing.name}
                  onChange={(event) => setEditing({ ...editing, name: event.target.value })}
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">仓库类型</label>
                <input
                  type="text"
                  value={editing.type === 'git' ? 'Git 仓库' : '本地目录'}
                  readOnly
                  className="mt-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600"
                />
              </div>

              {editing.type === 'git' ? (
                <>
                  <div>
                    <label className="text-sm font-medium text-slate-700">Git 仓库 URL</label>
                    <input
                      type="url"
                      value={editing.git_url}
                      onChange={(event) => setEditing({ ...editing, git_url: event.target.value })}
                      className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700">默认分支</label>
                    <select
                      value={editing.git_branch}
                      onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })}
                      className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                    >
                      {editBranches.length === 0 ? (
                        <option value="">未找到分支</option>
                      ) : (
                        editBranches.map((branch) => (
                          <option key={branch} value={branch}>
                            {branch}
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                </>
              ) : (
                <div>
                  <label className="text-sm font-medium text-slate-700">本地路径</label>
                  <input
                    type="text"
                    value={editing.path}
                    readOnly
                    className="mt-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600"
                  />
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  rows="3"
                  value={editing.description || ''}
                  onChange={(event) => setEditing({ ...editing, description: event.target.value })}
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false)
                  setEditing(null)
                }}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleUpdate}
                disabled={saving}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {saving ? '更新中...' : '更新'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
