import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'

const emptyAssignment = {
  name: '',
  storage_type: '',
  description: '',
  course_id: '',
  class_id: '',
  git_url: '',
  git_branch: 'main',
  git_username: '',
  git_password: '',
}

export default function AssignmentManagement() {
  const [assignments, setAssignments] = useState([])
  const [courses, setCourses] = useState([])
  const [classes, setClasses] = useState([])
  const [filters, setFilters] = useState({ course_id: '', class_id: '', storage_type: '' })
  const [form, setForm] = useState(emptyAssignment)
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const isGit = useMemo(() => form.storage_type === 'git', [form.storage_type])

  const loadAssignments = async (params = filters) => {
    setLoading(true)
    setError('')
    try {
      const query = new URLSearchParams()
      if (params.course_id) query.append('course_id', params.course_id)
      if (params.class_id) query.append('class_id', params.class_id)
      if (params.storage_type) query.append('storage_type', params.storage_type)

      const response = await apiFetch(`/grading/api/assignments/?${query.toString()}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to load assignments')
      }
      setAssignments(data.assignments || [])
      setCourses(data.courses || [])
      setClasses(data.classes || [])
    } catch (err) {
      setError(err.message || 'Failed to load assignments')
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
    const cleared = { course_id: '', class_id: '', storage_type: '' }
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

  const handleCreate = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('name', form.name)
      payload.append('storage_type', form.storage_type)
      payload.append('course_id', form.course_id)
      payload.append('class_id', form.class_id)
      if (form.description) payload.append('description', form.description)
      if (isGit) {
        payload.append('git_url', form.git_url)
        payload.append('git_branch', form.git_branch || 'main')
        if (form.git_username) payload.append('git_username', form.git_username)
        if (form.git_password) payload.append('git_password', form.git_password)
      }

      const response = await apiFetch('/grading/assignments/create/', {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to create assignment')
      }
      setForm(emptyAssignment)
      loadAssignments()
    } catch (err) {
      setError(err.message || 'Failed to create assignment')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (assignment) => {
    setEditing({
      id: assignment.id,
      name: assignment.name,
      description: assignment.description || '',
      git_url: assignment.git_url || '',
      git_branch: assignment.git_branch || 'main',
    })
  }

  const handleUpdate = async (event) => {
    event.preventDefault()
    if (!editing) return
    setSaving(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('assignment_id', editing.id)
      payload.append('name', editing.name)
      if (editing.description) payload.append('description', editing.description)
      if (editing.git_url) payload.append('git_url', editing.git_url)
      if (editing.git_branch) payload.append('git_branch', editing.git_branch)

      const response = await apiFetch(`/grading/assignments/${editing.id}/edit/`, {
        method: 'POST',
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to update assignment')
      }
      setEditing(null)
      loadAssignments()
    } catch (err) {
      setError(err.message || 'Failed to update assignment')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (assignment) => {
    if (!window.confirm(`Delete assignment "${assignment.name}"?`)) {
      return
    }
    const response = await apiFetch(`/grading/assignments/${assignment.id}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ assignment_id: assignment.id }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || 'Failed to delete assignment')
      return
    }
    loadAssignments()
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Create Assignment</h5>
          </div>
          <div className="card-body">
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label">Name</label>
                <input className="form-control" name="name" value={form.name} onChange={handleFormChange} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Course</label>
                <select className="form-select" name="course_id" value={form.course_id} onChange={handleCourseSelection} required>
                  <option value="">Select course</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">Class</label>
                <select className="form-select" name="class_id" value={form.class_id} onChange={handleFormChange} required>
                  <option value="">Select class</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">Storage Type</label>
                <select className="form-select" name="storage_type" value={form.storage_type} onChange={handleFormChange} required>
                  <option value="">Select type</option>
                  <option value="filesystem">File Upload</option>
                  <option value="git">Git Repository</option>
                </select>
              </div>
              {isGit ? (
                <>
                  <div className="mb-3">
                    <label className="form-label">Git URL</label>
                    <input className="form-control" name="git_url" value={form.git_url} onChange={handleFormChange} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Git Branch</label>
                    <input className="form-control" name="git_branch" value={form.git_branch} onChange={handleFormChange} />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Git Username</label>
                    <input className="form-control" name="git_username" value={form.git_username} onChange={handleFormChange} />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Git Password / Token</label>
                    <input className="form-control" type="password" name="git_password" value={form.git_password} onChange={handleFormChange} />
                  </div>
                </>
              ) : null}
              <div className="mb-3">
                <label className="form-label">Description</label>
                <textarea className="form-control" name="description" rows="3" value={form.description} onChange={handleFormChange} />
              </div>
              <button className="btn btn-primary w-100" type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Create Assignment'}
              </button>
            </form>
          </div>
        </div>
        {editing ? (
          <div className="card mt-4">
            <div className="card-header">
              <h6 className="mb-0">Edit Assignment</h6>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpdate}>
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input className="form-control" value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Description</label>
                  <textarea className="form-control" rows="3" value={editing.description} onChange={(event) => setEditing({ ...editing, description: event.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git URL</label>
                  <input className="form-control" value={editing.git_url} onChange={(event) => setEditing({ ...editing, git_url: event.target.value })} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Git Branch</label>
                  <input className="form-control" value={editing.git_branch} onChange={(event) => setEditing({ ...editing, git_branch: event.target.value })} />
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
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Assignments</h5>
          </div>
          <div className="card-body">
            <form className="row g-3 mb-3" onSubmit={applyFilters}>
              <div className="col-md-4">
                <label className="form-label">Course</label>
                <select className="form-select" name="course_id" value={filters.course_id} onChange={handleFilterChange}>
                  <option value="">All</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label">Class</label>
                <select className="form-select" name="class_id" value={filters.class_id} onChange={handleFilterChange}>
                  <option value="">All</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label">Storage Type</label>
                <select className="form-select" name="storage_type" value={filters.storage_type} onChange={handleFilterChange}>
                  <option value="">All</option>
                  <option value="filesystem">File Upload</option>
                  <option value="git">Git Repository</option>
                </select>
              </div>
              <div className="col-12 d-flex gap-2">
                <button className="btn btn-outline-primary" type="submit">
                  Filter
                </button>
                <button className="btn btn-outline-secondary" type="button" onClick={resetFilters}>
                  Reset
                </button>
              </div>
            </form>

            {loading ? <div className="alert alert-info">Loading...</div> : null}
            {!loading && assignments.length === 0 ? (
              <div className="alert alert-secondary">No assignments found.</div>
            ) : null}
            <div className="d-flex flex-column gap-3">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="border rounded p-3 bg-white">
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 className="mb-1">{assignment.name}</h6>
                      <div className="text-muted small">
                        {assignment.course?.name} · {assignment.class_obj?.name}
                      </div>
                      <div className="text-muted small">
                        {assignment.storage_type === 'git' ? 'Git' : 'File Upload'}
                      </div>
                    </div>
                    <div className="d-flex gap-2">
                      <button className="btn btn-outline-primary btn-sm" onClick={() => startEdit(assignment)}>
                        Edit
                      </button>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => handleDelete(assignment)}>
                        Delete
                      </button>
                    </div>
                  </div>
                  {assignment.description ? <div className="text-muted mt-2">{assignment.description}</div> : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
