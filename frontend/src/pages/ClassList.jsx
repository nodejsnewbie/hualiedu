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
        throw new Error((data && data.message) || '加载班级失败')
      }
      setClasses(data.classes || [])
    } catch (err) {
      setError(err.message || '加载班级失败')
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
      setError((data && data.message) || '创建班级失败')
      return
    }
    setForm({ course_id: '', name: '', student_count: '' })
    loadClasses(selectedCourse)
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">班级管理</h1>
          <p className="mt-1 text-sm text-slate-500">创建班级并查看班级列表。</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">创建班级</h2>
            <p className="mt-1 text-xs text-slate-500">填写课程、班级名称与人数。</p>

            {error ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <form className="mt-4 space-y-4" onSubmit={handleCreate}>
              <div>
                <label className="text-sm font-medium text-slate-700">课程</label>
                <select
                  name="course_id"
                  value={form.course_id}
                  onChange={handleChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                >
                  <option value="">请选择课程</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">班级名称</label>
                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">学生人数</label>
                <input
                  name="student_count"
                  value={form.student_count}
                  onChange={handleChange}
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />
              </div>
              <button
                type="submit"
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                创建班级
              </button>
            </form>
          </section>

          <section className="card-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-slate-800">班级列表</h2>
                <p className="mt-1 text-xs text-slate-500">按课程筛选班级。</p>
              </div>
              <select
                value={selectedCourse}
                onChange={handleFilter}
                className="w-56 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
              >
                <option value="">全部课程</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
            </div>

            {loading ? (
              <div className="mt-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
                加载中...
              </div>
            ) : null}
            {!loading && classes.length === 0 ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                暂无班级。
              </div>
            ) : null}

            <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-slate-600">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">名称</th>
                    <th className="px-4 py-2 text-left font-medium">课程</th>
                    <th className="px-4 py-2 text-left font-medium">人数</th>
                    <th className="px-4 py-2 text-left font-medium">创建时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {classes.map((cls) => (
                    <tr key={cls.id} className="text-slate-700">
                      <td className="px-4 py-2 font-medium text-slate-800">{cls.name}</td>
                      <td className="px-4 py-2">{cls.course?.name}</td>
                      <td className="px-4 py-2">{cls.student_count}</td>
                      <td className="px-4 py-2">
                        {cls.created_at ? new Date(cls.created_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
