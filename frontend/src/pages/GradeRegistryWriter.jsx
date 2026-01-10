import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'
import { loadExternalScript } from '../utils/loadExternalScript.js'
import { API_BASE_URL } from '../api/config.js'

const staticUrl = (path) => `${API_BASE_URL}${path}`

export default function GradeRegistryWriter() {
  const [repositories, setRepositories] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    const loadRepos = async () => {
      const response = await apiFetch('/grading/api/repositories/')
      const data = await response.json().catch(() => null)
      if (!mounted) return
      if (!response.ok || (data && data.status !== 'success')) {
        setError((data && data.message) || 'Failed to load repositories')
        return
      }
      setRepositories(data.repositories || [])
    }

    const setup = async () => {
      await loadRepos()
      await loadExternalScript(staticUrl('/static/grading/js/grade_registry_writer.js'))
    }

    setup().catch((err) => setError(err.message || 'Failed to load page'))

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="container-fluid mt-4">
      {error ? <div className="alert alert-danger">{error}</div> : null}
      <div className="row">
        <div className="col-12">
          <h4 className="mb-3">Grade Registry Writer</h4>
          <p className="text-muted">
            Select a repository and class directory to write grades into the registry file.
          </p>
        </div>
      </div>
      <div className="row">
        <div className="col-md-4">
          <div className="card">
            <div className="card-header">
              <h6 className="mb-0">Select Directory</h6>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <label htmlFor="repository-select" className="form-label">
                  Repository
                </label>
                <select className="form-select" id="repository-select">
                  <option value="">-- Select repository --</option>
                  {repositories.map((repo) => (
                    <option key={repo.id} value={repo.id}>
                      {repo.name}
                    </option>
                  ))}
                </select>
              </div>
              <div
                id="directory-tree"
                className="border rounded p-2"
                style={{ minHeight: '400px', maxHeight: '600px', overflowY: 'auto' }}
              >
                <p className="text-muted text-center mt-5">Select a repository first</p>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-8">
          <div className="card mb-3" id="selected-dir-card" style={{ display: 'none' }}>
            <div className="card-header bg-primary text-white">
              <h6 className="mb-0">Selected Directory</h6>
            </div>
            <div className="card-body">
              <p className="mb-2">
                <strong>Directory:</strong> <span id="selected-dir-path" />
              </p>
              <p className="mb-0">
                <strong>Registry file:</strong>{' '}
                <span id="registry-file-name" className="text-success">
                  Checking...
                </span>
              </p>
              <button type="button" className="btn btn-success mt-3" id="start-write-btn" disabled>
                Start Write
              </button>
            </div>
          </div>

          <div className="card mb-3" id="progress-card" style={{ display: 'none' }}>
            <div className="card-header">
              <h6 className="mb-0">Progress</h6>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-1">
                  <span id="progress-text">Preparing...</span>
                  <span id="progress-percentage">0%</span>
                </div>
                <div className="progress" style={{ height: '25px' }}>
                  <div
                    className="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    id="progress-bar"
                    style={{ width: '0%' }}
                    aria-valuenow="0"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  />
                </div>
              </div>
              <div id="current-file-info" className="text-muted small">
                <span id="current-file-name">-</span>
              </div>
            </div>
          </div>

          <div className="card" id="result-card" style={{ display: 'none' }}>
            <div className="card-header" id="result-header">
              <h6 className="mb-0">Result</h6>
            </div>
            <div className="card-body">
              <div className="row mb-4" id="result-summary">
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-primary" id="total-files">
                      0
                    </h3>
                    <small className="text-muted">Total</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-success" id="success-count">
                      0
                    </h3>
                    <small className="text-muted">Success</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-danger" id="failed-count">
                      0
                    </h3>
                    <small className="text-muted">Failed</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-warning" id="skipped-count">
                      0
                    </h3>
                    <small className="text-muted">Skipped</small>
                  </div>
                </div>
              </div>

              <div id="result-details">
                <div id="success-section" style={{ display: 'none' }}>
                  <h6 className="text-success">
                    Success (<span id="success-count-text">0</span>)
                  </h6>
                  <div className="table-responsive mb-4">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Student</th>
                          <th>Homework</th>
                          <th>Grade</th>
                        </tr>
                      </thead>
                      <tbody id="success-list" />
                    </table>
                  </div>
                </div>

                <div id="failed-section" style={{ display: 'none' }}>
                  <h6 className="text-danger">
                    Failed (<span id="failed-count-text">0</span>)
                  </h6>
                  <div className="table-responsive mb-4">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody id="failed-list" />
                    </table>
                  </div>
                </div>

                <div id="skipped-section" style={{ display: 'none' }}>
                  <h6 className="text-warning">
                    Skipped (<span id="skipped-count-text">0</span>)
                  </h6>
                  <div className="table-responsive">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Reason</th>
                        </tr>
                      </thead>
                      <tbody id="skipped-list" />
                    </table>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <button type="button" className="btn btn-primary" id="new-write-btn">
                  New Write
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
