import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function ClassList() {
  const [courses, setCourses] = useState([])
  const [classes, setClasses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')
  const [form, setForm] = useState({ course_id: '', name: '', student_count: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadCourses = async () => {
    const response = await apiFetch('/grading/api/courses/')
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.status === 'success') {
      setCourses(data.courses || [])
    }
  }

  const loadClasses = async (courseId = selectedCourse) => {
    setLoading(true)
    setError('')
    try {
      const query = courseId ? `?course_id=${courseId}` : ''
      const response = await apiFetch(`/grading/api/classes/${query}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to load classes')
      }
      setClasses(data.classes || [])
    } catch (err) {
      setError(err.message || 'Failed to load classes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCourses().then(() => loadClasses())
  }, [])

  const handleFilter = (event) => {
    const value = event.target.value
    setSelectedCourse(value)
    loadClasses(value)
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    setError('')
    const payload = new URLSearchParams(form)
    const response = await apiFetch('/grading/api/classes/create/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || 'Failed to create class')
      return
    }
    setForm({ course_id: '', name: '', student_count: '' })
    loadClasses(selectedCourse)
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Create Class</h5>
          </div>
          <div className="card-body">
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label">Course</label>
                <select
                  className="form-select"
                  name="course_id"
                  value={form.course_id}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select course</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">Class Name</label>
                <input
                  className="form-control"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Student Count</label>
                <input
                  className="form-control"
                  name="student_count"
                  value={form.student_count}
                  onChange={handleChange}
                />
              </div>
              <button className="btn btn-primary w-100" type="submit">
                Create Class
              </button>
            </form>
          </div>
        </div>
      </div>
      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Classes</h5>
            <select className="form-select form-select-sm" style={{ width: '200px' }} value={selectedCourse} onChange={handleFilter}>
              <option value="">All courses</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.name}
                </option>
              ))}
            </select>
          </div>
          <div className="card-body">
            {loading ? <div className="alert alert-info">Loading...</div> : null}
            {!loading && classes.length === 0 ? (
              <div className="alert alert-secondary">No classes found.</div>
            ) : null}
            <div className="table-responsive">
              <table className="table table-sm">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Course</th>
                    <th>Students</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {classes.map((cls) => (
                    <tr key={cls.id}>
                      <td>{cls.name}</td>
                      <td>{cls.course?.name}</td>
                      <td>{cls.student_count}</td>
                      <td>{cls.created_at ? new Date(cls.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
