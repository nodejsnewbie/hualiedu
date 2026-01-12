import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function StudentSubmission() {
  const [assignments, setAssignments] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')
  const [assignmentId, setAssignmentId] = useState('')
  const [assignmentNumber, setAssignmentNumber] = useState('')
  const [directories, setDirectories] = useState([])
  const [loadingDirectories, setLoadingDirectories] = useState(false)
  const [creatingDirectory, setCreatingDirectory] = useState(false)
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    const loadAssignments = async () => {
      const response = await apiFetch('/grading/api/student/assignments/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        setMessage((data && data.message) || '加载作业失败')
        return
      }
      setAssignments(data.assignments || [])
    }
    loadAssignments()
  }, [])

  const loadDirectories = async (targetAssignmentId) => {
    if (!targetAssignmentId) {
      setDirectories([])
      return
    }
    setLoadingDirectories(true)
    const response = await apiFetch(
      `/grading/api/assignments/directories/?assignment_id=${targetAssignmentId}`,
    )
    const data = await response.json().catch(() => null)
    if (response.ok && data && data.success) {
      setDirectories(data.directories || [])
    } else {
      setMessage((data && data.message) || '加载作业目录失败')
    }
    setLoadingDirectories(false)
  }

  const handleAssignmentChange = (event) => {
    const value = event.target.value
    setAssignmentId(value)
    setAssignmentNumber('')
    loadDirectories(value)
  }

  const courseOptions = Array.from(
    new Set(assignments.map((assignment) => assignment.course_name).filter(Boolean)),
  )

  const filteredAssignments = selectedCourse
    ? assignments.filter((assignment) => assignment.course_name === selectedCourse)
    : assignments

  const createDirectory = async () => {
    if (!assignmentId) {
      setMessage('请先选择作业。')
      return
    }
    setCreatingDirectory(true)
    const response = await apiFetch('/grading/api/student/create-directory/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ assignment_id: assignmentId, auto_generate: 'true' }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.success === false)) {
      setMessage((data && data.message) || '创建作业目录失败')
      setCreatingDirectory(false)
      return
    }
    const directoryName = data && data.directory_name ? data.directory_name : ''
    await loadDirectories(assignmentId)
    setAssignmentNumber(directoryName)
    setMessage(data.message || '作业目录创建成功')
    setCreatingDirectory(false)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file) {
      setMessage('请选择要上传的文件。')
      return
    }
    if (!assignmentNumber) {
      setMessage('请选择作业次数目录。')
      return
    }
    const formData = new FormData()
    formData.append('assignment_id', assignmentId)
    formData.append('assignment_number', assignmentNumber)
    formData.append('file', file)
    const response = await apiFetch('/grading/api/student/upload/', {
      method: 'POST',
      body: formData,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.success === false)) {
      setMessage((data && data.message) || '上传失败')
      return
    }
    setMessage(data.message || '上传成功')
    setAssignmentId('')
    setAssignmentNumber('')
    setFile(null)
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto w-full max-w-4xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">学生提交</h1>
          <p className="mt-1 text-sm text-slate-500">选择作业并上传文件。</p>
        </header>

        {message ? (
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        ) : null}

        <section className="card-surface p-6">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-700">课程</label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                value={selectedCourse}
                onChange={(event) => {
                  setSelectedCourse(event.target.value)
                  setAssignmentId('')
                  setAssignmentNumber('')
                  setDirectories([])
                }}
              >
                <option value="">全部课程</option>
                {courseOptions.map((course) => (
                  <option key={course} value={course}>
                    {course}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">作业</label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                value={assignmentId}
                onChange={handleAssignmentChange}
                required
              >
                <option value="">请选择作业</option>
                {filteredAssignments.map((assignment) => (
                  <option key={assignment.id} value={assignment.id}>
                    {assignment.course_name} · {assignment.class_name} · {assignment.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">作业次数目录</label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                value={assignmentNumber}
                onChange={(event) => setAssignmentNumber(event.target.value)}
                required
                disabled={!assignmentId || loadingDirectories}
              >
                <option value="">
                  {loadingDirectories ? '加载中...' : '请选择作业次数'}
                </option>
                {directories.map((dir) => (
                  <option key={dir.name} value={dir.name}>
                    {dir.name}
                  </option>
                ))}
              </select>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <button
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                  type="button"
                  onClick={createDirectory}
                  disabled={!assignmentId || creatingDirectory}
                >
                  {creatingDirectory ? '创建中...' : '创建新作业目录'}
                </button>
                <span>未找到合适目录时，可自动创建下一次作业目录。</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">文件</label>
              <input
                className="mt-2 block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                type="file"
                onChange={(event) => setFile(event.target.files[0])}
              />
            </div>

            <button
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              type="submit"
            >
              上传
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}
