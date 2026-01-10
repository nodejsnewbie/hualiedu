import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function BatchAiScore() {
  const [step, setStep] = useState(1)
  const [scoringType, setScoringType] = useState('')
  const [repositories, setRepositories] = useState([])
  const [selectedRepo, setSelectedRepo] = useState('')
  const [classes, setClasses] = useState([])
  const [homeworks, setHomeworks] = useState([])
  const [selectedClass, setSelectedClass] = useState('')
  const [selectedHomework, setSelectedHomework] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const loadRepositories = async () => {
    setLoading(true)
    const response = await apiFetch('/grading/batch-ai-score/')
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.status === 'success') {
      setRepositories(data.repositories || [])
    } else {
      setMessage((data && data.message) || '加载仓库失败')
    }
    setLoading(false)
  }

  const loadClasses = async (repoName) => {
    setLoading(true)
    const response = await apiFetch(`/grading/batch-ai-score/get-classes/?repository=${repoName}`)
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.status === 'success') {
      setClasses(data.classes || [])
    } else {
      setMessage((data && data.message) || '加载班级失败')
    }
    setLoading(false)
  }

  const loadHomeworks = async (repoName, className) => {
    setLoading(true)
    const response = await apiFetch(
      `/grading/batch-ai-score/get-homework/?repository=${repoName}&class=${className}`,
    )
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.status === 'success') {
      setHomeworks(data.homework_list || [])
    } else {
      setMessage((data && data.message) || '加载作业列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    loadRepositories()
  }, [])

  const startScoring = async () => {
    setLoading(true)
    setMessage('')
    const payload = new URLSearchParams({
      scoring_type: scoringType,
      repository: selectedRepo,
    })
    if (selectedClass) payload.append('class', selectedClass)
    if (selectedHomework) payload.append('homework', selectedHomework)

    const response = await apiFetch('/grading/batch-ai-score/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      setMessage((data && data.message) || '批量AI评分失败')
    } else {
      setMessage(data.message || '批量AI评分完成')
    }
    setLoading(false)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">批量AI评分</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}

        <div className="mb-3">
          <h6>步骤 1：选择评分范围</h6>
          <div className="d-flex gap-2 flex-wrap">
            {['repository', 'class', 'homework'].map((type) => (
              <button
                key={type}
                className={`btn ${scoringType === type ? 'btn-primary' : 'btn-outline-primary'}`}
                type="button"
                onClick={() => {
                  setScoringType(type)
                  setStep(2)
                }}
              >
                {type === 'repository' ? '仓库' : type === 'class' ? '班级' : '作业'}
              </button>
            ))}
          </div>
        </div>

        {step >= 2 ? (
          <div className="mb-3">
            <h6>步骤 2：选择仓库</h6>
            {loading ? <div className="text-muted">加载中...</div> : null}
            <div className="d-flex gap-2 flex-wrap">
              {repositories.map((repo) => (
                <button
                  key={repo.name}
                  className={`btn ${selectedRepo === repo.name ? 'btn-success' : 'btn-outline-success'}`}
                  type="button"
                  onClick={() => {
                    setSelectedRepo(repo.name)
                    setSelectedClass('')
                    setSelectedHomework('')
                    setClasses([])
                    setHomeworks([])
                    if (scoringType === 'class' || scoringType === 'homework') {
                      loadClasses(repo.name)
                    }
                    setStep(3)
                  }}
                >
                  {repo.name}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {step >= 3 && scoringType !== 'repository' ? (
          <div className="mb-3">
            <h6>步骤 3：选择班级</h6>
            <div className="d-flex gap-2 flex-wrap">
              {classes.map((cls) => (
                <button
                  key={cls.name}
                  className={`btn ${selectedClass === cls.name ? 'btn-warning' : 'btn-outline-warning'}`}
                  type="button"
                  onClick={() => {
                    setSelectedClass(cls.name)
                    setSelectedHomework('')
                    if (scoringType === 'homework') {
                      loadHomeworks(selectedRepo, cls.name)
                    }
                    setStep(4)
                  }}
                >
                  {cls.name}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {step >= 4 && scoringType === 'homework' ? (
          <div className="mb-3">
            <h6>步骤 4：选择作业</h6>
            <div className="d-flex gap-2 flex-wrap">
              {homeworks.map((hw) => (
                <button
                  key={hw.name}
                  className={`btn ${selectedHomework === hw.name ? 'btn-info' : 'btn-outline-info'}`}
                  type="button"
                  onClick={() => {
                    setSelectedHomework(hw.name)
                    setStep(5)
                  }}
                >
                  {hw.name}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-3">
          <button
            className="btn btn-success"
            type="button"
            onClick={startScoring}
            disabled={!selectedRepo || (scoringType === 'class' && !selectedClass) || (scoringType === 'homework' && !selectedHomework)}
          >
            开始评分
          </button>
        </div>
      </div>
    </div>
  )
}
