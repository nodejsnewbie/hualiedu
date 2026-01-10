import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function CourseList() {
  const [courses, setCourses] = useState([])
  const [semester, setSemester] = useState(null)
  const [form, setForm] = useState({ name: '', course_type: '', description: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadCourses = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/grading/api/courses/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载课程失败')
      }
      setCourses(data.courses || [])
      setSemester(data.current_semester || null)
    } catch (err) {
      setError(err.message || '加载课程失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCourses()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = new URLSearchParams(form)
      const response = await apiFetch('/grading/api/courses/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: payload,
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '创建课程失败')
      }
      setForm({ name: '', course_type: '', description: '' })
      loadCourses()
    } catch (err) {
      setError(err.message || '创建课程失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">创建课程</h5>
          </div>
          <div className="card-body">
            {semester ? (
              <div className="alert alert-info">当前学期：{semester.name}</div>
            ) : (
              <div className="alert alert-warning">暂无激活学期。</div>
            )}
            {error ? <div className="alert alert-danger">{error}</div> : null}
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label">课程名称</label>
                <input
                  className="form-control"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label">课程类型</label>
                <select
                  className="form-select"
                  name="course_type"
                  value={form.course_type}
                  onChange={handleChange}
                  required
                >
                  <option value="">请选择类型</option>
                  <option value="theory">理论</option>
                  <option value="lab">实验</option>
                  <option value="practice">实践</option>
                  <option value="mixed">综合</option>
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">描述</label>
                <textarea
                  className="form-control"
                  name="description"
                  rows="3"
                  value={form.description}
                  onChange={handleChange}
                />
              </div>
              <button className="btn btn-primary w-100" type="submit" disabled={saving}>
                {saving ? '保存中...' : '创建课程'}
              </button>
            </form>
          </div>
        </div>
      </div>

      <div className="col-lg-8">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">课程列表</h5>
            <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadCourses}>
              刷新
            </button>
          </div>
          <div className="card-body">
            {loading ? <div className="alert alert-info">加载中...</div> : null}
            {!loading && courses.length === 0 ? (
              <div className="alert alert-secondary">暂无课程。</div>
            ) : null}
            <div className="row g-3">
              {courses.map((course) => (
                <div className="col-md-6" key={course.id}>
                  <div className="border rounded p-3 bg-white h-100">
                    <div className="fw-semibold">{course.name}</div>
                    <div className="text-muted small">{course.course_type_display}</div>
                    {course.description ? (
                      <div className="text-muted small mt-2">{course.description}</div>
                    ) : null}
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
