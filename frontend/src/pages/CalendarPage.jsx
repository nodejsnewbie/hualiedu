import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const weekdays = [
  { key: 1, label: '周一' },
  { key: 2, label: '周二' },
  { key: 3, label: '周三' },
  { key: 4, label: '周四' },
  { key: 5, label: '周五' },
  { key: 6, label: '周六' },
  { key: 7, label: '周日' },
]

const periods = [
  { key: 1, label: '第1节' },
  { key: 2, label: '第2节' },
  { key: 3, label: '第3节' },
  { key: 4, label: '第4节' },
  { key: 5, label: '第5节' },
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
      setError((data && data.message) || '加载课表失败')
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
    <div className="min-h-screen">
      <div className="page-shell">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">课程表</h1>
          <p className="mt-1 text-sm text-slate-500">按周查看课程安排。</p>
        </header>

        {error ? (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <section className="card-surface p-5">
          <form className="flex flex-wrap items-end gap-3" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-700">周次</label>
              <input
                className="mt-2 w-32 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                type="number"
                min="1"
                value={week}
                onChange={(event) => setWeek(event.target.value)}
              />
            </div>
            <button
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              type="submit"
            >
              加载
            </button>
          </form>

          <div className="mt-6 overflow-auto rounded-lg border border-slate-200">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">节次</th>
                  {weekdays.map((day) => (
                    <th key={day.key} className="px-4 py-2 text-left font-medium">
                      {day.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {periods.map((period) => (
                  <tr key={period.key} className="align-top text-slate-700">
                    <td className="px-4 py-3 font-medium text-slate-800">{period.label}</td>
                    {weekdays.map((day) => {
                      const cellKey = `${day.key}_${period.key}`
                      const items = schedule[cellKey] || []
                      return (
                        <td key={cellKey} className="px-4 py-3">
                          {items.length === 0 ? (
                            <span className="text-xs text-slate-400">-</span>
                          ) : (
                            <div className="space-y-2">
                              {items.map((item, index) => (
                                <div key={`${cellKey}-${index}`} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1">
                                  <div className="text-xs font-semibold text-slate-800">{item.course_name}</div>
                                  <div className="text-[11px] text-slate-500">{item.location}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
