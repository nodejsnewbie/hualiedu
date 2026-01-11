import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'

const emptyAssignment = {
  name: '',
  course_id: '',
  class_id: '',
  git_url: '',
  git_branch: 'main',
  git_username: '',
  git_password: '',
}

const getGitAuthMode = (gitUrl) => {
  const value = (gitUrl || '').trim()
  if (!value) return ''
  if (value.startsWith('http://') || value.startsWith('https://')) return 'http'
  if (value.startsWith('git@') || value.startsWith('ssh://')) return 'ssh'
  if (value.startsWith('git://')) return 'git'
  return ''
}

const getGitAuthLabel = (mode) => {
  if (mode === 'ssh') return 'SSH 私钥'
  return 'Git 密码 / Token'
}

const getGitAuthHint = (mode) => {
  if (mode === 'http') return 'HTTPS 仓库需要用户名与密码/Token。'
  if (mode === 'ssh') return 'SSH 仓库需要私钥内容（以 -----BEGIN 开头）。'
  if (mode === 'git') return 'git:// 协议通常无需凭据。'
  return '请输入正确的 Git 仓库地址。'
}

export default function AssignmentManagement() {
  const [assignments, setAssignments] = useState([])
  const [courses, setCourses] = useState([])
  const [classes, setClasses] = useState([])
  const [filters, setFilters] = useState({ course_id: '', class_id: '' })
  const [form, setForm] = useState(emptyAssignment)
  const [editing, setEditing] = useState(null)
  const [editingSource, setEditingSource] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const gitAuthMode = useMemo(() => getGitAuthMode(form.git_url), [form.git_url])
  const editAuthMode = useMemo(() => (editing ? getGitAuthMode(editing.git_url) : ''), [editing])

  const loadAssignments = async (params = filters) => {
    setLoading(true)
    setError('')
    try {
      const query = new URLSearchParams()
      if (params.course_id) query.append('course_id', params.course_id)
      if (params.class_id) query.append('class_id', params.class_id)

      const response = await apiFetch(`/grading/api/assignments/?${query.toString()}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载作业失败')
      }
      setAssignments(data.assignments || [])
      setCourses(data.courses || [])
      setClasses(data.classes || [])
    } catch (err) {
      setError(err.message || '加载作业失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAssignments()
  }, [])

  const handleFilterChange = (event) => {
    const { name, value } = event.target
    setFilters((prev) => ({ ...prev, [name]: value }))
  }

  const applyFilters = (event) => {
    event.preventDefault()
    loadAssignments(filters)
  }

  const resetFilters = () => {
    const cleared = { course_id: '', class_id: '' }
    setFilters(cleared)
    loadAssignments(cleared)
  }

  const handleFormChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const fetchClassesForCourse = async (courseId) => {
    if (!courseId) {
      setClasses([])
      return
    }
    const response = await apiFetch(`/grading/api/course-classes/?course_id=${courseId}`)
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.status === 'success') {
      setClasses(data.classes || [])
    }
  }

  const handleCourseSelection = async (event) => {
    const courseId = event.target.value
    setForm((prev) => ({ ...prev, course_id: courseId, class_id: '' }))
    await fetchClassesForCourse(courseId)
  }

  const validateGitAuth = (mode, username, password) => {
    if (!mode) return '请输入正确的 Git 仓库地址'
    if (mode === 'http') {
      if (!username.trim() || !password) return 'HTTPS 仓库需要用户名和密码/Token'
      return ''
    }
    if (mode === 'ssh') {
      if (!password.trim()) return 'SSH 仓库需要私钥'
      return ''
    }
    return ''
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const authError = validateGitAuth(gitAuthMode, form.git_username, form.git_password)
      if (authError) {
        setError(authError)
        setSaving(false)
        return
      }

      const payload = new FormData()
      payload.append('name', form.name)
      payload.append('storage_type', 'git')
      payload.append('course_id', form.course_id)
      payload.append('class_id', form.class_id)
      payload.append('git_url', form.git_url)
      payload.append('git_branch', form.git_branch || 'main')
      if (gitAuthMode === 'http') {
        payload.append('git_username', form.git_username.trim())
        payload.append('git_password', form.git_password)
      } else if (gitAuthMode === 'ssh') {
        payload.append('git_password', form.git_password)
      }

      const response = await apiFetch('/grading/assignments/create/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '创建作业失败')
      }
      setForm(emptyAssignment)
      loadAssignments()
    } catch (err) {
      setError(err.message || '创建作业失败')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (assignment) => {
    const next = {
      id: assignment.id,
      name: assignment.name,
      git_url: assignment.git_url || '',
      git_branch: assignment.git_branch || 'main',
      git_username: '',
      git_password: '',
    }
    setEditing(next)
    setEditingSource({ ...next })
  }

  const handleUpdate = async (event) => {
    event.preventDefault()
    if (!editing) return
    setSaving(true)
    setError('')
    try {
      const gitUrlChanged = editingSource ? editing.git_url !== editingSource.git_url : true
      const needsAuth = gitUrlChanged || editing.git_username || editing.git_password
      if (needsAuth) {
        const authError = validateGitAuth(editAuthMode, editing.git_username, editing.git_password)
        if (authError) {
          setError(authError)
          setSaving(false)
          return
        }
      }

      const payload = new FormData()
      payload.append('assignment_id', editing.id)
      payload.append('name', editing.name)
      if (gitUrlChanged) payload.append('git_url', editing.git_url)
      if (!editingSource || editing.git_branch !== editingSource.git_branch) {
        payload.append('git_branch', editing.git_branch)
      }
      if (editing.git_username) payload.append('git_username', editing.git_username)
      if (editing.git_password) payload.append('git_password', editing.git_password)

      const response = await apiFetch(`/grading/assignments/${editing.id}/edit/`, {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '更新作业失败')
      }
      setEditing(null)
      setEditingSource(null)
      loadAssignments()
    } catch (err) {
      setError(err.message || '更新作业失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (assignment) => {
    if (!window.confirm(`确定删除作业 "${assignment.name}" 吗？`)) {
      return
    }
    const response = await apiFetch(`/grading/assignments/${assignment.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ assignment_id: assignment.id }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || '删除作业失败')
      return
    }
    loadAssignments()
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">创建作业</h5>
          </div>
          <div className="card-body">
            <p className="text-muted small">
              作业管理仅维护 Git 仓库地址，保存前会验证仓库连接。
            </p>
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label">作业名称/次数</label>
                <input className="form-control" name="name" value={form.name} onChange={handleFormChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">课程</label>
                <select className="form-select" name="course_id" value={form.course_id} onChange={handleCourseSelection} required>
                  <option value="">请选择课程</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">班级</label>
                <select className="form-select" name="class_id" value={form.class_id} onChange={handleFormChange} required>
                  <option value="">请选择班级</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">Git 地址</label>
                <input className="form-control" name="git_url" value={form.git_url} onChange={handleFormChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Git 分支</label>
                <input className="form-control" name="git_branch" value={form.git_branch} onChange={handleFormChange} />
              </div>
              {gitAuthMode === 'http' ? (
                <div className="mb-3">
                  <label className="form-label">Git 用户名</label>
                  <input className="form-control" name="git_username" value={form.git_username} onChange={handleFormChange} required />
                </div>
              ) : null}
              {(gitAuthMode === 'http' || gitAuthMode === 'ssh') ? (
                <div className="mb-3">
                  <label className="form-label">{getGitAuthLabel(gitAuthMode)}</label>
                  {gitAuthMode === 'ssh' ? (
                    <textarea
                      className="form-control"
                      name="git_password"
                      rows="4"
                      value={form.git_password}
                      onChange={handleFormChange}
                      required
                    />
                  ) : (
                    <input
                      className="form-control"
                      type="password"
                      name="git_password"
                      value={form.git_password}
                      onChange={handleFormChange}
                      required
                    />
                  )}
                  <div className="form-text">{getGitAuthHint(gitAuthMode)}</div>
                </div>
              ) : null}
              <button className="btn btn-primary w-100" type="submit" disabled={saving}>
                {saving ? '保存中...' : '创建作业'}
              </button>
            </form>
          </div>
        </div>
        {editing ? (
          <div className="card mt-4">
            <div className="card-header">
              <h6 className="mb-0">编辑作业</h6>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpdate}>
                <div className="mb-3">
                  <label className="form-label">名称</label>
                  <input className="form-control" value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 地址</label>
                  <input className="form-control" value={editing.git_url} onChange={(event) => setEditing({ ...editing, git_url: event.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git 分支</label>
                  <input className="form-control" value={editing.git_branch} onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })} />
                </div>
                {editAuthMode === 'http' ? (
                  <div className="mb-3">
                    <label className="form-label">Git 用户名</label>
                    <input
                      className="form-control"
                      value={editing.git_username}
                      onChange={(event) => setEditing({ ...editing, git_username: event.target.value })}
                    />
                  </div>
                ) : null}
                {(editAuthMode === 'http' || editAuthMode === 'ssh') ? (
                  <div className="mb-3">
                    <label className="form-label">{getGitAuthLabel(editAuthMode)}</label>
                    {editAuthMode === 'ssh' ? (
                      <textarea
                        className="form-control"
                        rows="4"
                        value={editing.git_password}
                        onChange={(event) => setEditing({ ...editing, git_password: event.target.value })}
                      />
                    ) : (
                      <input
                        className="form-control"
                        type="password"
                        value={editing.git_password}
                        onChange={(event) => setEditing({ ...editing, git_password: event.target.value })}
                      />
                    )}
                    <div className="form-text">{getGitAuthHint(editAuthMode)}</div>
                  </div>
                ) : null}
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" type="submit" disabled={saving}>
                    {saving ? '更新中...' : '更新'}
                  </button>
                  <button className="btn btn-outline-secondary" type="button" onClick={() => { setEditing(null); setEditingSource(null) }}>
                    取消
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">作业列表</h5>
          </div>
          <div className="card-body">
            <form className="row g-3 mb-3" onSubmit={applyFilters}>
              <div className="col-md-4">
                <label className="form-label">课程</label>
                <select className="form-select" name="course_id" value={filters.course_id} onChange={handleFilterChange}>
                  <option value="">全部</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label">班级</label>
                <select className="form-select" name="class_id" value={filters.class_id} onChange={handleFilterChange}>
                  <option value="">全部</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-12 d-flex gap-2">
                <button className="btn btn-outline-primary" type="submit">
                  筛选
                </button>
                <button className="btn btn-outline-secondary" type="button" onClick={resetFilters}>
                  重置
                </button>
              </div>
            </form>

            {loading ? <div className="alert alert-info">加载中...</div> : null}
            {!loading && assignments.length === 0 ? (
              <div className="alert alert-secondary">暂无作业。</div>
            ) : null}
            <div className="d-flex flex-column gap-3">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="border rounded p-3 bg-white">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 className="mb-1">{assignment.name}</h6>
                      <div className="text-muted small">
                        {(assignment.course?.name || '') + ' · ' + (assignment.class_obj?.name || '')}
                      </div>
                      <div className="text-muted small">
                        Git
                        {assignment.created_at ? (
                          <> · 创建时间 {new Date(assignment.created_at).toLocaleString()}</>
                        ) : null}
                      </div>
                    </div>
                    <div className="d-flex gap-2">
                      <button className="btn btn-outline-primary btn-sm" onClick={() => startEdit(assignment)}>
                        编辑
                      </button>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => handleDelete(assignment)}>
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
