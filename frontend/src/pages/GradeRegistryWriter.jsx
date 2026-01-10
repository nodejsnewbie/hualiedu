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
        setError((data && data.message) || '加载仓库失败')
        return
      }
      setRepositories(data.repositories || [])
    }

    const setup = async () => {
      await loadRepos()
      await loadExternalScript(staticUrl('/static/grading/js/grade_registry_writer.js'))
    }

    setup().catch((err) => setError(err.message || '页面加载失败'))

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="container-fluid mt-4">
      {error ? <div className="alert alert-danger">{error}</div> : null}
      <div className="row">
        <div className="col-12">
          <h4 className="mb-3">成绩登记册写入</h4>
          <p className="text-muted">
            选择仓库和班级目录，将成绩写入登记册文件。
          </p>
        </div>
      </div>
      <div className="row">
        <div className="col-md-4">
          <div className="card">
            <div className="card-header">
              <h6 className="mb-0">选择目录</h6>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <label htmlFor="repository-select" className="form-label">
                  仓库
                </label>
                <select className="form-select" id="repository-select">
                  <option value="">-- 请选择仓库 --</option>
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
                <p className="text-muted text-center mt-5">请先选择仓库</p>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-8">
          <div className="card mb-3" id="selected-dir-card" style={{ display: 'none' }}>
            <div className="card-header bg-primary text-white">
              <h6 className="mb-0">已选目录</h6>
            </div>
            <div className="card-body">
              <p className="mb-2">
                <strong>目录：</strong> <span id="selected-dir-path" />
              </p>
              <p className="mb-0">
                <strong>登记册文件：</strong>{' '}
                <span id="registry-file-name" className="text-success">
                  检查中...
                </span>
              </p>
              <button type="button" className="btn btn-success mt-3" id="start-write-btn" disabled>
                开始写入
              </button>
            </div>
          </div>

          <div className="card mb-3" id="progress-card" style={{ display: 'none' }}>
            <div className="card-header">
              <h6 className="mb-0">进度</h6>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-1">
                  <span id="progress-text">准备中...</span>
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
              <h6 className="mb-0">结果</h6>
            </div>
            <div className="card-body">
              <div className="row mb-4" id="result-summary">
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-primary" id="total-files">
                      0
                    </h3>
                    <small className="text-muted">总计</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-success" id="success-count">
                      0
                    </h3>
                    <small className="text-muted">成功</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-danger" id="failed-count">
                      0
                    </h3>
                    <small className="text-muted">失败</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center p-3 border rounded">
                    <h3 className="mb-0 text-warning" id="skipped-count">
                      0
                    </h3>
                    <small className="text-muted">跳过</small>
                  </div>
                </div>
              </div>

              <div id="result-details">
                <div id="success-section" style={{ display: 'none' }}>
                  <h6 className="text-success">
                    成功（<span id="success-count-text">0</span>）
                  </h6>
                  <div className="table-responsive mb-4">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>文件</th>
                          <th>学生</th>
                          <th>作业</th>
                          <th>成绩</th>
                        </tr>
                      </thead>
                      <tbody id="success-list" />
                    </table>
                  </div>
                </div>

                <div id="failed-section" style={{ display: 'none' }}>
                  <h6 className="text-danger">
                    失败（<span id="failed-count-text">0</span>）
                  </h6>
                  <div className="table-responsive mb-4">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>文件</th>
                          <th>错误</th>
                        </tr>
                      </thead>
                      <tbody id="failed-list" />
                    </table>
                  </div>
                </div>

                <div id="skipped-section" style={{ display: 'none' }}>
                  <h6 className="text-warning">
                    跳过（<span id="skipped-count-text">0</span>）
                  </h6>
                  <div className="table-responsive">
                    <table className="table table-sm table-hover">
                      <thead>
                        <tr>
                          <th>文件</th>
                          <th>原因</th>
                        </tr>
                      </thead>
                      <tbody id="skipped-list" />
                    </table>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <button type="button" className="btn btn-primary" id="new-write-btn">
                  新的写入
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
