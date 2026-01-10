import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const weekdays = [
  { key: 1, label: 'Mon' },
  { key: 2, label: 'Tue' },
  { key: 3, label: 'Wed' },
  { key: 4, label: 'Thu' },
  { key: 5, label: 'Fri' },
  { key: 6, label: 'Sat' },
  { key: 7, label: 'Sun' },
]

const periods = [
  { key: 1, label: 'Period 1' },
  { key: 2, label: 'Period 2' },
  { key: 3, label: 'Period 3' },
  { key: 4, label: 'Period 4' },
  { key: 5, label: 'Period 5' },
]

export default function CalendarPage() {
  const [week, setWeek] = useState(1)
  const [schedule, setSchedule] = useState({})
  const [error, setError] = useState('')

  const loadSchedule = async (weekNumber = week) => {
    setError('')
    const response = await apiFetch(`/grading/get-schedule-data/?week=${weekNumber}`)
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || 'Failed to load schedule')
      return
    }
    setSchedule(data.schedule_data || {})
  }

  useEffect(() => {
    loadSchedule(week)
  }, [])

  const handleSubmit = (event) => {
    event.preventDefault()
    loadSchedule(week)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Calendar</h4>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        <form className="row g-2 align-items-center mb-3" onSubmit={handleSubmit}>
          <div className="col-auto">
            <label className="col-form-label">Week</label>
          </div>
          <div className="col-auto">
            <input
              className="form-control"
              type="number"
              min="1"
              value={week}
              onChange={(event) => setWeek(event.target.value)}
            />
          </div>
          <div className="col-auto">
            <button className="btn btn-primary" type="submit">
              Load
            </button>
          </div>
        </form>

        <div className="table-responsive">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>Period</th>
                {weekdays.map((day) => (
                  <th key={day.key}>{day.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {periods.map((period) => (
                <tr key={period.key}>
                  <th>{period.label}</th>
                  {weekdays.map((day) => {
                    const cellKey = `${day.key}_${period.key}`
                    const items = schedule[cellKey] || []
                    return (
                      <td key={cellKey}>
                        {items.length === 0 ? (
                          <span className="text-muted">-</span>
                        ) : (
                          items.map((item, index) => (
                            <div key={`${cellKey}-${index}`} className="mb-2">
                              <div className="fw-semibold">{item.course_name}</div>
                              <div className="small text-muted">{item.location}</div>
                            </div>
                          ))
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
