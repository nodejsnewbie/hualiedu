import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiFetch } from '../api/client.js'

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'secondary'
}

const statusLabel = (status) => {
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'processing') return '处理中'
  if (status === 'pending') return '等待中'
  return status || ''
}

export default function ToolboxTaskDetail() {
  const { taskId } = useParams()
  const [task, setTask] = useState(null)
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  const loadDetail = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch(`/toolbox/api/tasks/${taskId}/`)
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '加载任务失败')
      }
      setTask(data.task)
      setLogs(data.logs || [])
    } catch (err) {
      setError(err.message || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDetail()
  }, [taskId])

  useEffect(() => {
    if (!task || task.status !== 'processing') return undefined
    const interval = setInterval(async () => {
      const response = await apiFetch(`/toolbox/api/tasks/${taskId}/status/`)
      const data = await response.json().catch(() => null)
      if (response.ok && data && data.status === 'success') {
        setTask((prev) => ({ ...(prev || {}), ...data.data }))
        if (data.data.status !== 'processing') {
          clearInterval(interval)
          loadDetail()
        }
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [task, taskId])

  const deleteTask = async () => {
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
  }

  if (loading) {
    return (
      <div className="container mt-4">
        <div className="alert alert-info">正在加载任务...</div>
      </div>
    )
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
              <li className="breadcrumb-item">
                <Link to="/toolbox/tasks">任务列表</Link>
              </li>
              <li className="breadcrumb-item active">任务详情</li>
            </ol>
          </nav>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h1 className="mb-0">任务详情</h1>
            <div>
              <Link to="/toolbox/tasks" className="btn btn-outline-secondary me-2">
                返回列表
              </Link>
              <button type="button" className="btn btn-outline-danger" onClick={deleteTask}>
                删除任务
              </button>
            </div>
          </div>
        </div>
      </div>

      {error ? <div className="alert alert-danger">{error}</div> : null}
      {message ? <div className="alert alert-success">{message}</div> : null}
      {!task ? (
        <div className="alert alert-warning">任务不存在</div>
      ) : (
        <div className="row">
          <div className="col-md-8">
            <div className="card mb-4">
              <div className="card-header">
                <h5 className="mb-0">任务信息</h5>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-6">
                    <p>
                      <strong>任务类型：</strong> {task.task_type_display}
                    </p>
                    <p>
                      <strong>任务状态：</strong>{' '}
                      <span className={`badge bg-${statusBadgeClass(task.status)}`}>
                        {statusLabel(task.status)}
                      </span>
                    </p>
                    <p>
                      <strong>创建时间：</strong>{' '}
                      {new Date(task.created_at).toLocaleString()}
                    </p>
                    <p>
                      <strong>更新时间：</strong>{' '}
                      {new Date(task.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="col-md-6">
                    <p>
                      <strong>源目录：</strong> <code>{task.source_directory}</code>
                    </p>
                    <p>
                      <strong>输出目录：</strong> <code>{task.output_directory}</code>
                    </p>
                    <p>
                      <strong>总文件数：</strong> {task.total_files}
                    </p>
                    <p>
                      <strong>已处理：</strong> {task.processed_files}
                    </p>
                  </div>
                </div>
                {task.error_message ? (
                  <div className="alert alert-danger mt-3">{task.error_message}</div>
                ) : null}
              </div>
            </div>

            <div className="card mb-4">
              <div className="card-header">
                <h5 className="mb-0">转换进度</h5>
              </div>
              <div className="card-body">
                <div className="row text-center">
                  <div className="col-md-4">
                    <div className="border rounded p-3">
                      <h3 className="text-primary">{task.total_files}</h3>
                      <p className="mb-0">总文件数</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="border rounded p-3">
                      <h3 className="text-success">{task.success_files}</h3>
                      <p className="mb-0">成功转换</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="border rounded p-3">
                      <h3 className="text-danger">{task.failed_files}</h3>
                      <p className="mb-0">转换失败</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="d-flex justify-content-between mb-2">
                    <span>总体进度</span>
                    <span>{task.progress_percentage}%</span>
                  </div>
                  <div className="progress" style={{ height: '24px' }}>
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
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">转换日志</h5>
              </div>
              <div className="card-body">
                {logs.length === 0 ? (
                  <p className="text-muted text-center">暂无转换日志</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>文件名</th>
                          <th>状态</th>
                          <th>时间</th>
                          <th>错误信息</th>
                        </tr>
                      </thead>
                      <tbody>
                        {logs.map((log) => (
                          <tr key={log.id}>
                            <td>{log.file_name}</td>
                            <td>
                              <span className={`badge bg-${statusBadgeClass(log.status)}`}>
                                {log.status_display}
                              </span>
                            </td>
                            <td>{new Date(log.created_at).toLocaleTimeString()}</td>
                            <td>{log.error_message || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className="card mb-4">
              <div className="card-header">
                <h5 className="mb-0">实时状态</h5>
              </div>
              <div className="card-body">
                <p>
                  <strong>当前状态：</strong>{' '}
                  <span className={`badge bg-${statusBadgeClass(task.status)}`}>
                    {statusLabel(task.status)}
                  </span>
                </p>
                <p>
                  <strong>进度：</strong> {task.progress_percentage}%
                </p>
                <p>
                  <strong>已处理：</strong> {task.processed_files}/{task.total_files}
                </p>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">操作指南</h5>
              </div>
              <div className="card-body">
                <ul className="list-unstyled mb-0">
                  <li className="mb-2">转换完成后 PDF 会保存在输出目录</li>
                  <li className="mb-2">任务处理中会自动刷新状态</li>
                  <li className="mb-2">如失败请确认 LibreOffice 安装情况</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
