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
        throw new Error((data && data.message) || '加载仓库失败')
      }
      setRepos(data.repositories || [])
    } catch (err) {
      setError(err.message || '加载仓库失败')
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
      setResult((data && data.message) || '批量登分失败')
      return
    }
    setResult(data.message || '批量登分完成')
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h4 className="mb-0">批量登分</h4>
        <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadRepos}>
          刷新
        </button>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? (
          <div className="alert alert-info">正在加载仓库...</div>
        ) : repos.length === 0 ? (
          <div className="alert alert-warning">暂无仓库。</div>
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
                  <div className="small">Excel 文件数：{repo.excel_count}</div>
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="mt-3">
          <button className="btn btn-success" type="button" onClick={startBatch} disabled={!selected}>
            开始批量登分
          </button>
        </div>
        {result ? <div className="alert alert-info mt-3">{result}</div> : null}
      </div>
    </div>
  )
}
