import { Link } from 'react-router-dom'

export default function Dashboard() {
  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">仪表盘</h4>
      </div>
      <div className="card-body">
        <p className="text-muted">
          使用下面入口访问评分、仓库与作业管理功能。
        </p>
        <div className="d-flex flex-wrap gap-2">
          <Link className="btn btn-primary" to="/grading">
            进入评分
          </Link>
          <Link className="btn btn-outline-primary" to="/assignments">
            作业管理
          </Link>
          <Link className="btn btn-outline-info" to="/batch-ai-score">
            批量AI评分
          </Link>
          <Link className="btn btn-outline-success" to="/batch-grade">
            批量登分
          </Link>
        </div>
      </div>
    </div>
  )
}
