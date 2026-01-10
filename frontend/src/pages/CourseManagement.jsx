import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const weekdayOptions = [
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
  { value: 7, label: 'Sun' },
]

const periodOptions = [
  { value: 1, label: 'Period 1 (08:00-09:40)' },
  { value: 2, label: 'Period 2 (10:00-11:40)' },
  { value: 3, label: 'Period 3 (14:00-15:40)' },
  { value: 4, label: 'Period 4 (16:00-17:40)' },
  { value: 5, label: 'Period 5 (19:00-20:40)' },
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
      setError((data && data.message) || 'Failed to load course management data')
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
      setError((data && data.message) || 'Failed to add course')
      return
    }
    setCourseForm({ course_name: '', class_name: '', location: '', description: '' })
    loadData()
  }

  const deleteCourse = async (courseId, name) => {
    if (!window.confirm(`Delete course "${name}"?`)) {
      return
    }
    const response = await apiFetch('/grading/delete-course/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ course_id: courseId }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || 'Failed to delete course')
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
      setError((data && data.message) || 'Failed to save schedule')
      return
    }
    setActiveCourseId(null)
    loadData()
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Course Management</h4>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        {semester ? (
          <div className="alert alert-info">
            Current semester: {semester.name} ({semester.week_count} weeks)
          </div>
        ) : (
          <div className="alert alert-warning">No active semester configured.</div>
        )}

        <div className="border rounded p-3 mb-4">
          <h6>Add Course</h6>
          <form onSubmit={submitCourse}>
            <div className="row g-2">
              <div className="col-md-4">
                <input
                  className="form-control"
                  name="course_name"
                  placeholder="Course name"
                  value={courseForm.course_name}
                  onChange={handleCourseChange}
                  required
                />
              </div>
              <div className="col-md-4">
                <input
                  className="form-control"
                  name="class_name"
                  placeholder="Class name"
                  value={courseForm.class_name}
                  onChange={handleCourseChange}
                />
              </div>
              <div className="col-md-4">
                <input
                  className="form-control"
                  name="location"
                  placeholder="Location"
                  value={courseForm.location}
                  onChange={handleCourseChange}
                  required
                />
              </div>
              <div className="col-12">
                <textarea
                  className="form-control"
                  name="description"
                  placeholder="Description"
                  value={courseForm.description}
                  onChange={handleCourseChange}
                  rows="2"
                />
              </div>
              <div className="col-12">
                <button className="btn btn-primary" type="submit">
                  Add Course
                </button>
              </div>
            </div>
          </form>
        </div>

        {courses.length === 0 ? (
          <div className="alert alert-secondary">No courses available.</div>
        ) : (
          courses.map((course) => (
            <div key={course.id} className="border rounded p-3 mb-3">
              <div className="d-flex justify-content-between align-items-start">
                <div>
                  <div className="fw-semibold">{course.name}</div>
                  <div className="text-muted small">{course.location}</div>
                  {course.class_name ? (
                    <div className="text-muted small">Class: {course.class_name}</div>
                  ) : null}
                  {course.description ? (
                    <div className="text-muted small">{course.description}</div>
                  ) : null}
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-outline-primary btn-sm" onClick={() => openScheduleForm(course.id)}>
                    Add Schedule
                  </button>
                  <button className="btn btn-outline-danger btn-sm" onClick={() => deleteCourse(course.id, course.name)}>
                    Delete
                  </button>
                </div>
              </div>
              <div className="mt-3">
                <h6>Schedules</h6>
                {course.schedules.length === 0 ? (
                  <div className="text-muted small">No schedules yet.</div>
                ) : (
                  course.schedules.map((schedule) => (
                    <div key={schedule.id} className="d-flex justify-content-between align-items-center border rounded p-2 mb-2">
                      <div className="small">
                        {schedule.weekday_display} {schedule.period_display} · {schedule.week_text}
                      </div>
                      <button className="btn btn-outline-secondary btn-sm" onClick={() => editSchedule(course.id, schedule)}>
                        Edit
                      </button>
                    </div>
                  ))
                )}
              </div>

              {activeCourseId === course.id ? (
                <div className="border rounded p-3 mt-3">
                  <h6>{scheduleForm.schedule_id ? 'Edit Schedule' : 'Add Schedule'}</h6>
                  <form onSubmit={submitSchedule}>
                    <div className="row g-2">
                      <div className="col-md-4">
                        <select
                          className="form-select"
                          name="weekday"
                          value={scheduleForm.weekday}
                          onChange={handleScheduleChange}
                          required
                        >
                          <option value="">Weekday</option>
                          {weekdayOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="col-md-4">
                        <select
                          className="form-select"
                          name="period"
                          value={scheduleForm.period}
                          onChange={handleScheduleChange}
                          required
                        >
                          <option value="">Period</option>
                          {periodOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="col-md-2">
                        <input
                          className="form-control"
                          name="start_week"
                          placeholder="Start week"
                          value={scheduleForm.start_week}
                          onChange={handleScheduleChange}
                          required
                        />
                      </div>
                      <div className="col-md-2">
                        <input
                          className="form-control"
                          name="end_week"
                          placeholder="End week"
                          value={scheduleForm.end_week}
                          onChange={handleScheduleChange}
                          required
                        />
                      </div>
                      {semester ? (
                        <div className="col-12">
                          <div className="d-flex flex-wrap gap-2">
                            {Array.from({ length: semester.week_count }).map((_, index) => {
                              const week = index + 1
                              const active = scheduleForm.weeks.includes(week)
                              return (
                                <button
                                  key={week}
                                  type="button"
                                  className={`btn btn-sm ${active ? 'btn-primary' : 'btn-outline-primary'}`}
                                  onClick={() => toggleWeek(week)}
                                >
                                  {week}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      ) : null}
                      <div className="col-12 d-flex gap-2">
                        <button className="btn btn-success" type="submit">
                          {scheduleForm.schedule_id ? 'Update Schedule' : 'Save Schedule'}
                        </button>
                        <button className="btn btn-outline-secondary" type="button" onClick={() => setActiveCourseId(null)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
