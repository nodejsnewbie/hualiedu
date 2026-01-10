import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function BatchGrade() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState('')
  const [result, setResult] = useState('')

  const loadRepos = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/grading/batch-grade-registration/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || 'Failed to load repositories')
      }
      setRepos(data.repositories || [])
    } catch (err) {
      setError(err.message || 'Failed to load repositories')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  const startBatch = async () => {
    setResult('')
    const response = await apiFetch('/grading/batch-grade-registration/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ repository: selected }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setResult((data && data.message) || 'Batch grading failed')
      return
    }
    setResult(data.message || 'Batch grading completed')
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h4 className="mb-0">Batch Grade</h4>
        <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadRepos}>
          Refresh
        </button>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? (
          <div className="alert alert-info">Loading repositories...</div>
        ) : repos.length === 0 ? (
          <div className="alert alert-warning">No repositories found.</div>
        ) : (
          <div className="row g-3">
            {repos.map((repo) => (
              <div key={repo.name} className="col-md-6 col-lg-4">
                <button
                  className={`btn w-100 text-start ${selected === repo.name ? 'btn-primary' : 'btn-outline-primary'}`}
                  type="button"
                  onClick={() => setSelected(repo.name)}
                >
                  <div className="fw-semibold">{repo.name}</div>
                  <div className="small">Excel files: {repo.excel_count}</div>
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="mt-3">
          <button className="btn btn-success" type="button" onClick={startBatch} disabled={!selected}>
            Start Batch Grade
          </button>
        </div>
        {result ? <div className="alert alert-info mt-3">{result}</div> : null}
      </div>
    </div>
  )
}
