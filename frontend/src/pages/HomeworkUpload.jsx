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
    <div className="min-h-screen">
      <div className="page-shell max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">作业上传</h1>
          <p className="mt-1 text-sm text-slate-500">上传作业并查看提交记录。</p>
        </header>

        {message ? (
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        ) : null}

        {loading ? (
          <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
            加载中...
          </div>
        ) : null}

        {!loading && homeworks.length === 0 ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            暂无作业。
          </div>
        ) : (
          <div className="space-y-4">
            {homeworks.map((homework) => (
              <div key={homework.id} className="card-surface p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-base font-semibold text-slate-900">{homework.title}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {homework.course_name} / {homework.class_name}
                    </div>
                    {homework.description ? (
                      <div className="mt-2 text-xs text-slate-600">{homework.description}</div>
                    ) : null}
                  </div>
                  <div>
                    <input
                      type="file"
                      className="block w-56 text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                      onChange={(event) => uploadFile(homework.id, event.target.files[0])}
                    />
                  </div>
                </div>

                {homework.submissions && homework.submissions.length > 0 ? (
                  <div className="mt-4">
                    <div className="text-xs font-semibold text-slate-500">提交记录</div>
                    <div className="mt-2 space-y-2">
                      {homework.submissions.map((submission) => (
                        <div
                          key={submission.id}
                          className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600"
                        >
                          <span>{submission.file_name}</span>
                          <span>版本 {submission.version}</span>
                          <span>{new Date(submission.submitted_at).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
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
