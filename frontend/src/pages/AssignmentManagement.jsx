import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'

const emptyForm = {
  description: '',
  repo_type: 'git',
  git_url: '',
  git_branch: '',
  git_username: '',
  git_password: '',
  filesystem_path: '',
}

const getRepoProtocol = (repoUrl) => {
  const trimmed = (repoUrl || '').trim()
  if (!trimmed) return ''
  if (/^git@[^:]+:/.test(trimmed)) return 'ssh'
  const match = trimmed.match(/^([a-z][a-z0-9+.-]*):\/\//i)
  return match ? match[1].toLowerCase() : ''
}

const getStorageLabel = (storageType) => (storageType === 'git' ? 'Git 仓库' : '文件上传')

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

export default function AssignmentManagement() {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [branchOptions, setBranchOptions] = useState([])
  const [branchLoading, setBranchLoading] = useState(false)
  const [branchError, setBranchError] = useState('')
  const [editBranchOptions, setEditBranchOptions] = useState([])
  const [editBranchLoading, setEditBranchLoading] = useState(false)
  const [editBranchError, setEditBranchError] = useState('')

  const protocol = useMemo(() => getRepoProtocol(form.git_url), [form.git_url])
  const editProtocol = useMemo(() => getRepoProtocol(editing?.git_url), [editing?.git_url])
  const isGit = form.repo_type === 'git'
  const isFilesystem = form.repo_type === 'filesystem'
  const showAuthFields = isGit && (protocol === 'http' || protocol === 'https')
  const showEditAuthFields =
    editing && editing.repo_type === 'git' && (editProtocol === 'http' || editProtocol === 'https')

  const loadAssignments = async () => {
    setLoading(true)
    try {
      const response = await apiFetch('/grading/api/assignments/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '请求失败，请重试')
      }
      setAssignments(data.assignments || [])
    } catch (err) {
      window.alert(`错误：${err.message || '请求失败，请重试'}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAssignments()
  }, [])

  useEffect(() => {
    if (!isGit) {
      setBranchOptions([])
      setBranchError('')
      return
    }
    if (!form.git_url.trim()) return
    const timer = setTimeout(() => {
      fetchCreateBranches()
    }, 400)
    return () => clearTimeout(timer)
  }, [isGit, form.git_url, form.git_username, form.git_password, showAuthFields])

  useEffect(() => {
    if (!showEditModal || !editing || editing.repo_type !== 'git') {
      setEditBranchOptions([])
      setEditBranchError('')
      return
    }
    if (!editing.git_url || !editing.git_url.trim()) return
    const timer = setTimeout(() => {
      fetchEditBranches()
    }, 400)
    return () => clearTimeout(timer)
  }, [
    showEditModal,
    editing?.git_url,
    editing?.git_username,
    editing?.git_password,
    showEditAuthFields,
  ])

  const resetForm = () => {
    setForm(emptyForm)
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const fetchCreateBranches = async () => {
    const gitUrl = form.git_url.trim()
    if (!gitUrl) return
    setBranchLoading(true)
    setBranchError('')
    try {
      const payload = new FormData()
      payload.append('git_url', gitUrl)
      if (showAuthFields) {
        payload.append('git_username', form.git_username.trim())
        payload.append('git_password', form.git_password)
      }
      const response = await apiFetch('/grading/api/git-branches/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '获取分支失败')
      }
      const branches = data.branches || []
      const defaultBranch = data.default_branch || branches[0] || ''
      setBranchOptions(branches)
      setForm((prev) => ({ ...prev, git_branch: defaultBranch }))
    } catch (err) {
      setBranchOptions([])
      setBranchError(err.message || '获取分支失败')
    } finally {
      setBranchLoading(false)
    }
  }

  const fetchEditBranches = async () => {
    if (!editing || editing.repo_type !== 'git') return
    const gitUrl = (editing.git_url || '').trim()
    if (!gitUrl) return
    setEditBranchLoading(true)
    setEditBranchError('')
    try {
      const payload = new FormData()
      payload.append('git_url', gitUrl)
      if (showEditAuthFields) {
        payload.append('git_username', (editing.git_username || '').trim())
        payload.append('git_password', editing.git_password || '')
      }
      const response = await apiFetch('/grading/api/git-branches/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '获取分支失败')
      }
      const branches = data.branches || []
      const defaultBranch = data.default_branch || branches[0] || ''
      setEditBranchOptions(branches)
      setEditing((prev) =>
        prev ? { ...prev, git_branch: prev.git_branch || defaultBranch } : prev
      )
    } catch (err) {
      setEditBranchOptions([])
      setEditBranchError(err.message || '获取分支失败')
    } finally {
      setEditBranchLoading(false)
    }
  }

  const handleCreate = async () => {
    if (form.repo_type === 'git') {
      if (!form.git_url.trim()) {
        window.alert('错误：Git 仓库 URL 不能为空')
        return
      }
      if (!form.git_branch.trim()) {
        window.alert('错误：请先获取并选择分支')
        return
      }
    } else if (form.repo_type === 'filesystem') {
      if (!form.filesystem_path.trim()) {
        window.alert('错误：存储路径不能为空')
        return
      }
    }

    setSaving(true)
    try {
      const payload = new FormData()
      payload.append('storage_type', form.repo_type)
      if (form.repo_type === 'git') {
        payload.append('git_url', form.git_url.trim())
        payload.append('git_branch', form.git_branch.trim())
        if (showAuthFields) {
          payload.append('git_username', form.git_username.trim())
          payload.append('git_password', form.git_password)
        }
      } else if (form.repo_type === 'filesystem') {
        payload.append('base_path', form.filesystem_path.trim())
      }
      if (form.description.trim()) {
        payload.append('description', form.description.trim())
      }

      const response = await apiFetch('/grading/assignments/create/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        const message = (data && data.message) || '创建失败'
        window.alert(`错误：${message}`)
        return
      }
      window.alert('作业配置创建成功')
      setShowAddModal(false)
      resetForm()
      loadAssignments()
    } finally {
      setSaving(false)
    }
  }

  const openEdit = (assignment) => {
    setEditing({
      id: assignment.id,
      description: assignment.description || '',
      repo_type: assignment.repo_type || 'git',
      git_url: assignment.git_url || '',
      git_branch: assignment.git_branch || '',
      git_username: assignment.git_username || '',
      git_password: '',
      filesystem_path: assignment.filesystem_path || '',
    })
    setShowEditModal(true)
  }

  const handleUpdate = async () => {
    if (!editing) return
    if (editing.repo_type === 'git' && !editing.git_branch.trim()) {
      window.alert('错误：请先获取并选择分支')
      return
    }
    setSaving(true)
    try {
      const payload = new FormData()
      payload.append('description', editing.description || '')
      if (editing.repo_type === 'git') {
        payload.append('git_url', editing.git_url || '')
        payload.append('git_branch', editing.git_branch || '')
        payload.append('git_username', editing.git_username || '')
        if (editing.git_password) {
          payload.append('git_password', editing.git_password)
        }
      } else if (editing.repo_type === 'filesystem') {
        payload.append('base_path', editing.filesystem_path || '')
      }

      const response = await apiFetch(`/grading/assignments/${editing.id}/edit/`, {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        window.alert(`错误：${(data && data.message) || '更新失败'}`)
        return
      }
      window.alert('作业配置更新成功')
      setShowEditModal(false)
      setEditing(null)
      loadAssignments()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (assignment) => {
    if (!assignment) return
    const previewResponse = await apiFetch(`/grading/assignments/${assignment.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ confirm: 'false' }),
    })
    const previewData = await previewResponse.json().catch(() => null)
    if (!previewResponse.ok || !previewData) {
      window.alert('请求失败，请重试')
      return
    }
    if (previewData.deleted) {
      window.alert(previewData.message || '作业配置删除成功')
      loadAssignments()
      return
    }

    const warning = previewData.impact && previewData.impact.warning ? previewData.impact.warning : ''
    const message = `确定要删除作业配置“${assignment.name}”吗？\n\n${warning}`
    if (!window.confirm(message)) return

    const confirmResponse = await apiFetch(`/grading/assignments/${assignment.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ confirm: 'true' }),
    })
    const confirmData = await confirmResponse.json().catch(() => null)
    if (!confirmResponse.ok || !confirmData) {
      window.alert('请求失败，请重试')
      return
    }
    if (confirmData.success) {
      window.alert(confirmData.message || '作业配置删除成功')
      loadAssignments()
      return
    }
    window.alert(`错误：${confirmData.message || '删除失败'}`)
  }

  const handleViewStructure = (assignment) => {
    if (!assignment) return
    window.location.href = `/grading?assignment_id=${assignment.id}`
  }

  return (
    <div className="page-shell max-w-5xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">作业管理</h1>
          <p className="text-sm text-slate-500">配置作业仓库或上传目录。</p>
        </div>
        <button
          type="button"
          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
          onClick={() => setShowAddModal(true)}
        >
          新增作业配置
        </button>
      </div>

      <div className="mt-6 space-y-4">
        {loading ? (
          <div className="card-surface p-6 text-sm text-slate-500">
            正在加载作业配置...
          </div>
        ) : null}

        {!loading && assignments.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-10 text-center">
            <p className="text-sm text-slate-500">暂无作业配置，点击右上角新增。</p>
          </div>
        ) : null}

        {assignments.map((assignment) => (
          <div key={assignment.id} className="card-surface p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-semibold text-slate-900">{assignment.name}</h2>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      assignment.repo_type === 'git'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {getStorageLabel(assignment.repo_type)}
                  </span>
                </div>
                <div className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  {assignment.repo_type === 'git' ? (
                    <>
                      {assignment.git_url}
                      {assignment.git_branch ? <span className="text-slate-400"> @ {assignment.git_branch}</span> : null}
                    </>
                  ) : (
                    assignment.filesystem_path
                  )}
                </div>
                {assignment.description ? (
                  <p className="text-sm text-slate-500">{assignment.description}</p>
                ) : null}
                <p className="text-xs text-slate-400">
                  创建时间：{formatDate(assignment.created_at)}
                  {assignment.updated_at && assignment.updated_at !== assignment.created_at ? (
                    <> · 更新时间：{formatDate(assignment.updated_at)}</>
                  ) : null}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 hover:border-slate-300"
                  onClick={() => handleViewStructure(assignment)}
                >
                  查看结构
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 hover:border-slate-300"
                  onClick={() => openEdit(assignment)}
                >
                  编辑
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-rose-200 px-3 py-2 text-xs text-rose-600 hover:border-rose-300"
                  onClick={() => handleDelete(assignment)}
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showAddModal ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">新增作业配置</h2>
              <button
                type="button"
                className="text-sm text-slate-500"
                onClick={() => {
                  setShowAddModal(false)
                  resetForm()
                }}
              >
                关闭
              </button>
            </div>

            <form className="mt-4 space-y-4" onSubmit={(event) => event.preventDefault()}>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  提交方式 <span className="text-rose-500">*</span>
                </label>
                <select className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" name="repo_type" value={form.repo_type} onChange={handleChange}>
                  <option value="git">Git 仓库</option>
                  <option value="filesystem">文件上传</option>
                </select>
                <p className="text-xs text-slate-400">选择学生提交作业的方式。</p>
              </div>

              {isGit ? (
                <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    学生通过 Git 仓库提交作业，系统将从远程仓库读取内容。
                  </p>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      Git 仓库 URL <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="url"
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      name="git_url"
                      value={form.git_url}
                      onChange={handleChange}
                      placeholder="https://github.com/user/repo.git"
                      required
                    />
                    <p className="text-xs text-slate-400">支持 https、git、ssh 协议。</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">
                        分支名称 <span className="text-rose-500">*</span>
                      </label>
                      <button
                        type="button"
                        className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-600"
                        onClick={fetchCreateBranches}
                        disabled={branchLoading || !form.git_url.trim()}
                      >
                        {branchLoading ? '加载中...' : '获取分支'}
                      </button>
                    </div>
                    <select
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      name="git_branch"
                      value={form.git_branch}
                      onChange={handleChange}
                      disabled={branchOptions.length === 0}
                      required
                    >
                      {branchOptions.length === 0 ? <option value="">请先获取分支</option> : null}
                      {branchOptions.map((branch) => (
                        <option key={branch} value={branch}>
                          {branch}
                        </option>
                      ))}
                    </select>
                    {branchError ? (
                      <p className="text-xs text-rose-600">{branchError}</p>
                    ) : (
                      <p className="text-xs text-slate-400">从远程仓库分支列表中选择。</p>
                    )}
                  </div>
                  {showAuthFields ? (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">认证信息（可选）</label>
                      <input
                        type="text"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                        name="git_username"
                        value={form.git_username}
                        onChange={handleChange}
                        placeholder="Git 用户名 / 账号（HTTPS 私有仓库）"
                      />
                      <input
                        type="password"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                        name="git_password"
                        value={form.git_password}
                        onChange={handleChange}
                        placeholder="Git 密码 / Token（HTTPS 私有仓库）"
                      />
                    </div>
                  ) : null}
                </div>
              ) : null}

              {isFilesystem ? (
                <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    学生通过文件上传提交作业，系统按固定目录结构保存。
                  </p>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      存储路径 <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      name="filesystem_path"
                      value={form.filesystem_path}
                      onChange={handleChange}
                      placeholder="例如：D:\\homework"
                      required
                    />
                    <p className="text-xs text-slate-400">
                      目录结构固定为：课程/班级/作业次数/文件。
                    </p>
                  </div>
                </div>
              ) : null}

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  name="description"
                  rows="3"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="作业配置描述（可选）"
                />
              </div>
            </form>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm"
                onClick={() => {
                  setShowAddModal(false)
                  resetForm()
                }}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
                onClick={handleCreate}
                disabled={saving}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showEditModal && editing ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">编辑作业配置</h2>
              <button
                type="button"
                className="text-sm text-slate-500"
                onClick={() => {
                  setShowEditModal(false)
                  setEditing(null)
                }}
              >
                关闭
              </button>
            </div>

            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              提交方式不可修改，以保护已提交的学生作业数据。
            </div>

            <form className="mt-4 space-y-4" onSubmit={(event) => event.preventDefault()}>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">提交方式</label>
                <input
                  type="text"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={getStorageLabel(editing.repo_type)}
                  readOnly
                />
              </div>

              {editing.repo_type === 'git' ? (
                <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Git 仓库 URL</label>
                    <input
                      type="url"
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={editing.git_url}
                      onChange={(event) => setEditing({ ...editing, git_url: event.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">
                        分支名称 <span className="text-rose-500">*</span>
                      </label>
                      <button
                        type="button"
                        className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-600"
                        onClick={fetchEditBranches}
                        disabled={editBranchLoading || !editing.git_url}
                      >
                        {editBranchLoading ? '加载中...' : '获取分支'}
                      </button>
                    </div>
                    <select
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={editing.git_branch}
                      onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })}
                      disabled={editBranchOptions.length === 0}
                      required
                    >
                      {editBranchOptions.length === 0 ? <option value="">请先获取分支</option> : null}
                      {editBranchOptions.map((branch) => (
                        <option key={branch} value={branch}>
                          {branch}
                        </option>
                      ))}
                    </select>
                    {editBranchError ? (
                      <p className="text-xs text-rose-600">{editBranchError}</p>
                    ) : (
                      <p className="text-xs text-slate-400">从远程仓库分支列表中选择。</p>
                    )}
                  </div>
                  {showEditAuthFields ? (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">认证信息（可选）</label>
                      <input
                        type="text"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                        value={editing.git_username || ''}
                        onChange={(event) => setEditing({ ...editing, git_username: event.target.value })}
                        placeholder="Git 用户名 / 账号（HTTPS 私有仓库）"
                      />
                      <input
                        type="password"
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                        value={editing.git_password || ''}
                        onChange={(event) => setEditing({ ...editing, git_password: event.target.value })}
                        placeholder="Git 密码 / Token（HTTPS 私有仓库）"
                      />
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">存储路径</label>
                  <input
                    type="text"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={editing.filesystem_path}
                    onChange={(event) => setEditing({ ...editing, filesystem_path: event.target.value })}
                  />
                  <p className="text-xs text-slate-400">目录结构固定为：课程/班级/作业次数。</p>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  rows="3"
                  value={editing.description || ''}
                  onChange={(event) => setEditing({ ...editing, description: event.target.value })}
                />
              </div>
            </form>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm"
                onClick={() => {
                  setShowEditModal(false)
                  setEditing(null)
                }}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
                onClick={handleUpdate}
                disabled={saving}
              >
                {saving ? '更新中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
