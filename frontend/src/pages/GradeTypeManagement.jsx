import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function GradeTypeManagement() {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadConfigs = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/grading/api/grade-types/')
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error((data && data.message) || 'Failed to load grade types')
      }
      setConfigs(data.configs || [])
    } catch (err) {
      setError(err.message || 'Failed to load grade types')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfigs()
  }, [])

  const changeGradeType = async (classIdentifier) => {
    const newGradeType = window.prompt(
      'Enter new grade type: letter, text, or numeric',
    )
    if (!newGradeType) {
      return
    }
    if (
      !window.confirm(
        `Change grade type for ${classIdentifier} to ${newGradeType}?`,
      )
    ) {
      return
    }

    const response = await apiFetch('/grading/change-grade-type/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        class_identifier: classIdentifier,
        new_grade_type: newGradeType,
      }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || 'Failed to update grade type')
      return
    }
    window.alert(data.message || 'Updated')
    loadConfigs()
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Grade Type Management</h4>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? (
          <div className="alert alert-info">Loading...</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Class Identifier</th>
                  <th>Grade Type</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {configs.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center">
                      No grade type configs.
                    </td>
                  </tr>
                ) : (
                  configs.map((config) => (
                    <tr key={config.class_identifier}>
                      <td>{config.class_identifier}</td>
                      <td>{config.grade_type_display}</td>
                      <td>
                        {config.is_locked ? (
                          <span className="badge bg-success">Locked</span>
                        ) : (
                          <span className="badge bg-warning text-dark">Unlocked</span>
                        )}
                      </td>
                      <td>
                        {config.is_locked ? (
                          <button className="btn btn-sm btn-secondary" disabled>
                            Locked
                          </button>
                        ) : (
                          <button
                            className="btn btn-sm btn-primary"
                            type="button"
                            onClick={() => changeGradeType(config.class_identifier)}
                          >
                            Change
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
