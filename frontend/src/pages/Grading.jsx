
import { useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE_URL } from '../api/config.js'
import { ensureCsrfToken, getCsrfToken } from '../api/csrf.js'

const COURSE_TYPE_OPTIONS = [
  { value: 'theory', label: '理论课' },
  { value: 'lab', label: '实验课' },
  { value: 'practice', label: '实践课' },
  { value: 'mixed', label: '理论+实验' },
]

const LETTER_GRADES = ['A', 'B', 'C', 'D', 'E']
const TEXT_GRADES = ['优秀', '良好', '中等', '及格', '不及格']
const HOMEWORK_TYPE_OPTIONS = [
  { value: 'normal', label: '普通作业' },
  { value: 'lab_report', label: '实验报告' },
]

const apiUrl = (path) => `${API_BASE_URL}${path}`

const toParams = (payload) => {
  const params = new URLSearchParams()
  Object.entries(payload || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    params.append(key, String(value))
  })
  return params
}

const flattenFiles = (nodes, out = []) => {
  nodes.forEach((node) => {
    if (node.type === 'file') {
      out.push(node)
      return
    }
    if (node.children && node.children.length > 0) {
      flattenFiles(node.children, out)
    }
  })
  return out
}

const updateTreeNode = (nodes, targetId, updater) =>
  nodes.map((node) => {
    if (node.id === targetId) {
      return updater(node)
    }
    if (!node.children || node.children.length === 0) {
      return node
    }
    return {
      ...node,
      children: updateTreeNode(node.children, targetId, updater),
    }
  })

const getDirectoryPath = (path) => {
  if (!path) return ''
  const parts = path.split('/')
  if (parts.length <= 1) return ''
  return parts.slice(0, -1).join('/')
}

const formatFileIndex = (index, total) => {
  if (!total) return '0 / 0'
  return `${index + 1} / ${total}`
}

const getHomeworkFolderFromPath = (path) => {
  if (!path) return ''
  const parts = path.split('/').filter(Boolean)
  if (parts.length >= 2) {
    return parts[1]
  }
  if (parts.length === 1) {
    return parts[0]
  }
  return ''
}

