import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const normalizePath = (value) => (value || '').replace(/\\/g, '/').replace(/\/+$/, '')

export default function ToolboxAssignmentGradeImport() {
  const [repositories, setRepositories] = useState([])
  const [selectedRepoId, setSelectedRepoId] = useState('')
  const [selectedCourse, setSelectedCourse] = useState('')
  const [selectedClass, setSelectedClass] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const treeRef = useRef(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [currentPath, setCurrentPath] = useState('/')
  const [items, setItems] = useState([])
  const [dirError, setDirError] = useState('')
  const [dirLoading, setDirLoading] = useState(false)

  const currentRepo = useMemo(
    () => repositories.find((repo) => repo.id === selectedRepoId),
    [repositories, selectedRepoId]
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
      return
    }
    if (!courses.includes(selectedCourse)) {
      setSelectedCourse(courses[0] || '')
      setSelectedClass('')
    }
  }, [selectedRepoId, courses, selectedCourse])

  useEffect(() => {
    const $ = window.$
    if (!treeRef.current || !$) return undefined

    const $tree = $(treeRef.current)
    if ($tree.data('jstree')) {
      $tree.jstree(true).destroy()
    }

    if (!selectedRepoId || !selectedCourse) {
      $tree.html('<div class="text-muted">请选择仓库与课程</div>')
      return undefined
    }

    $tree
      .empty()
      .jstree({
        core: {
          data: function (node, cb) {
            const path = node.id === '#' ? '' : node.id
            apiFetch(
              `/toolbox/api/class-directory-tree/?repo_id=${encodeURIComponent(
                selectedRepoId
              )}&course=${encodeURIComponent(selectedCourse)}&path=${encodeURIComponent(path)}`
            )
              .then((response) => response.json())
              .then((data) => cb(data.children || []))
              .catch(() => cb([]))
          },
          themes: { responsive: false },
        },
        plugins: ['types'],
        types: {
          default: { icon: 'bi bi-folder-fill text-secondary' },
        },
      })
      .on('select_node.jstree', function (_event, data) {
        setSelectedClass(data.node.id || '')
      })

    return () => {
      if ($tree.data('jstree')) {
        $tree.jstree(true).destroy()
      }
    }
  }, [selectedRepoId, selectedCourse])

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

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item">
                <Link to="/toolbox">工具箱</Link>
              </li>
              <li className="breadcrumb-item active">作业成绩写入</li>
            </ol>
          </nav>
          <h1 className="mb-3">作业成绩写入</h1>
          <p className="text-muted">
            选择班级目录后，系统会自动查找“第X次作业.xlsx”并写入成绩登记册。
          </p>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0">配置参数</h5>
        </div>
        <div className="card-body">
          {error ? <div className="alert alert-danger">{error}</div> : null}
          {loading ? (
            <div className="alert alert-info">正在加载仓库...</div>
          ) : repositories.length === 0 ? (
            <div className="alert alert-warning">暂无可用仓库</div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="row">
                <div className="col-md-4">
                  <div className="mb-3">
                    <label className="form-label">选择仓库</label>
                    <select
                      className="form-select"
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
                  <div className="mb-3">
                    <label className="form-label">选择课程</label>
                    {courses.length ? (
                      <select
                        className="form-select"
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
                      <div className="alert alert-warning mb-0">该仓库下没有课程目录</div>
                    )}
                  </div>
                  <div className="mb-3">
                    <label className="form-label">已选择的班级目录</label>
                    <div className="form-control-plaintext border rounded py-2 px-2 bg-light">
                      {classDisplay}
                    </div>
                    <button
                      type="button"
                      className="btn btn-outline-secondary btn-sm mt-2"
                      onClick={openModal}
                      disabled={!selectedCourse}
                    >
                      浏览目录
                    </button>
                  </div>
                  <button type="submit" className="btn btn-primary w-100" disabled={!selectedClass}>
                    开始写入
                  </button>
                </div>
                <div className="col-md-8">
                  <label className="form-label">课程目录</label>
                  <div
                    ref={treeRef}
                    className="border rounded p-2"
                    style={{ maxHeight: '420px', overflowY: 'auto', background: '#fff' }}
                  />
                  <small className="form-text text-muted">
                    展开课程目录后选择班级，系统只显示目录结构。
                  </small>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>

      {result ? (
        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">执行结果</h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-3 mb-3">
                <p className="mb-1 text-muted">仓库</p>
                <p className="h6 text-break">{result.repository_name}</p>
              </div>
              <div className="col-md-3 mb-3">
                <p className="mb-1 text-muted">课程</p>
                <p className="h6 text-break">{result.course_name}</p>
              </div>
              <div className="col-md-3 mb-3">
                <p className="mb-1 text-muted">班级目录</p>
                <p className="h6 text-break">{result.class_directory}</p>
              </div>
              <div className="col-md-3 mb-3">
                <p className="mb-1 text-muted">成绩登记册</p>
                <p className="h6 text-break">{result.gradebook_file}</p>
              </div>
            </div>

            <div className="mb-3">
              共找到 {result.total_files} 个作业文件，成功 {result.success_count} 个，失败{' '}
              {result.error_count} 个。
            </div>

            {result.processed && result.processed.length ? (
              <div className="table-responsive">
                <table className="table table-striped align-middle">
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>作业次数</th>
                      <th>写入列</th>
                      <th>已更新学生</th>
                      <th>登记册缺失</th>
                      <th>作业缺失</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.processed.map((item) => (
                      <tr key={`${item.file_name}-${item.assignment_number}`}>
                        <td className="text-break">{item.file_name}</td>
                        <td>第 {item.assignment_number} 次</td>
                        <td>{item.assignment_column_letter}</td>
                        <td>{item.updated_students} 人</td>
                        <td>{item.missing_in_gradebook.length} 人</td>
                        <td>{item.missing_in_assignment.length} 人</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {result.errors && result.errors.length ? (
              <div className="mt-4">
                <h6>写入失败的文件（{result.errors.length}）</h6>
                <div className="list-group">
                  {result.errors.map((item) => (
                    <div key={`${item.file_name}-${item.assignment_number}`} className="list-group-item list-group-item-warning">
                      <strong className="text-break">{item.file_name}</strong>
                      <span className="ms-2 text-muted">第 {item.assignment_number} 次作业</span>
                      <div className="small text-danger mt-1">{item.error}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {modalOpen ? (
        <>
          <div className="modal fade show d-block" tabIndex="-1" role="dialog">
            <div className="modal-dialog modal-lg" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">选择目录</h5>
                  <button type="button" className="btn-close" aria-label="Close" onClick={closeModal} />
                </div>
                <div className="modal-body">
                  <div className="input-group mb-3">
                    <span className="input-group-text">当前路径</span>
                    <input type="text" className="form-control" value={currentPath} readOnly />
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => parentPath && loadDirectory(parentPath)}
                      disabled={!parentPath}
                    >
                      上一级
                    </button>
                  </div>
                  {dirError ? <div className="alert alert-danger">{dirError}</div> : null}
                  {dirLoading ? (
                    <div className="text-center">正在加载...</div>
                  ) : (
                    <div className="list-group">
                      {items.map((item) => (
                        <button
                          key={item.path}
                          type="button"
                          className="list-group-item list-group-item-action"
                          onClick={() => item.type === 'directory' && loadDirectory(item.path)}
                        >
                          {item.type === 'directory' ? '[DIR] ' : '[FILE] '}
                          {item.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={closeModal}>
                    取消
                  </button>
                  <button type="button" className="btn btn-primary" onClick={handleSelectDirectory}>
                    选择当前目录
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show" />
        </>
      ) : null}
    </div>
  )
}
