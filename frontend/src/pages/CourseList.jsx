import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const COURSE_TYPES = [
  { value: 'theory', label: '理论' },
  { value: 'lab', label: '实验' },
  { value: 'practice', label: '实践' },
  { value: 'mixed', label: '综合' },
]

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
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">课程管理</h1>
            <p className="mt-1 text-sm text-slate-500">创建课程并维护课程信息。</p>
          </div>
          <button
            type="button"
            onClick={loadCourses}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          >
            刷新
          </button>
        </header>

        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">创建课程</h2>
            <p className="mt-1 text-xs text-slate-500">填写课程名称与类型。</p>

            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              {semester ? `当前学期：${semester.name}` : '暂无激活学期。'}
            </div>

            {error ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="text-sm font-medium text-slate-700">课程名称</label>
                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">课程类型</label>
                <select
                  name="course_type"
                  value={form.course_type}
                  onChange={handleChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                >
                  <option value="">请选择类型</option>
                  {COURSE_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  name="description"
                  rows="3"
                  value={form.description}
                  onChange={handleChange}
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {saving ? '保存中...' : '创建课程'}
              </button>
            </form>
          </section>

          <section className="card-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-slate-800">课程列表</h2>
                <p className="mt-1 text-xs text-slate-500">查看所有课程信息。</p>
              </div>
            </div>

            {loading ? (
              <div className="mt-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
                加载中...
              </div>
            ) : null}
            {!loading && courses.length === 0 ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无课程。
              </div>
            ) : null}

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {courses.map((course) => (
                <div
                  key={course.id}
                  className="card-surface p-4"
                >
                  <div className="text-sm font-semibold text-slate-900">{course.name}</div>
                  <div className="mt-1 text-xs text-slate-500">{course.course_type_display}</div>
                  {course.description ? (
                    <p className="mt-3 text-xs text-slate-600">{course.description}</p>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
