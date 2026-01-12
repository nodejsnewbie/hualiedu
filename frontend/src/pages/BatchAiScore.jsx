import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

const scoringOptions = [
  { value: 'repository', label: '仓库' },
  { value: 'class', label: '班级' },
  { value: 'homework', label: '作业' },
]

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

  const canStart =
    selectedRepo &&
    (scoringType !== 'class' || selectedClass) &&
    (scoringType !== 'homework' || selectedHomework)

  return (
    <div className="min-h-screen">
      <div className="page-shell max-w-5xl flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">批量 AI 评分</h1>
          <p className="mt-1 text-sm text-slate-500">选择评分范围并发起批量评分任务。</p>
        </header>

        <section className="card-surface p-6">
          {message ? (
            <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {message}
            </div>
          ) : null}

          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-700">步骤 1：选择评分范围</h2>
                {loading ? (
                  <span className="text-xs text-slate-400">加载中...</span>
                ) : null}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {scoringOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      setScoringType(option.value)
                      setStep(2)
                    }}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                      scoringType === option.value
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {step >= 2 ? (
              <div>
                <h2 className="text-sm font-semibold text-slate-700">步骤 2：选择仓库</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {repositories.map((repo) => (
                    <button
                      key={repo.name}
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
                      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                        selectedRepo === repo.name
                          ? 'border-emerald-600 bg-emerald-600 text-white'
                          : 'border-emerald-200 bg-white text-emerald-700 hover:border-emerald-300 hover:bg-emerald-50'
                      }`}
                    >
                      {repo.name}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {step >= 3 && scoringType !== 'repository' ? (
              <div>
                <h2 className="text-sm font-semibold text-slate-700">步骤 3：选择班级</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {classes.map((cls) => (
                    <button
                      key={cls.name}
                      type="button"
                      onClick={() => {
                        setSelectedClass(cls.name)
                        setSelectedHomework('')
                        if (scoringType === 'homework') {
                          loadHomeworks(selectedRepo, cls.name)
                        }
                        setStep(4)
                      }}
                      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                        selectedClass === cls.name
                          ? 'border-amber-500 bg-amber-500 text-white'
                          : 'border-amber-200 bg-white text-amber-700 hover:border-amber-300 hover:bg-amber-50'
                      }`}
                    >
                      {cls.name}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {step >= 4 && scoringType === 'homework' ? (
              <div>
                <h2 className="text-sm font-semibold text-slate-700">步骤 4：选择作业</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {homeworks.map((hw) => (
                    <button
                      key={hw.name}
                      type="button"
                      onClick={() => {
                        setSelectedHomework(hw.name)
                        setStep(5)
                      }}
                      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                        selectedHomework === hw.name
                          ? 'border-sky-500 bg-sky-500 text-white'
                          : 'border-sky-200 bg-white text-sky-700 hover:border-sky-300 hover:bg-sky-50'
                      }`}
                    >
                      {hw.name}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={startScoring}
                disabled={!canStart}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                开始评分
              </button>
              {!canStart ? (
                <span className="text-xs text-slate-400">请按步骤选择范围</span>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
