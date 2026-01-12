import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'

const mapTreeNodes = (nodes) =>
  (nodes || []).map((node) => ({
    id: node.id,
    text: node.text,
    type: node.type || 'folder',
    children: mapTreeNodes(node.children),
  }))

export default function GradeRegistryWriter() {
  const [repositories, setRepositories] = useState([])
  const [selectedRepoId, setSelectedRepoId] = useState('')
  const [treeData, setTreeData] = useState([])
  const [expandedIds, setExpandedIds] = useState(new Set())
  const [selectedDir, setSelectedDir] = useState('')
  const [registryFile, setRegistryFile] = useState('')
  const [registryFound, setRegistryFound] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [writing, setWriting] = useState(false)
  const [progress, setProgress] = useState({ pct: 0, text: '准备中...', currentFile: '-' })

  const summary = result && result.summary ? result.summary : null
  const details = result && result.details ? result.details : null

  const loadRepos = async () => {
    setError('')
    const response = await apiFetch('/grading/api/repositories/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '加载仓库失败')
      return
    }
    setRepositories(data.repositories || [])
  }

  const loadTree = async (repoId) => {
    if (!repoId) {
      setTreeData([])
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch(`/grading/get_directory_tree/?repo_id=${repoId}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载目录树失败')
      }
      setTreeData(mapTreeNodes(data.tree_data || []))
      setExpandedIds(new Set())
    } catch (err) {
      setError(err.message || '加载目录树失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  useEffect(() => {
    if (!selectedRepoId) return
    loadTree(selectedRepoId)
  }, [selectedRepoId])

  const handleSelectDir = async (nodeId) => {
    setSelectedDir(nodeId)
    setRegistryFile('检查中...')
    setRegistryFound(false)
    setResult(null)
    try {
      const response = await apiFetch('/grading/check_grade_registry/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ directory: nodeId, repo_id: selectedRepoId }),
      })
      const data = await response.json().catch(() => null)
      if (response.ok && data && data.found) {
        setRegistryFound(true)
        setRegistryFile(data.file_name)
      } else {
        setRegistryFound(false)
        setRegistryFile('未找到成绩登记册')
      }
    } catch (err) {
      setRegistryFound(false)
      setRegistryFile(err.message || '检查失败')
    }
  }

  const startWrite = async () => {
    if (!selectedRepoId || !selectedDir) {
      window.alert('请先选择仓库和目录')
      return
    }
    setWriting(true)
    setProgress({ pct: 10, text: '准备中...', currentFile: '-' })
    setResult(null)
    try {
      const response = await apiFetch('/grading/grade-registry-writer/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ class_directory: selectedDir, repository_id: selectedRepoId }),
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.error) || '写入失败')
      }
      setProgress({ pct: 100, text: '完成', currentFile: '-' })
      setResult(data.data)
    } catch (err) {
      setError(err.message || '写入失败')
    } finally {
      setWriting(false)
    }
  }

  const resetSelection = () => {
    setSelectedDir('')
    setRegistryFile('')
    setRegistryFound(false)
    setResult(null)
  }

  const toggleNode = (nodeId) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  const renderTree = (nodes, level = 0) => (
    <ul className={level === 0 ? 'space-y-1' : 'space-y-1 pl-4 border-l border-slate-200'}>
      {nodes.map((node) => {
        const hasChildren = node.children && node.children.length > 0
        const isExpanded = expandedIds.has(node.id)
        const isSelected = selectedDir === node.id
        const isFolder = node.type === 'folder'
        return (
          <li key={node.id}>
            <div
              className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition ${
                isSelected ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {hasChildren ? (
                <button
                  type="button"
                  className="h-5 w-5 rounded border border-slate-200 text-xs text-slate-500 hover:border-slate-300 hover:bg-white"
                  onClick={() => toggleNode(node.id)}
                >
                  {isExpanded ? '-' : '+'}
                </button>
              ) : (
                <span className="inline-block h-5 w-5" />
              )}
              <button
                type="button"
                className="flex-1 text-left"
                onClick={() => {
                  if (isFolder) handleSelectDir(node.id)
                }}
              >
                {node.text}
              </button>
            </div>
            {hasChildren && isExpanded ? renderTree(node.children, level + 1) : null}
          </li>
        )
      })}
    </ul>
  )

  const resultSummaryClass = useMemo(() => {
    if (!summary) return 'bg-slate-100'
    return summary.failed_count > 0 ? 'bg-amber-50' : 'bg-emerald-50'
  }, [summary])

  return (
    <div className="min-h-screen">
      <div className="page-shell">
        {error ? (
          <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">成绩登记册写入</h1>
          <p className="mt-1 text-sm text-slate-500">
            选择仓库和班级目录，将成绩写入登记册文件。
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <section className="card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">选择目录</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label htmlFor="repository-select" className="text-sm font-medium text-slate-700">
                  仓库
                </label>
                <select
                  className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                  id="repository-select"
                  value={selectedRepoId}
                  onChange={(event) => {
                    setSelectedRepoId(event.target.value)
                    resetSelection()
                  }}
                >
                  <option value="">-- 请选择仓库 --</option>
                  {repositories.map((repo) => (
                    <option key={repo.id} value={repo.id}>
                      {repo.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="min-h-[360px] rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-500">
                {!selectedRepoId ? (
                  <p className="mt-16 text-center">请先选择仓库</p>
                ) : loading ? (
                  <p className="mt-16 text-center">加载中...</p>
                ) : treeData.length === 0 ? (
                  <p className="mt-16 text-center">暂无目录数据</p>
                ) : (
                  renderTree(treeData)
                )}
              </div>
            </div>
          </section>

          <section className="space-y-4">
            {selectedDir ? (
              <div className="card-surface p-5" id="selected-dir-card">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-slate-800">已选目录</h2>
                  <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    已就绪
                  </span>
                </div>
                <div className="mt-3 text-sm text-slate-700">
                  <p className="mb-2">
                    <span className="font-semibold text-slate-600">目录：</span>
                    <span className="break-all">{selectedDir}</span>
                  </p>
                  <p className="mb-0">
                    <span className="font-semibold text-slate-600">登记册文件：</span>
                    <span className={registryFound ? 'text-emerald-600' : 'text-rose-600'}>
                      {registryFile || '检查中...'}
                    </span>
                  </p>
                </div>
                <button
                  type="button"
                  className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500"
                  onClick={startWrite}
                  disabled={!registryFound || writing}
                >
                  {writing ? '处理中...' : '开始写入'}
                </button>
              </div>
            ) : null}

            {writing ? (
              <div className="card-surface p-5" id="progress-card">
                <h2 className="text-base font-semibold text-slate-800">进度</h2>
                <div className="mt-3">
                  <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
                    <span>{progress.text}</span>
                    <span>{progress.pct}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-900 transition-all"
                      style={{ width: `${progress.pct}%` }}
                    />
                  </div>
                  <div className="mt-3 text-xs text-slate-500">{progress.currentFile}</div>
                </div>
              </div>
            ) : null}

            {result ? (
              <div className="card-surface p-5" id="result-card">
                <div className={`rounded-lg px-3 py-2 ${resultSummaryClass}`} id="result-header">
                  <h2 className="text-base font-semibold text-slate-800">结果</h2>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" id="result-summary">
                  <div className="rounded-lg border border-slate-200 px-4 py-3 text-center">
                    <div className="text-2xl font-semibold text-slate-900" id="total-files">
                      {summary?.total_files || 0}
                    </div>
                    <div className="text-xs text-slate-500">总计</div>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-4 py-3 text-center">
                    <div className="text-2xl font-semibold text-emerald-600" id="success-count">
                      {summary?.success_count || 0}
                    </div>
                    <div className="text-xs text-slate-500">成功</div>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-4 py-3 text-center">
                    <div className="text-2xl font-semibold text-rose-600" id="failed-count">
                      {summary?.failed_count || 0}
                    </div>
                    <div className="text-xs text-slate-500">失败</div>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-4 py-3 text-center">
                    <div className="text-2xl font-semibold text-amber-500" id="skipped-count">
                      {summary?.skipped_count || 0}
                    </div>
                    <div className="text-xs text-slate-500">跳过</div>
                  </div>
                </div>

                <div className="mt-4 space-y-4" id="result-details">
                  {details?.success && details.success.length > 0 ? (
                    <div id="success-section">
                      <h3 className="text-sm font-semibold text-emerald-600">
                        成功（{details.success.length}）
                      </h3>
                      <div className="mt-2 overflow-hidden rounded-lg border border-slate-200">
                        <table className="min-w-full text-xs">
                          <thead className="bg-slate-100 text-slate-600">
                            <tr>
                              <th className="px-3 py-2 text-left font-medium">文件</th>
                              <th className="px-3 py-2 text-left font-medium">学生</th>
                              <th className="px-3 py-2 text-left font-medium">作业</th>
                              <th className="px-3 py-2 text-left font-medium">成绩</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100" id="success-list">
                            {details.success.map((item, index) => (
                              <tr key={`${item.file}-${index}`} className="text-slate-700">
                                <td className="px-3 py-2">{item.file || '-'}</td>
                                <td className="px-3 py-2">{item.student || '-'}</td>
                                <td className="px-3 py-2">{item.homework || '-'}</td>
                                <td className="px-3 py-2">
                                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                                    {item.grade || '-'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : null}

                  {details?.failed && details.failed.length > 0 ? (
                    <div id="failed-section">
                      <h3 className="text-sm font-semibold text-rose-600">
                        失败（{details.failed.length}）
                      </h3>
                      <div className="mt-2 overflow-hidden rounded-lg border border-slate-200">
                        <table className="min-w-full text-xs">
                          <thead className="bg-slate-100 text-slate-600">
                            <tr>
                              <th className="px-3 py-2 text-left font-medium">文件</th>
                              <th className="px-3 py-2 text-left font-medium">错误</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100" id="failed-list">
                            {details.failed.map((item, index) => (
                              <tr key={`${item.file}-${index}`} className="text-slate-700">
                                <td className="px-3 py-2">{item.file || '-'}</td>
                                <td className="px-3 py-2 text-rose-600">{item.error || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : null}

                  {details?.skipped && details.skipped.length > 0 ? (
                    <div id="skipped-section">
                      <h3 className="text-sm font-semibold text-amber-600">
                        跳过（{details.skipped.length}）
                      </h3>
                      <div className="mt-2 overflow-hidden rounded-lg border border-slate-200">
                        <table className="min-w-full text-xs">
                          <thead className="bg-slate-100 text-slate-600">
                            <tr>
                              <th className="px-3 py-2 text-left font-medium">文件</th>
                              <th className="px-3 py-2 text-left font-medium">原因</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100" id="skipped-list">
                            {details.skipped.map((item, index) => (
                              <tr key={`${item.file}-${index}`} className="text-slate-700">
                                <td className="px-3 py-2">{item.file || '-'}</td>
                                <td className="px-3 py-2 text-amber-600">{item.reason || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="mt-4">
                  <button
                    type="button"
                    className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                    onClick={resetSelection}
                    id="new-write-btn"
                  >
                    新的写入
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </div>
  )
}
