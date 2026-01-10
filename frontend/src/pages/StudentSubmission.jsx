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
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">学生提交</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">课程</label>
            <select
              className="form-select"
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
          <div className="mb-3">
            <label className="form-label">作业</label>
            <select
              className="form-select"
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
          <div className="mb-3">
            <label className="form-label">作业次数目录</label>
            <select
              className="form-select"
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
            <div className="d-flex align-items-center gap-2 mt-2">
              <button
                className="btn btn-outline-primary btn-sm"
                type="button"
                onClick={createDirectory}
                disabled={!assignmentId || creatingDirectory}
              >
                {creatingDirectory ? '创建中...' : '创建新作业目录'}
              </button>
              <span className="text-muted small">
                未找到合适目录时可自动创建下一次作业目录。
              </span>
            </div>
          </div>
          <div className="mb-3">
            <label className="form-label">文件</label>
            <input className="form-control" type="file" onChange={(event) => setFile(event.target.files[0])} />
          </div>
          <button className="btn btn-primary" type="submit">
            上传
          </button>
        </form>
      </div>
    </div>
  )
}