export default function Grading() {
  const [repositories, setRepositories] = useState([])
  const [repoLoading, setRepoLoading] = useState(false)
  const [repoError, setRepoError] = useState('')
  const [selectedRepoId, setSelectedRepoId] = useState('')

  const [courses, setCourses] = useState([])
  const [courseLoading, setCourseLoading] = useState(false)
  const [courseError, setCourseError] = useState('')
  const [selectedCourse, setSelectedCourse] = useState('')

  const [courseType, setCourseType] = useState('')
  const [courseTypeLoading, setCourseTypeLoading] = useState(false)
  const [courseTypeError, setCourseTypeError] = useState('')

  const [treeLoading, setTreeLoading] = useState(false)
  const [treeData, setTreeData] = useState([])
  const [expandedNodes, setExpandedNodes] = useState(() => new Set())
  const [selectedNodeId, setSelectedNodeId] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)

  const [directoryFileCount, setDirectoryFileCount] = useState(0)

  const [fileLoading, setFileLoading] = useState(false)
  const [fileError, setFileError] = useState('')
  const [fileContent, setFileContent] = useState(null)
  const [gradeInfo, setGradeInfo] = useState(null)

  const [gradeMode, setGradeMode] = useState('letter')
  const [selectedGrade, setSelectedGrade] = useState('B')
  const [percentageValue, setPercentageValue] = useState('85')
  const [gradeSubmitError, setGradeSubmitError] = useState('')
  const pendingGradeRef = useRef(null)

  const [commentModalOpen, setCommentModalOpen] = useState(false)
  const [commentText, setCommentText] = useState('')
  const [commentLoading, setCommentLoading] = useState(false)
  const [commentTemplates, setCommentTemplates] = useState([])
  const [commentError, setCommentError] = useState('')

  const [homeworkTypeModal, setHomeworkTypeModal] = useState(null)
  const [homeworkTypeSaving, setHomeworkTypeSaving] = useState(false)
  const [homeworkTypeError, setHomeworkTypeError] = useState('')

  const [batchGradeState, setBatchGradeState] = useState({
    enabled: false,
    folderName: '',
    homeworkId: null,
    relativePath: '',
  })
  const [batchProgress, setBatchProgress] = useState(null)
  const batchPollRef = useRef(null)

  useEffect(() => {
    ensureCsrfToken()
  }, [])

  const flatFiles = useMemo(() => flattenFiles(treeData, []), [treeData])
  const currentFileIndex = useMemo(() => {
    if (!selectedNode || selectedNode.type !== 'file') {
      return -1
    }
    return flatFiles.findIndex((file) => file.id === selectedNode.id)
  }, [flatFiles, selectedNode])

  const stopBatchPolling = () => {
    if (batchPollRef.current) {
      clearInterval(batchPollRef.current)
      batchPollRef.current = null
    }
  }

  const loadRepositories = async () => {
    setRepoLoading(true)
    setRepoError('')
    try {
      const response = await fetch(apiUrl('/grading/api/repositories/'), {
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || (data && data.status !== 'success')) {
        throw new Error((data && data.message) || '获取作业仓库失败')
      }
      const list = data.repositories || []
      setRepositories(list)
      if (list.length > 0) {
        const nextRepoId = String(list[0].id)
        await handleRepoChange(nextRepoId)
      } else {
        setSelectedRepoId('')
        setCourses([])
        setSelectedCourse('')
        setTreeData([])
      }
    } catch (error) {
      setRepoError(error.message || '获取作业仓库失败')
    } finally {
      setRepoLoading(false)
    }
  }

  useEffect(() => {
    loadRepositories()
  }, [])

  const loadCourses = async (repoId) => {
    if (!repoId) {
      setCourses([])
      return []
    }
    setCourseLoading(true)
    setCourseError('')
    try {
      const response = await fetch(
        apiUrl(`/grading/get_courses_list/?repo_id=${encodeURIComponent(repoId)}`),
        { credentials: 'include' },
      )
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status !== 'success') {
        throw new Error((data && data.message) || '获取课程失败')
      }
      const list = data.courses || []
      setCourses(list)
      return list
    } catch (error) {
      setCourseError(error.message || '获取课程失败')
      setCourses([])
      return []
    } finally {
      setCourseLoading(false)
    }
  }

  const loadCourseType = async (courseName) => {
    if (!courseName) {
      setCourseType('')
      setCourseTypeError('')
      return
    }
    setCourseTypeLoading(true)
    setCourseTypeError('')
    try {
      const response = await fetch(
        apiUrl(
          `/grading/api/course-info/?course_name=${encodeURIComponent(courseName)}&auto_create=true`,
        ),
        { credentials: 'include' },
      )
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.message) || '获取课程类型失败')
      }
      setCourseType(data.course?.course_type || 'theory')
    } catch (error) {
      setCourseType('')
      setCourseTypeError(error.message || '获取课程类型失败')
    } finally {
      setCourseTypeLoading(false)
    }
  }

  const loadDirectoryTree = async (repoId, courseName) => {
    if (!repoId) {
      setTreeData([])
      return
    }
    setTreeLoading(true)
    try {
      const params = new URLSearchParams({ repo_id: repoId })
      if (courseName) {
        params.set('course', courseName)
      }
      const response = await fetch(apiUrl(`/grading/get_directory_tree/?${params.toString()}`), {
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      setTreeData((data && data.children) || [])
    } catch (error) {
      setTreeData([])
    } finally {
      setTreeLoading(false)
    }
  }

  const handleRepoChange = async (repoId) => {
    const value = String(repoId || '')
    setSelectedRepoId(value)
    setSelectedCourse('')
    setCourseType('')
    setCourses([])
    setTreeData([])
    setSelectedNodeId('')
    setSelectedNode(null)
    setFileContent(null)
    setGradeInfo(null)

    if (!value) {
      return
    }

    const list = await loadCourses(value)
    if (list.length > 0) {
      const nextCourse = list[0].name
      setSelectedCourse(nextCourse)
      await loadDirectoryTree(value, nextCourse)
      await loadCourseType(nextCourse)
    } else {
      await loadDirectoryTree(value, '')
    }
  }

  const handleCourseChange = async (courseName) => {
    if (!selectedRepoId) {
      return
    }
    const value = String(courseName || '')
    setSelectedCourse(value)
    setSelectedNodeId('')
    setSelectedNode(null)
    setFileContent(null)
    setGradeInfo(null)
    await loadDirectoryTree(selectedRepoId, value)
    await loadCourseType(value)
  }

  const handleCourseTypeChange = async (nextType) => {
    if (!selectedCourse) {
      setCourseType(nextType)
      return
    }
    const previousType = courseType
    setCourseType(nextType)
    setCourseTypeLoading(true)
    setCourseTypeError('')
    try {
      await ensureCsrfToken()
      const response = await fetch(apiUrl('/grading/api/update-course-type/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({ course_name: selectedCourse, course_type: nextType }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.message) || '更新课程类型失败')
      }
    } catch (error) {
      setCourseType(previousType)
      setCourseTypeError(error.message || '更新课程类型失败')
    } finally {
      setCourseTypeLoading(false)
    }
  }

  const loadDirectoryFileCount = async (path) => {
    if (!path || !selectedRepoId) {
      setDirectoryFileCount(0)
      return
    }
    try {
      const response = await fetch(apiUrl('/grading/get_dir_file_count/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({
          path,
          repo_id: selectedRepoId,
          course: selectedCourse,
        }).toString(),
        credentials: 'include',
      })
      const text = await response.text()
      const count = Number.parseInt(text, 10)
      setDirectoryFileCount(Number.isNaN(count) ? 0 : count)
    } catch {
      setDirectoryFileCount(0)
    }
  }

  const loadFileContent = async (path) => {
    if (!path) {
      return
    }
    setFileLoading(true)
    setFileError('')
    setFileContent(null)
    setGradeInfo(null)
    try {
      const response = await fetch(apiUrl('/grading/get_file_content/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: toParams({
          path,
          repo_id: selectedRepoId,
          course: selectedCourse,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status !== 'success') {
        throw new Error((data && data.message) || '加载文件失败')
      }
      setFileContent(data)
      const nextGradeInfo = data.grade_info || null
      setGradeInfo(nextGradeInfo)
      if (nextGradeInfo?.grade_type) {
        setGradeMode(nextGradeInfo.grade_type)
      }
      if (nextGradeInfo?.grade) {
        const gradeValue = String(nextGradeInfo.grade)
        setSelectedGrade(gradeValue)
        if (nextGradeInfo.grade_type === 'percentage') {
          setPercentageValue(gradeValue)
        }
      } else if (nextGradeInfo?.grade_type === 'percentage') {
        setPercentageValue('85')
      } else if (!nextGradeInfo?.grade_type) {
        setGradeMode('letter')
        setSelectedGrade('B')
      }
    } catch (error) {
      setFileError(error.message || '加载文件失败')
    } finally {
      setFileLoading(false)
    }
  }

  const resolveHomeworkInfo = async (folderPath) => {
    if (!folderPath || !selectedCourse) {
      setBatchGradeState({ enabled: false, folderName: '', homeworkId: null, relativePath: '' })
      return
    }

    const parts = folderPath.split('/').filter(Boolean)
    const folderName = parts[parts.length - 1] || ''
    if (!folderName) {
      setBatchGradeState({ enabled: false, folderName: '', homeworkId: null, relativePath: '' })
      return
    }

    try {
      const response = await fetch(
        apiUrl(
          `/grading/api/homework-info/?course_name=${encodeURIComponent(selectedCourse)}&homework_folder=${encodeURIComponent(folderName)}`,
        ),
        { credentials: 'include' },
      )
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.message) || '未找到作业信息')
      }

      let relativePath = folderPath
      if (selectedCourse && !relativePath.startsWith(`${selectedCourse}/`)) {
        relativePath = `${selectedCourse}/${folderPath}`
      }

      setBatchGradeState({
        enabled: true,
        folderName,
        homeworkId: data.homework.id,
        relativePath,
      })
    } catch {
      setBatchGradeState({ enabled: false, folderName: '', homeworkId: null, relativePath: '' })
    }
  }

  const handleSelectNode = async (node) => {
    setSelectedNodeId(node.id)
    setSelectedNode(node)

    if (node.type === 'folder') {
      setFileContent(null)
      setGradeInfo(null)
      await loadDirectoryFileCount(node.id)
      await resolveHomeworkInfo(node.id)
      return
    }

    if (node.type === 'file') {
      const directoryPath = getDirectoryPath(node.id)
      await loadDirectoryFileCount(directoryPath)
      await resolveHomeworkInfo(directoryPath)
      await loadFileContent(node.id)
    }
  }

  const toggleNode = (nodeId) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  const navigateFile = async (direction) => {
    if (currentFileIndex < 0 || flatFiles.length === 0) {
      return
    }
    const nextIndex = currentFileIndex + direction
    if (nextIndex < 0 || nextIndex >= flatFiles.length) {
      return
    }
    const target = flatFiles[nextIndex]
    await handleSelectNode(target)
  }

  const handleSubmitGrade = async (gradeOverride) => {
    if (!selectedNode || selectedNode.type !== 'file') {
      setGradeSubmitError('请先选择文件')
      return
    }
    if (gradeInfo?.locked) {
      setGradeSubmitError('此文件已锁定，无法修改评分')
      return
    }

    let gradeToSubmit = gradeOverride ?? selectedGrade
    if (gradeMode === 'percentage') {
      const value = Number.parseFloat(percentageValue)
      if (Number.isNaN(value)) {
        setGradeSubmitError('请输入有效的分数')
        return
      }
      if (value < 0 || value > 100) {
        setGradeSubmitError('分数必须在 0-100 之间')
        return
      }
      gradeToSubmit = String(value)
    }

    if (!gradeToSubmit) {
      setGradeSubmitError('请先选择评分')
      return
    }

    setGradeSubmitError('')
    try {
      await ensureCsrfToken()
      const response = await fetch(apiUrl('/grading/add_grade_to_file/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({
          path: selectedNode.id,
          repo_id: selectedRepoId,
          course: selectedCourse,
          grade: gradeToSubmit,
          grade_type: gradeMode,
          is_lab_report: gradeInfo?.is_lab_report || false,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      const success = response.ok && (data?.status === 'success' || data?.success)
      if (!success) {
        const message = data?.message || '评分失败'
        if (message.includes('实验报告必须添加评价')) {
          pendingGradeRef.current = gradeToSubmit
          setCommentModalOpen(true)
          return
        }
        throw new Error(message)
      }
      await loadFileContent(selectedNode.id)
    } catch (error) {
      setGradeSubmitError(error.message || '评分失败')
    }
  }

  const handleCancelGrade = async () => {
    if (!selectedNode || selectedNode.type !== 'file') {
      return
    }
    try {
      await ensureCsrfToken()
      const response = await fetch(apiUrl('/grading/remove_grade/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({
          path: selectedNode.id,
          repo_id: selectedRepoId,
          course: selectedCourse,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || data?.status !== 'success') {
        throw new Error(data?.message || '撤销评分失败')
      }
      await loadFileContent(selectedNode.id)
    } catch (error) {
      setGradeSubmitError(error.message || '撤销评分失败')
    }
  }

  const handleAiScore = async () => {
    if (!selectedNode || selectedNode.type !== 'file') {
      setGradeSubmitError('请先选择文件')
      return
    }
    if (gradeInfo?.locked) {
      setGradeSubmitError('此文件已锁定，无法评分')
      return
    }
    try {
      await ensureCsrfToken()
      const response = await fetch(apiUrl('/grading/ai_score/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({
          path: selectedNode.id,
          repo_id: selectedRepoId,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status !== 'success') {
        throw new Error((data && data.message) || 'AI 评分失败')
      }
      await loadFileContent(selectedNode.id)
    } catch (error) {
      setGradeSubmitError(error.message || 'AI 评分失败')
    }
  }

  const loadCommentTemplates = async () => {
    try {
      const response = await fetch(apiUrl('/grading/api/comment-templates/recommended/'), {
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        setCommentTemplates([])
        return
      }
      setCommentTemplates(data.templates || [])
    } catch {
      setCommentTemplates([])
    }
  }

  const loadTeacherComment = async () => {
    if (!selectedNode || selectedNode.type !== 'file') {
      setCommentText('')
      return
    }
    setCommentLoading(true)
    setCommentError('')
    try {
      const params = new URLSearchParams({
        file_path: selectedNode.id,
        repo_id: selectedRepoId,
        course: selectedCourse,
        homework_folder: getHomeworkFolderFromPath(selectedNode.id),
      })
      const response = await fetch(apiUrl(`/grading/get_teacher_comment/?${params.toString()}`), {
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.message) || '获取评语失败')
      }
      setCommentText(data.comment || '')
    } catch (error) {
      setCommentError(error.message || '获取评语失败')
    } finally {
      setCommentLoading(false)
    }
  }

  const recordCommentUsage = async (comment) => {
    if (!comment) return
    try {
      await ensureCsrfToken()
      await fetch(apiUrl('/grading/api/comment-templates/record-usage/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ comment_text: comment }),
        credentials: 'include',
      })
    } catch {
      // ignore
    }
  }

  const handleOpenCommentModal = async () => {
    setCommentModalOpen(true)
    await loadTeacherComment()
    await loadCommentTemplates()
  }

  const handleSaveComment = async () => {
    if (!selectedNode || selectedNode.type !== 'file') {
      return
    }
    if (!commentText.trim()) {
      setCommentError('请输入评语')
      return
    }
    setCommentError('')
    setCommentLoading(true)
    try {
      const response = await fetch(apiUrl('/grading/save_teacher_comment/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: toParams({
          file_path: selectedNode.id,
          comment: commentText.trim(),
          grade: selectedGrade,
          repo_id: selectedRepoId,
          course: selectedCourse,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || data.status === 'error' || data.success === false) {
        throw new Error((data && data.message) || '保存评语失败')
      }
      await recordCommentUsage(commentText.trim())
      setCommentModalOpen(false)
      await loadFileContent(selectedNode.id)
      if (pendingGradeRef.current) {
        const pending = pendingGradeRef.current
        pendingGradeRef.current = null
        setSelectedGrade(pending)
        await handleSubmitGrade(pending)
      }
    } catch (error) {
      setCommentError(error.message || '保存评语失败')
    } finally {
      setCommentLoading(false)
    }
  }

  const handleHomeworkTypeSave = async () => {
    if (!homeworkTypeModal || !selectedCourse) {
      return
    }
    setHomeworkTypeSaving(true)
    setHomeworkTypeError('')
    try {
      await ensureCsrfToken()
      const response = await fetch(apiUrl('/grading/api/update-homework-type/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken(),
        },
        body: toParams({
          course_name: selectedCourse,
          folder_name: homeworkTypeModal.folderName,
          homework_type: homeworkTypeModal.type,
        }).toString(),
        credentials: 'include',
      })
      const data = await response.json().catch(() => null)
      if (!response.ok || !data || !data.success) {
        throw new Error((data && data.message) || '更新作业类型失败')
      }
      setTreeData((prev) =>
        updateTreeNode(prev, homeworkTypeModal.nodeId, (node) => ({
          ...node,
          data: {
            ...(node.data || {}),
            homework_type: data.homework.homework_type,
            homework_type_display: data.homework.homework_type_display,
          },
        })),
      )
      setHomeworkTypeModal(null)
    } catch (error) {
      setHomeworkTypeError(error.message || '更新作业类型失败')
    } finally {
      setHomeworkTypeSaving(false)
    }
  }

  const startBatchPolling = (trackingId) => {
    stopBatchPolling()
    batchPollRef.current = setInterval(async () => {
      try {
        const response = await fetch(apiUrl(`/grading/batch-grade/progress/${trackingId}/`), {
          credentials: 'include',
        })
        const data = await response.json().catch(() => null)
        if (!response.ok || !data || !data.success) {
          return
        }
        const progress = data.data || {}
        setBatchProgress(progress)
        if (['success', 'error'].includes(progress.status)) {
          stopBatchPolling()
        }
      } catch {
        // ignore
      }
    }, 1000)
  }

  const handleBatchGrade = async () => {
    if (!batchGradeState.enabled || !batchGradeState.homeworkId) {
      return
    }
    try {
      await ensureCsrfToken()
      const trackingId = window.crypto?.randomUUID
        ? window.crypto.randomUUID()
        : `batch-${Date.now()}`
      setBatchProgress({ status: 'running', processed: 0, total: 0, message: '正在批量登分...' })
      startBatchPolling(trackingId)

      const response = await fetch(
        apiUrl(`/grading/homework/${batchGradeState.homeworkId}/batch-grade-to-registry/`),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
          },
          body: toParams({
            relative_path: batchGradeState.relativePath,
            tracking_id: trackingId,
            repo_id: selectedRepoId,
            course: selectedCourse,
          }).toString(),
          credentials: 'include',
        },
      )
      const data = await response.json().catch(() => null)
      if (!response.ok || !data) {
        throw new Error(data?.message || '批量登分失败')
      }
      setBatchProgress({
        status: data.success || data.data ? 'success' : 'error',
        message: data.message || '批量登分完成',
        details: data.data || data,
      })
    } catch (error) {
      setBatchProgress({ status: 'error', message: error.message || '批量登分失败' })
    }
  }

  const renderFilePreview = () => {
    if (!fileContent) {
      return (
        <div className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
          请选择文件查看内容
        </div>
      )
    }

    if (fileContent.type === 'docx' || fileContent.type === 'excel') {
      return (
        <div
          className="prose max-w-none text-sm"
          dangerouslySetInnerHTML={{ __html: fileContent.content }}
        />
      )
    }

    if (fileContent.type === 'image') {
      return <img className="max-h-[720px] max-w-full rounded-md" src={fileContent.content} alt="预览" />
    }

    if (fileContent.type === 'pdf') {
      return (
        <iframe
          title="pdf-preview"
          className="h-[720px] w-full rounded-md border"
          src={fileContent.content}
        />
      )
    }

    if (fileContent.type === 'text') {
      return (
        <pre className="max-h-[720px] overflow-auto rounded-md bg-slate-900 p-4 text-xs text-slate-100">
          {fileContent.content}
        </pre>
      )
    }

    if (fileContent.type === 'binary') {
      const link = fileContent.content?.startsWith('/') ? apiUrl(fileContent.content) : fileContent.content
      return (
        <a
          className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white"
          href={link}
          target="_blank"
          rel="noreferrer"
        >
          下载文件
        </a>
      )
    }

    return <div className="rounded-md border border-slate-200 p-4 text-sm text-slate-500">暂不支持该类型</div>
  }

  const renderTreeNodes = (nodes, depth = 0) => (
    <ul className="space-y-1">
      {nodes.map((node) => {
        const isFolder = node.type === 'folder'
        const isExpanded = expandedNodes.has(node.id)
        const isSelected = selectedNodeId === node.id
        const hasUpdates = node.data?.has_updates
        const homeworkLabel = node.data?.homework_type_display
        const paddingLeft = depth * 16

        return (
          <li key={node.id}>
            <div
              className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition ${
                isSelected ? 'bg-amber-100 text-amber-900' : 'hover:bg-slate-100'
              }`}
              style={{ paddingLeft: paddingLeft + 8 }}
            >
              {isFolder ? (
                <button type="button" className="text-slate-500" onClick={() => toggleNode(node.id)}>
                  {isExpanded ? '-' : '+'}
                </button>
              ) : (
                <span className="text-slate-400">-</span>
              )}
              <button
                type="button"
                className="flex flex-1 items-center gap-2 text-left"
                onClick={() => handleSelectNode(node)}
              >
                <span className="text-slate-600">{isFolder ? '[DIR]' : '[FILE]'}</span>
                <span className="truncate">{node.text}</span>
              </button>
              {hasUpdates ? (
                <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] text-rose-700">更新</span>
              ) : null}
              {homeworkLabel ? (
                <button
                  type="button"
                  className="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] text-slate-700"
                  onClick={(event) => {
                    event.stopPropagation()
                    setHomeworkTypeModal({
                      nodeId: node.id,
                      folderName: node.text,
                      type: node.data?.homework_type || 'normal',
                    })
                  }}
                >
                  {homeworkLabel}
                </button>
              ) : null}
            </div>
            {isFolder && isExpanded && node.children && node.children.length > 0
              ? renderTreeNodes(node.children, depth + 1)
              : null}
          </li>
        )
      })}
    </ul>
  )

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-6">
      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <div className="space-y-4">
          <div className="card-surface p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700">作业目录</h2>
              <button
                type="button"
                onClick={loadRepositories}
                className="text-xs font-medium text-amber-600 hover:text-amber-700"
                disabled={repoLoading}
              >
                {repoLoading ? '加载中...' : '刷新'}
              </button>
            </div>
            <div className="mt-4 space-y-3">
              <label className="block text-xs font-semibold text-slate-500">选择作业仓库</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedRepoId}
                onChange={(event) => handleRepoChange(event.target.value)}
              >
                {repositories.length === 0 ? <option value="">暂无作业仓库</option> : null}
                {repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.name}
                  </option>
                ))}
              </select>
              {repoError ? <p className="text-xs text-rose-600">{repoError}</p> : null}

              <label className="block text-xs font-semibold text-slate-500">课程</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedCourse}
                onChange={(event) => handleCourseChange(event.target.value)}
                disabled={!selectedRepoId || courseLoading}
              >
                {!selectedRepoId ? <option value="">请先选择仓库</option> : null}
                {selectedRepoId && courses.length === 0 ? <option value="">暂无课程</option> : null}
                {courses.map((course) => (
                  <option key={course.path || course.name} value={course.name}>
                    {course.name}
                  </option>
                ))}
              </select>
              {courseError ? <p className="text-xs text-rose-600">{courseError}</p> : null}

              <label className="block text-xs font-semibold text-slate-500">课程类型</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={courseType}
                onChange={(event) => handleCourseTypeChange(event.target.value)}
                disabled={!selectedCourse || courseTypeLoading}
              >
                {!selectedCourse ? <option value="">请先选择课程</option> : null}
                {COURSE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {courseTypeError ? <p className="text-xs text-rose-600">{courseTypeError}</p> : null}
            </div>

            <div className="mt-4 space-y-2">
              <button
                type="button"
                className={`w-full rounded-md px-3 py-2 text-sm font-medium text-white transition ${
                  batchGradeState.enabled
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-slate-300 text-slate-500'
                }`}
                onClick={handleBatchGrade}
                disabled={!batchGradeState.enabled}
              >
                批量登分{batchGradeState.folderName ? ` (${batchGradeState.folderName})` : ''}
              </button>
              <button
                type="button"
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-600"
                disabled
              >
                批量 AI 评分（开发中）
              </button>
              <p className="text-xs text-slate-400">选择作业文件夹后才能启用批量登分。</p>
            </div>

            {batchProgress ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                <p className="font-medium">{batchProgress.message || '批量登分中...'}</p>
                {batchProgress.total ? (
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-2 rounded-full ${
                        batchProgress.status === 'error'
                          ? 'bg-rose-500'
                          : batchProgress.status === 'success'
                            ? 'bg-emerald-500'
                            : 'bg-amber-500'
                      }`}
                      style={{
                        width: `${Math.min(
                          100,
                          Math.round((batchProgress.processed / batchProgress.total) * 100),
                        )}%`,
                      }}
                    />
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="card-surface p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">目录树</h3>
              {treeLoading ? <span className="text-xs text-slate-400">加载中...</span> : null}
            </div>
            <div className="mt-3 max-h-[520px] overflow-auto pr-2">
              {treeData.length === 0 ? (
                <p className="text-xs text-slate-400">暂无目录</p>
              ) : (
                renderTreeNodes(treeData)
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-surface p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">文件内容</h2>
                <p className="text-xs text-slate-400">当前目录文件数：{directoryFileCount}</p>
              </div>
              <span className="text-xs text-slate-400">{formatFileIndex(currentFileIndex, flatFiles.length)}</span>
            </div>

            <div className="mt-4">
              {fileLoading ? (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                  正在加载文件内容...
                </div>
              ) : fileError ? (
                <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
                  {fileError}
                </div>
              ) : (
                renderFilePreview()
              )}
            </div>
          </div>

          <div className="card-surface p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">评分</h2>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-600"
                  onClick={() => navigateFile(-1)}
                >
                  上一个
                </button>
                <button
                  type="button"
                  className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-600"
                  onClick={() => navigateFile(1)}
                >
                  下一个
                </button>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <div className="flex rounded-md border border-slate-200 bg-slate-50 text-xs font-medium">
                <button
                  type="button"
                  className={`px-3 py-1 ${gradeMode === 'letter' ? 'bg-slate-900 text-white' : ''}`}
                  onClick={() => setGradeMode('letter')}
                >
                  字母
                </button>
                <button
                  type="button"
                  className={`px-3 py-1 ${gradeMode === 'text' ? 'bg-slate-900 text-white' : ''}`}
                  onClick={() => setGradeMode('text')}
                >
                  文字
                </button>
                <button
                  type="button"
                  className={`px-3 py-1 ${gradeMode === 'percentage' ? 'bg-slate-900 text-white' : ''}`}
                  onClick={() => setGradeMode('percentage')}
                >
                  百分制
                </button>
              </div>

              {gradeMode === 'letter' ? (
                <div className="flex flex-wrap gap-2">
                  {LETTER_GRADES.map((grade) => (
                    <button
                      key={grade}
                      type="button"
                      className={`rounded-md border px-3 py-1 text-xs font-semibold ${
                        selectedGrade === grade
                          ? 'border-amber-500 bg-amber-100 text-amber-700'
                          : 'border-slate-200 text-slate-600'
                      }`}
                      onClick={() => setSelectedGrade(grade)}
                    >
                      {grade}
                    </button>
                  ))}
                </div>
              ) : null}

              {gradeMode === 'text' ? (
                <div className="flex flex-wrap gap-2">
                  {TEXT_GRADES.map((grade) => (
                    <button
                      key={grade}
                      type="button"
                      className={`rounded-md border px-3 py-1 text-xs font-semibold ${
                        selectedGrade === grade
                          ? 'border-amber-500 bg-amber-100 text-amber-700'
                          : 'border-slate-200 text-slate-600'
                      }`}
                      onClick={() => setSelectedGrade(grade)}
                    >
                      {grade}
                    </button>
                  ))}
                </div>
              ) : null}

              {gradeMode === 'percentage' ? (
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    value={percentageValue}
                    onChange={(event) => setPercentageValue(event.target.value)}
                    className="w-24 rounded-md border border-slate-200 px-2 py-1 text-sm"
                  />
                  <span className="text-xs text-slate-500">%</span>
                </div>
              ) : null}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                className="rounded-md bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
                onClick={handleSubmitGrade}
                disabled={!selectedNode || selectedNode.type !== 'file'}
              >
                确认评分
              </button>
              <button
                type="button"
                className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-600"
                onClick={handleCancelGrade}
                disabled={!selectedNode || selectedNode.type !== 'file'}
              >
                撤销评分
              </button>
              <button
                type="button"
                className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-600"
                onClick={handleOpenCommentModal}
                disabled={!selectedNode || selectedNode.type !== 'file'}
              >
                教师评语
              </button>
              <button
                type="button"
                className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-600"
                onClick={handleAiScore}
                disabled={!selectedNode || selectedNode.type !== 'file' || gradeInfo?.ai_grading_disabled}
              >
                AI 评分
              </button>
            </div>

            {gradeSubmitError ? <p className="mt-3 text-xs text-rose-600">{gradeSubmitError}</p> : null}
          </div>
        </div>
      </div>

      {commentModalOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-2xl rounded-xl bg-white p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-800">教师评语</h3>
              <button
                type="button"
                className="text-sm text-slate-500"
                onClick={() => setCommentModalOpen(false)}
              >
                关闭
              </button>
            </div>

            {commentTemplates.length > 0 ? (
              <div className="mt-4">
                <p className="text-xs font-semibold text-slate-500">常用评语模板</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {commentTemplates.map((template) => (
                    <button
                      key={template.id}
                      type="button"
                      className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600"
                      onClick={() => setCommentText(template.comment_text)}
                    >
                      {template.comment_text.length > 24
                        ? `${template.comment_text.slice(0, 24)}...`
                        : template.comment_text}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mt-4">
              <textarea
                className="h-40 w-full rounded-md border border-slate-200 p-3 text-sm"
                value={commentText}
                onChange={(event) => setCommentText(event.target.value)}
                placeholder="请输入评语"
              />
            </div>
            {commentError ? <p className="mt-2 text-xs text-rose-600">{commentError}</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-md border border-slate-200 px-4 py-2 text-sm"
                onClick={() => setCommentModalOpen(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-md bg-amber-500 px-4 py-2 text-sm font-semibold text-white"
                onClick={handleSaveComment}
                disabled={commentLoading}
              >
                {commentLoading ? '保存中...' : '保存评语'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {homeworkTypeModal ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
            <h3 className="text-base font-semibold text-slate-800">修改作业类型</h3>
            <p className="mt-2 text-xs text-slate-500">作业：{homeworkTypeModal.folderName}</p>
            <select
              className="mt-3 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
              value={homeworkTypeModal.type}
              onChange={(event) => setHomeworkTypeModal((prev) => ({ ...prev, type: event.target.value }))}
            >
              {HOMEWORK_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {homeworkTypeError ? <p className="mt-2 text-xs text-rose-600">{homeworkTypeError}</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-md border border-slate-200 px-3 py-1 text-sm"
                onClick={() => setHomeworkTypeModal(null)}
              >
                取消
              </button>
              <button
                type="button"
                className="rounded-md bg-amber-500 px-3 py-1 text-sm font-semibold text-white"
                onClick={handleHomeworkTypeSave}
                disabled={homeworkTypeSaving}
              >
                {homeworkTypeSaving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
