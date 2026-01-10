import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function StudentSubmission() {
  const [assignments, setAssignments] = useState([])
  const [assignmentId, setAssignmentId] = useState('')
  const [assignmentNumber, setAssignmentNumber] = useState('')
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    const loadAssignments = async () => {
      const response = await apiFetch('/grading/api/student/assignments/')
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        setMessage((data && data.message) || 'Failed to load assignments')
        return
      }
      setAssignments(data.assignments || [])
    }
    loadAssignments()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file) {
      setMessage('Please select a file to upload.')
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
      setMessage((data && data.message) || 'Upload failed')
      return
    }
    setMessage(data.message || 'Upload success')
    setAssignmentId('')
    setAssignmentNumber('')
    setFile(null)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">Student Submission</h4>
      </div>
      <div className="card-body">
        {message ? <div className="alert alert-info">{message}</div> : null}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Assignment</label>
            <select
              className="form-select"
              value={assignmentId}
              onChange={(event) => setAssignmentId(event.target.value)}
              required
            >
              <option value="">Select assignment</option>
              {assignments.map((assignment) => (
                <option key={assignment.id} value={assignment.id}>
                  {assignment.course_name} · {assignment.class_name} · {assignment.name}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Assignment Number</label>
            <input
              className="form-control"
              value={assignmentNumber}
              onChange={(event) => setAssignmentNumber(event.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label className="form-label">File</label>
            <input className="form-control" type="file" onChange={(event) => setFile(event.target.files[0])} />
          </div>
          <button className="btn btn-primary" type="submit">
            Upload
          </button>
        </form>
      </div>
    </div>
  )
}
