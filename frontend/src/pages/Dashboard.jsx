import { Link } from 'react-router-dom'

export default function Dashboard() {
  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Dashboard</h4>
      </div>
      <div className="card-body">
        <p className="text-muted">
          Use the links below to access grading, repositories, and assignment workflows.
        </p>
        <div className="d-flex flex-wrap gap-2">
          <Link className="btn btn-primary" to="/grading">
            Go to Grading
          </Link>
          <Link className="btn btn-outline-primary" to="/assignments">
            Manage Assignments
          </Link>
          <Link className="btn btn-outline-secondary" to="/repositories">
            Manage Repositories
          </Link>
          <Link className="btn btn-outline-info" to="/batch-ai-score">
            Batch AI Score
          </Link>
          <Link className="btn btn-outline-success" to="/batch-grade">
            Batch Grade
          </Link>
        </div>
      </div>
    </div>
  )
}
