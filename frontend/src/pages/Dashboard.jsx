import { Link } from 'react-router-dom'

export default function Dashboard() {
  return (
    <div className="card-surface p-6">
      <div className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-900">仪表盘</h1>
        <p className="text-sm text-slate-500">
          使用下面入口访问评分、作业管理与批量处理功能。
        </p>
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link className="btn-primary" to="/grading">
          进入评分
        </Link>
        <Link className="btn-soft" to="/assignments">
          作业管理
        </Link>
        <Link className="btn-soft" to="/batch-ai-score">
          批量 AI 评分
        </Link>
        <Link className="btn-soft" to="/batch-grade">
          批量登分
        </Link>
      </div>
    </div>
  )
}
