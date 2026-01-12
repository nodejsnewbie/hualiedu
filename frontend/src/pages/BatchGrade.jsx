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
    <div className="min-h-screen">
      <div className="page-shell max-w-5xl flex flex-col gap-6">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">批量登分</h1>
            <p className="mt-1 text-sm text-slate-500">选择仓库后进行批量登分。</p>
          </div>
          <button
            type="button"
            onClick={loadRepos}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          >
            刷新仓库
          </button>
        </header>

        <section className="card-surface p-6">
          {error ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          {loading ? (
            <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
              正在加载仓库...
            </div>
          ) : repos.length === 0 ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              暂无仓库。
            </div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {repos.map((repo) => (
                <button
                  key={repo.name}
                  type="button"
                  onClick={() => setSelected(repo.name)}
                  className={`rounded-xl border px-4 py-3 text-left transition ${
                    selected === repo.name
                      ? 'border-slate-900 bg-slate-900 text-white'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="text-sm font-semibold">{repo.name}</div>
                  <div
                    className={`mt-1 text-xs ${
                      selected === repo.name ? 'text-slate-200' : 'text-slate-500'
                    }`}
                  >
                    Excel 文件数：{repo.excel_count}
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="mt-6 flex items-center gap-3">
            <button
              type="button"
              onClick={startBatch}
              disabled={!selected}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              开始批量登分
            </button>
            {selected ? (
              <span className="text-xs text-slate-500">已选择：{selected}</span>
            ) : null}
          </div>

          {result ? (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {result}
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
