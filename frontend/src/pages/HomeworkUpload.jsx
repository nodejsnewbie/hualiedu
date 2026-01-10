import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function HomeworkUpload() {
  const [homeworks, setHomeworks] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const loadHomeworks = async () => {
    setLoading(true)
    setMessage('')
    const response = await apiFetch('/grading/api/student/homework-list/')
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && !data.success)) {
      setMessage((data && data.message) || '加载作业列表失败')
      setLoading(false)
      return
    }
    setHomeworks(data.homeworks || [])
    setLoading(false)
  }

  useEffect(() => {
    loadHomeworks()
  }, [])

  const uploadFile = async (homeworkId, file) => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('homework_id', homeworkId)
    const response = await apiFetch('/grading/api/student/upload/', {
      method: 'POST',
      body: formData,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && !data.success)) {
      setMessage((data && data.message) || '上传失败')
      return
    }
    setMessage(data.message || '上传成功')
    loadHomeworks()
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">作业上传</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}
        {loading ? <div className="alert alert-info">加载中...</div> : null}
        {!loading && homeworks.length === 0 ? (
          <div className="alert alert-secondary">暂无作业。</div>
        ) : (
          <div className="d-flex flex-column gap-3">
            {homeworks.map((homework) => (
              <div key={homework.id} className="border rounded p-3 bg-white">
                <div className="d-flex justify-content-between">
                  <div>
                    <div className="fw-semibold">{homework.title}</div>
                    <div className="text-muted small">
                      {homework.course_name} · {homework.class_name}
                    </div>
                    {homework.description ? (
                      <div className="text-muted small">{homework.description}</div>
                    ) : null}
                  </div>
                  <div>
                    <input
                      type="file"
                      className="form-control form-control-sm"
                      onChange={(event) => uploadFile(homework.id, event.target.files[0])}
                    />
                  </div>
                </div>
                {homework.submissions && homework.submissions.length > 0 ? (
                  <div className="mt-3">
                    <div className="small text-muted">提交记录</div>
                    <ul className="list-group list-group-flush">
                      {homework.submissions.map((submission) => (
                        <li key={submission.id} className="list-group-item px-0">
                          <div className="small">
                            {submission.file_name} · 版本 {submission.version} ·{' '}
                            {new Date(submission.submitted_at).toLocaleString()}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
