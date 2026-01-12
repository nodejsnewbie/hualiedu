import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const weekdayOptions = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

const periodOptions = [
  { value: 1, label: '第1节(08:00-09:40)' },
  { value: 2, label: '第2节(10:00-11:40)' },
  { value: 3, label: '第3节(14:00-15:40)' },
  { value: 4, label: '第4节(16:00-17:40)' },
  { value: 5, label: '第5节(19:00-20:40)' },
]

export default function CourseManagement() {
  const [semester, setSemester] = useState(null)
  const [courses, setCourses] = useState([])
  const [error, setError] = useState('')
  const [courseForm, setCourseForm] = useState({
    course_name: '',
    class_name: '',
    location: '',
    description: '',
  })
  const [activeCourseId, setActiveCourseId] = useState(null)
  const [scheduleForm, setScheduleForm] = useState({
    course_id: '',
    schedule_id: '',
    weekday: '',
    period: '',
    start_week: '',
    end_week: '',
    weeks: [],
  })

  const loadData = async () => {
    setError('')
    const response = await apiFetch('/grading/api/course-management/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '加载课程管理数据失败')
      return
    }
    setSemester(data.current_semester)
    setCourses(data.courses || [])
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCourseChange = (event) => {
    const { name, value } = event.target
    setCourseForm((prev) => ({ ...prev, [name]: value }))
  }

  const submitCourse = async (event) => {
    event.preventDefault()
    setError('')
    const payload = new URLSearchParams(courseForm)
    const response = await apiFetch('/grading/add-course/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '添加课程失败')
      return
    }
    setCourseForm({ course_name: '', class_name: '', location: '', description: '' })
    loadData()
  }

  const deleteCourse = async (courseId, name) => {
    if (!window.confirm(`确定删除课程“${name}”吗？`)) {
      return
    }
    const response = await apiFetch('/grading/delete-course/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ course_id: courseId }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || '删除课程失败')
      return
    }
    loadData()
  }

  const openScheduleForm = (courseId) => {
    setActiveCourseId(courseId)
    setScheduleForm({
      course_id: courseId,
      schedule_id: '',
      weekday: '',
      period: '',
      start_week: '',
      end_week: '',
      weeks: [],
    })
  }

  const editSchedule = async (courseId, schedule) => {
    setActiveCourseId(courseId)
    const response = await apiFetch(`/grading/get-schedule-weeks/${schedule.id}/`)
    const data = await response.json().catch(() => null)
    const weeks = data && data.week_status
      ? Object.entries(data.week_status)
          .filter(([, isActive]) => isActive)
          .map(([weekNumber]) => Number(weekNumber))
      : []
    setScheduleForm({
      course_id: courseId,
      schedule_id: schedule.id,
      weekday: schedule.weekday,
      period: schedule.period,
      start_week: schedule.start_week,
      end_week: schedule.end_week,
      weeks,
    })
  }

  const handleScheduleChange = (event) => {
    const { name, value } = event.target
    setScheduleForm((prev) => ({ ...prev, [name]: value }))
  }

  const toggleWeek = (week) => {
    setScheduleForm((prev) => {
      const exists = prev.weeks.includes(week)
      const nextWeeks = exists ? prev.weeks.filter((w) => w !== week) : [...prev.weeks, week]
      return { ...prev, weeks: nextWeeks }
    })
  }

  const submitSchedule = async (event) => {
    event.preventDefault()
    const payload = new URLSearchParams()
    payload.append('course_id', scheduleForm.course_id)
    payload.append('weekday', scheduleForm.weekday)
    payload.append('period', scheduleForm.period)
    payload.append('start_week', scheduleForm.start_week)
    payload.append('end_week', scheduleForm.end_week)
    if (scheduleForm.schedule_id) {
      payload.append('schedule_id', scheduleForm.schedule_id)
    }
    scheduleForm.weeks.forEach((week) => {
      payload.append(`week_${week}`, String(week))
    })
    const response = await apiFetch('/grading/add-schedule/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '保存课表失败')
      return
    }
    setActiveCourseId(null)
    loadData()
  }

  return (
    <div className="min-h-screen">
      <div className="page-shell flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">课程管理</h1>
          <p className="mt-1 text-sm text-slate-500">维护课程与课表安排。</p>
        </header>

        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          {semester ? `当前学期：${semester.name}（${semester.week_count}周）` : '暂无激活学期。'}
        </div>

        <section className="card-surface p-5">
          <h2 className="text-base font-semibold text-slate-800">添加课程</h2>
          <form className="mt-4 space-y-3" onSubmit={submitCourse}>
            <div className="grid gap-3 md:grid-cols-3">
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                name="course_name"
                placeholder="课程名称"
                value={courseForm.course_name}
                onChange={handleCourseChange}
                required
              />
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                name="class_name"
                placeholder="班级名称"
                value={courseForm.class_name}
                onChange={handleCourseChange}
              />
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                name="location"
                placeholder="地点"
                value={courseForm.location}
                onChange={handleCourseChange}
                required
              />
            </div>
            <textarea
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
              name="description"
              placeholder="描述"
              value={courseForm.description}
              onChange={handleCourseChange}
              rows="2"
            />
            <button
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              type="submit"
            >
              添加课程
            </button>
          </form>
        </section>

        {courses.length === 0 ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            暂无课程。
          </div>
        ) : (
          <div className="space-y-4">
            {courses.map((course) => (
              <section key={course.id} className="card-surface p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-base font-semibold text-slate-900">{course.name}</div>
                    <div className="mt-1 text-xs text-slate-500">{course.location}</div>
                    {course.class_name ? (
                      <div className="mt-1 text-xs text-slate-500">班级：{course.class_name}</div>
                    ) : null}
                    {course.description ? (
                      <div className="mt-2 text-xs text-slate-600">{course.description}</div>
                    ) : null}
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      onClick={() => openScheduleForm(course.id)}
                      type="button"
                    >
                      添加课表
                    </button>
                    <button
                      className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:bg-rose-50"
                      onClick={() => deleteCourse(course.id, course.name)}
                      type="button"
                    >
                      删除
                    </button>
                  </div>
                </div>

                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-slate-700">课表</h3>
                  {course.schedules && course.schedules.length > 0 ? (
                    <div className="mt-2 space-y-2">
                      {course.schedules.map((schedule) => (
                        <div
                          key={schedule.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
                        >
                          <div className="text-xs text-slate-700">
                            {schedule.weekday_display} {schedule.period_display} 周 {schedule.week_text}
                          </div>
                          <button
                            className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-white"
                            onClick={() => editSchedule(course.id, schedule)}
                            type="button"
                          >
                            编辑
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-slate-500">暂无课表。</div>
                  )}
                </div>

                {activeCourseId === course.id ? (
                  <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <h4 className="text-sm font-semibold text-slate-700">
                      {scheduleForm.schedule_id ? '编辑课表' : '添加课表'}
                    </h4>
                    <form className="mt-3 space-y-3" onSubmit={submitSchedule}>
                      <div className="grid gap-3 md:grid-cols-4">
                        <select
                          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                          name="weekday"
                          value={scheduleForm.weekday}
                          onChange={handleScheduleChange}
                          required
                        >
                          <option value="">星期</option>
                          {weekdayOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <select
                          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                          name="period"
                          value={scheduleForm.period}
                          onChange={handleScheduleChange}
                          required
                        >
                          <option value="">节次</option>
                          {periodOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <input
                          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                          name="start_week"
                          placeholder="起始周"
                          value={scheduleForm.start_week}
                          onChange={handleScheduleChange}
                          required
                        />
                        <input
                          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                          name="end_week"
                          placeholder="结束周"
                          value={scheduleForm.end_week}
                          onChange={handleScheduleChange}
                          required
                        />
                      </div>

                      {semester ? (
                        <div className="flex flex-wrap gap-2">
                          {Array.from({ length: semester.week_count }).map((_, index) => {
                            const week = index + 1
                            const active = scheduleForm.weeks.includes(week)
                            return (
                              <button
                                key={week}
                                type="button"
                                className={`rounded-lg border px-3 py-1 text-xs font-semibold transition ${
                                  active
                                    ? 'border-slate-900 bg-slate-900 text-white'
                                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                                }`}
                                onClick={() => toggleWeek(week)}
                              >
                                {week}
                              </button>
                            )
                          })}
                        </div>
                      ) : null}

                      <div className="flex flex-wrap gap-2">
                        <button
                          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500"
                          type="submit"
                        >
                          {scheduleForm.schedule_id ? '更新课表' : '保存课表'}
                        </button>
                        <button
                          className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-white"
                          type="button"
                          onClick={() => setActiveCourseId(null)}
                        >
                          取消
                        </button>
                      </div>
                    </form>
                  </div>
                ) : null}
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
