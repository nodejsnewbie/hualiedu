import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'secondary'
}

export default function ToolboxTaskList() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadTasks = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/toolbox/api/tasks/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载任务失败')
      }
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err.message || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const deleteTask = async (taskId) => {
    setMessage('')
    const confirmed = window.confirm('确定要删除该任务吗？')
    if (!confirmed) return
    const response = await apiFetch(`/toolbox/api/tasks/${taskId}/delete/`, { method: 'POST' })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setError((data && data.message) || '删除任务失败')
      return
    }
    setMessage('任务已删除')
    setTasks((prev) => prev.filter((task) => task.id !== taskId))
  }

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item">
                <Link to="/toolbox">工具箱</Link>
              </li>
              <li className="breadcrumb-item active">任务列表</li>
            </ol>
          </nav>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h1 className="mb-0">任务列表</h1>
            <Link to="/toolbox/ppt-to-pdf" className="btn btn-primary">
              新建任务
            </Link>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">全部转换任务</h5>
          <button className="btn btn-outline-secondary btn-sm" type="button" onClick={loadTasks}>
            刷新
          </button>
        </div>
        <div className="card-body">
          {error ? <div className="alert alert-danger">{error}</div> : null}
          {message ? <div className="alert alert-success">{message}</div> : null}
          {loading ? (
            <div className="alert alert-info">正在加载任务...</div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-4 text-muted">暂无任务记录</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead>
                  <tr>
                    <th>任务类型</th>
                    <th>状态</th>
                    <th>进度</th>
                    <th>文件统计</th>
                    <th>创建时间</th>
                    <th>更新时间</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => (
                    <tr key={task.id}>
                      <td>{task.task_type_display}</td>
                      <td>
                        <span className={`badge bg-${statusBadgeClass(task.status)}`}>
                          {task.status_display}
                        </span>
                      </td>
                      <td style={{ minWidth: '160px' }}>
                        <div className="progress" style={{ height: '18px' }}>
                          <div
                            className="progress-bar"
                            role="progressbar"
                            style={{ width: `${task.progress_percentage}%` }}
                            aria-valuenow={task.progress_percentage}
                            aria-valuemin="0"
                            aria-valuemax="100"
                          >
                            {task.progress_percentage}%
                          </div>
                        </div>
                      </td>
                      <td>
                        <small>
                          总数: {task.total_files}
                          <br />
                          成功: <span className="text-success">{task.success_files}</span>
                          <br />
                          失败: <span className="text-danger">{task.failed_files}</span>
                        </small>
                      </td>
                      <td>{new Date(task.created_at).toLocaleString()}</td>
                      <td>{new Date(task.updated_at).toLocaleString()}</td>
                      <td>
                        <div className="btn-group" role="group">
                          <Link to={`/toolbox/tasks/${task.id}`} className="btn btn-sm btn-outline-primary">
                            详情
                          </Link>
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => deleteTask(task.id)}
                          >
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
