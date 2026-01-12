import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const normalizePath = (value) => (value || '').replace(/\\/g, '/').replace(/\/+$/, '')

const mapTreeNodes = (items) =>
  (items || []).map((item) => ({
    id: item.id,
    text: item.text,
    hasChildren: Array.isArray(item.children) ? item.children.length > 0 : !!item.children,
  }))

export default function ToolboxAssignmentGradeImport() {
  const [repositories, setRepositories] = useState([])
  const [selectedRepoId, setSelectedRepoId] = useState('')
  const [selectedCourse, setSelectedCourse] = useState('')
  const [selectedClass, setSelectedClass] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [treeNodes, setTreeNodes] = useState([])
  const [treeChildren, setTreeChildren] = useState({})
  const [expandedIds, setExpandedIds] = useState(new Set())
  const [loadingIds, setLoadingIds] = useState(new Set())
  const [treeError, setTreeError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [currentPath, setCurrentPath] = useState('/')
  const [items, setItems] = useState([])
  const [dirError, setDirError] = useState('')
  const [dirLoading, setDirLoading] = useState(false)

  const currentRepo = useMemo(
    () => repositories.find((repo) => repo.id === selectedRepoId),
    [repositories, selectedRepoId],
  )
  const courses = currentRepo ? currentRepo.courses || [] : []
  const courseRoot = useMemo(() => {
    if (!currentRepo || !selectedCourse) return ''
    return normalizePath(`${currentRepo.path}\\${selectedCourse}`)
  }, [currentRepo, selectedCourse])
  const parentPath = useMemo(() => {
    if (!currentPath || currentPath === '/') return null
    const idx = currentPath.lastIndexOf('/')
    if (idx <= 0) return '/'
    return currentPath.slice(0, idx)
  }, [currentPath])

  useEffect(() => {
    const loadRepos = async () => {
      setLoading(true)
      try {
        const response = await apiFetch('/toolbox/api/repositories/')
        const data = await response.json().catch(() => null)
        if (!response.ok || (data && data.status !== 'success')) {
          throw new Error((data && data.message) || '加载仓库失败')
        }
        const repoList = data.repositories || []
        setRepositories(repoList)
        if (repoList.length) {
          setSelectedRepoId(repoList[0].id)
          setSelectedCourse(repoList[0].courses && repoList[0].courses[0] ? repoList[0].courses[0] : '')
        }
      } catch (err) {
        setError(err.message || '加载仓库失败')
      } finally {
        setLoading(false)
      }
    }

    loadRepos()
  }, [])

  useEffect(() => {
    if (!selectedRepoId) {
      setSelectedCourse('')
      setSelectedClass('')
      setTreeNodes([])
      return
    }
    if (!courses.includes(selectedCourse)) {
      setSelectedCourse(courses[0] || '')
      setSelectedClass('')
    }
  }, [selectedRepoId, courses, selectedCourse])

  const fetchTreeChildren = async (path) => {
    const response = await apiFetch(
      `/toolbox/api/class-directory-tree/?repo_id=${encodeURIComponent(
        selectedRepoId,
      )}&course=${encodeURIComponent(selectedCourse)}&path=${encodeURIComponent(path)}`,
    )
    const data = await response.json().catch(() => null)
    return mapTreeNodes(data && data.children)
  }

  const loadRootTree = async () => {
    setTreeError('')
    if (!selectedRepoId || !selectedCourse) {
      setTreeNodes([])
      return
    }
    try {
      const children = await fetchTreeChildren('')
      setTreeNodes(children)
      setTreeChildren({ '': children })
      setExpandedIds(new Set())
    } catch {
      setTreeError('加载课程目录失败')
      setTreeNodes([])
    }
  }

  useEffect(() => {
    loadRootTree()
  }, [selectedRepoId, selectedCourse])

  const toggleNode = async (node) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(node.id)) {
        next.delete(node.id)
      } else {
        next.add(node.id)
      }
      return next
    })

    if (!node.hasChildren || treeChildren[node.id]) return

    setLoadingIds((prev) => new Set(prev).add(node.id))
    try {
      const children = await fetchTreeChildren(node.id)
      setTreeChildren((prev) => ({ ...prev, [node.id]: children }))
    } finally {
      setLoadingIds((prev) => {
        const next = new Set(prev)
        next.delete(node.id)
        return next
      })
    }
  }

  useEffect(() => {
    if (modalOpen) {
      loadDirectory(currentPath || '/')
    }
  }, [modalOpen])

  const openModal = () => {
    if (courseRoot) {
      setCurrentPath(courseRoot)
    } else {
      setCurrentPath('/')
    }
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setItems([])
    setDirError('')
  }

  const loadDirectory = async (path) => {
    setDirLoading(true)
    setDirError('')
    try {
      const response = await apiFetch(`/toolbox/api/browse-directory/?path=${encodeURIComponent(path)}`)
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status !== 'success') {
        throw new Error((data && data.message) || '加载目录失败')
      }
      setCurrentPath(data.data.current_path)
      setItems(data.data.items || [])
    } catch (err) {
      setDirError(err.message || '加载目录失败')
    } finally {
      setDirLoading(false)
    }
  }

  const handleSelectDirectory = () => {
    const normalizedCurrent = normalizePath(currentPath)
    const normalizedRoot = normalizePath(courseRoot)
    if (!normalizedRoot || !normalizedCurrent.toLowerCase().startsWith(normalizedRoot.toLowerCase())) {
      setDirError('所选目录不在当前课程目录下')
      return
    }
    const relative = normalizedCurrent.slice(normalizedRoot.length).replace(/^\/+/, '')
    if (!relative) {
      setDirError('请选择课程下的班级目录')
      return
    }
    setSelectedClass(relative)
    closeModal()
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setResult(null)
    try {
      const response = await apiFetch('/toolbox/api/assignment-grade-import/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          selected_repo_id: selectedRepoId,
          selected_course: selectedCourse,
          class_directory: selectedClass,
        }),
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '写入失败')
      }
      setResult(data.result)
    } catch (err) {
      setError(err.message || '写入失败')
    }
  }

  const classDisplay = selectedClass
    ? `${selectedCourse ? `${selectedCourse}/` : ''}${selectedClass}`
    : '未选择'

  const renderTree = (nodes) => (
    <ul className="space-y-1">
      {nodes.map((node) => {
        const isExpanded = expandedIds.has(node.id)
        const isLoading = loadingIds.has(node.id)
        const children = treeChildren[node.id] || []
        const isSelected = selectedClass === node.id
        return (
          <li key={node.id}>
            <div
              className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition ${
                isSelected ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {node.hasChildren ? (
                <button
                  type="button"
                  className="h-5 w-5 rounded border border-slate-200 text-xs text-slate-500 hover:border-slate-300 hover:bg-white"
                  onClick={() => toggleNode(node)}
                >
                  {isExpanded ? '-' : '+'}
                </button>
              ) : (
                <span className="inline-block h-5 w-5" />
              )}
              <button
                type="button"
                className="flex-1 text-left"
                onClick={() => setSelectedClass(node.id)}
              >
                {node.text}
              </button>
            </div>
            {node.hasChildren && isExpanded ? (
              <div className="ml-6 border-l border-slate-200 pl-3">
                {isLoading ? (
                  <div className="py-2 text-xs text-slate-400">加载中...</div>
                ) : children.length ? (
                  renderTree(children)
                ) : (
                  <div className="py-2 text-xs text-slate-400">空目录</div>
                )}
              </div>
            ) : null}
          </li>
        )
      })}
    </ul>
  )

  return (
    <div className="min-h-screen">
      <div className="page-shell">
        <div className="mb-6">
          <nav className="text-xs text-slate-500">
            <Link to="/toolbox" className="hover:text-slate-700">
              工具箱
            </Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700">作业成绩写入</span>
          </nav>
          <h1 className="mt-3 text-2xl font-semibold text-slate-900">作业成绩写入</h1>
          <p className="mt-2 text-sm text-slate-500">
            选择班级目录后，系统会自动查找“第X次作业.xlsx”并写入成绩登记册。
          </p>
        </div>

        <section className="card-surface p-5">
          <h2 className="text-base font-semibold text-slate-800">配置参数</h2>
          {error ? (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}
          {loading ? (
            <div className="mt-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
              正在加载仓库...
            </div>
          ) : repositories.length === 0 ? (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              暂无可用仓库。
            </div>
          ) : (
            <form className="mt-4" onSubmit={handleSubmit}>
              <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700">选择仓库</label>
                    <select
                      className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                      value={selectedRepoId}
                      onChange={(event) => {
                        setSelectedRepoId(event.target.value)
                        setSelectedClass('')
                      }}
                    >
                      {repositories.map((repo) => (
                        <option key={repo.id} value={repo.id}>
                          {repo.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700">选择课程</label>
                    {courses.length ? (
                      <select
                        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                        value={selectedCourse}
                        onChange={(event) => {
                          setSelectedCourse(event.target.value)
                          setSelectedClass('')
                        }}
                      >
                        {courses.map((course) => (
                          <option key={course} value={course}>
                            {course}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                        该仓库下没有课程目录。
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700">已选择的班级目录</label>
                    <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                      {classDisplay}
                    </div>
                    <button
                      type="button"
                      className="mt-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      onClick={openModal}
                      disabled={!selectedCourse}
                    >
                      浏览目录
                    </button>
                  </div>
                  <button
                    type="submit"
                    className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                    disabled={!selectedClass}
                  >
                    开始写入
                  </button>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">课程目录</label>
                  <div className="mt-2 max-h-[420px] overflow-y-auto rounded-lg border border-slate-200 bg-white p-3">
                    {treeError ? (
                      <div className="text-xs text-rose-600">{treeError}</div>
                    ) : treeNodes.length === 0 ? (
                      <div className="text-xs text-slate-400">请选择仓库与课程</div>
                    ) : (
                      renderTree(treeNodes)
                    )}
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    展开课程目录后选择班级，仅显示目录结构。
                  </p>
                </div>
              </div>
            </form>
          )}
        </section>

        {result ? (
          <section className="mt-6 card-surface p-5">
            <h2 className="text-base font-semibold text-slate-800">执行结果</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-xs text-slate-500">仓库</p>
                <p className="text-sm font-semibold text-slate-800 break-all">{result.repository_name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">课程</p>
                <p className="text-sm font-semibold text-slate-800 break-all">{result.course_name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">班级目录</p>
                <p className="text-sm font-semibold text-slate-800 break-all">{result.class_directory}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">成绩登记册</p>
                <p className="text-sm font-semibold text-slate-800 break-all">{result.gradebook_file}</p>
              </div>
            </div>

            <div className="mt-4 text-sm text-slate-600">
              共找到 {result.total_files} 个作业文件，成功 {result.success_count} 个，失败 {result.error_count} 个。
            </div>

            {result.processed && result.processed.length ? (
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <table className="min-w-full text-xs">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">文件名</th>
                      <th className="px-3 py-2 text-left font-medium">作业次数</th>
                      <th className="px-3 py-2 text-left font-medium">写入列</th>
                      <th className="px-3 py-2 text-left font-medium">已更新学生</th>
                      <th className="px-3 py-2 text-left font-medium">登记册缺失</th>
                      <th className="px-3 py-2 text-left font-medium">作业缺失</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.processed.map((item) => (
                      <tr key={`${item.file_name}-${item.assignment_number}`} className="text-slate-700">
                        <td className="px-3 py-2 break-all">{item.file_name}</td>
                        <td className="px-3 py-2">第 {item.assignment_number} 次</td>
                        <td className="px-3 py-2">{item.assignment_column_letter}</td>
                        <td className="px-3 py-2">{item.updated_students} 人</td>
                        <td className="px-3 py-2">{item.missing_in_gradebook.length} 人</td>
                        <td className="px-3 py-2">{item.missing_in_assignment.length} 人</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {result.errors && result.errors.length ? (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-rose-600">
                  写入失败的文件（{result.errors.length}）
                </h3>
                <div className="mt-2 space-y-2">
                  {result.errors.map((item) => (
                    <div
                      key={`${item.file_name}-${item.assignment_number}`}
                      className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700"
                    >
                      <div className="font-semibold break-all">{item.file_name}</div>
                      <div className="text-rose-600">第 {item.assignment_number} 次作业</div>
                      <div className="mt-1 text-rose-500">{item.error}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-10">
          <div className="w-full max-w-3xl rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-800">选择目录</h3>
              <button
                type="button"
                className="text-sm text-slate-500 hover:text-slate-700"
                onClick={closeModal}
              >
                关闭
              </button>
            </div>
            <div className="px-6 py-5">
              <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                <span className="font-semibold text-slate-700">当前路径：</span>
                <span className="flex-1 break-all">{currentPath}</span>
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-white"
                  onClick={() => parentPath && loadDirectory(parentPath)}
                  disabled={!parentPath}
                >
                  上一级
                </button>
              </div>
              {dirError ? (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {dirError}
                </div>
              ) : null}
              {dirLoading ? (
                <div className="mt-4 text-center text-sm text-slate-500">正在加载...</div>
              ) : (
                <div className="mt-4 space-y-2">
                  {items.map((item) => (
                    <button
                      key={item.path}
                      type="button"
                      className="flex w-full items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      onClick={() => item.type === 'directory' && loadDirectory(item.path)}
                    >
                      <span>
                        {item.type === 'directory' ? '[DIR]' : '[FILE]'} {item.name}
                      </span>
                      <span className="text-xs text-slate-400">{item.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-slate-200 px-6 py-4">
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                onClick={closeModal}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800"
                onClick={handleSelectDirectory}
              >
                选择当前目录
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
