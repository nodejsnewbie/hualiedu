import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'secondary'
}

export default function ToolboxHome() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTasks = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/toolbox/api/tasks/?limit=10')
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

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-3">工具箱</h1>
          <p className="text-muted">提供常用的作业与文件处理工具。</p>
        </div>
      </div>

      <div className="row">
        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">PPT 转 PDF</h5>
              <p className="card-text">批量将目录中的 PPT 文件转换为 PDF。</p>
              <Link to="/toolbox/ppt-to-pdf" className="btn btn-primary">
                开始转换
              </Link>
            </div>
          </div>
        </div>

        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">任务管理</h5>
              <p className="card-text">查看并管理文件转换任务。</p>
              <Link to="/toolbox/tasks" className="btn btn-info">
                查看任务
              </Link>
            </div>
          </div>
        </div>

        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">作业成绩写入</h5>
              <p className="card-text">自动将作业成绩写入成绩登记册。</p>
              <Link to="/toolbox/assignment-grade-import" className="btn btn-success">
                立即写入
              </Link>
            </div>
          </div>
        </div>

        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">批量解压缩</h5>
              <p className="card-text">按压缩文件名自动创建目录并解压。</p>
              <Link to="/toolbox/batch-unzip" className="btn btn-warning">
                开始解压
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="row mt-3">
        <div className="col-12">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">最近任务</h5>
              <button type="button" className="btn btn-outline-secondary btn-sm" onClick={loadTasks}>
                刷新
              </button>
            </div>
            <div className="card-body">
              {error ? <div className="alert alert-danger">{error}</div> : null}
              {loading ? (
                <div className="alert alert-info">正在加载任务...</div>
              ) : tasks.length === 0 ? (
                <p className="text-muted text-center">暂无任务记录</p>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover align-middle">
                    <thead>
                      <tr>
                        <th>任务类型</th>
                        <th>状态</th>
                        <th>进度</th>
                        <th>创建时间</th>
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
                            <div className="progress" style={{ height: '16px' }}>
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
                          <td>{new Date(task.created_at).toLocaleString()}</td>
                          <td>
                            <Link to={`/toolbox/tasks/${task.id}`} className="btn btn-sm btn-outline-primary">
                              查看
                            </Link>
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
      </div>
    </div>
  )
}
