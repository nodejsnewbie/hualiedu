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
      setMessage((data && data.message) || 'Failed to load repositories')
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
      setMessage((data && data.message) || 'Failed to load classes')
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
      setMessage((data && data.message) || 'Failed to load homework list')
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
      setMessage((data && data.message) || 'Batch AI scoring failed')
    } else {
      setMessage(data.message || 'Batch AI scoring completed')
    }
    setLoading(false)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Batch AI Score</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}

        <div className="mb-3">
          <h6>Step 1: Select scoring scope</h6>
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
                {type}
              </button>
            ))}
          </div>
        </div>

        {step >= 2 ? (
          <div className="mb-3">
            <h6>Step 2: Select repository</h6>
            {loading ? <div className="text-muted">Loading...</div> : null}
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
            <h6>Step 3: Select class</h6>
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
            <h6>Step 4: Select homework</h6>
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
            Start AI Scoring
          </button>
        </div>
      </div>
    </div>
  )
}
