import { useEffect } from 'react'
import { API_BASE_URL } from '../api/config.js'
import { ensureCsrfToken } from '../api/csrf.js'
import { loadExternalScript } from '../utils/loadExternalScript.js'

const staticUrl = (path) => `${API_BASE_URL}${path}`

export default function Grading() {
  useEffect(() => {
    let mounted = true

    const setup = async () => {
      await ensureCsrfToken()

      if (!mounted) {
        return
      }

      window.initialTreeData = window.initialTreeData || []
      window.currentCourse = window.currentCourse || null
      window.currentRepoId = window.currentRepoId || null

      const scripts = [
        staticUrl('/static/grading/js/comment-cache-service.js'),
        staticUrl('/static/grading/js/grading.js'),
        staticUrl('/static/grading/js/homework-type-labels.js'),
      ]

      for (const src of scripts) {
        await loadExternalScript(src)
      }

      if (window.pdfjsLib && window.pdfjsLib.GlobalWorkerOptions) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = staticUrl(
          '/static/grading/vendor/pdfjs/pdf.worker.min.js',
        )
      }
    }

    setup().catch((error) => {
      console.error('初始化评分页面失败', error)
    })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-md-3">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="bi bi-folder2-open" /> 作业
              </h5>
              <div className="mt-2">
                <button
                  type="button"
                  className="btn btn-success btn-sm me-2"
                  id="batch-grade-btn"
                  disabled
                  title="请先选择文件夹"
                >
                  <i className="bi bi-tasks" /> 批量登分
                </button>
                <button
                  type="button"
                  className="btn btn-warning btn-sm"
                  id="batch-ai-score-btn"
                  disabled
                  title="请先选择文件夹"
                >
                  <i className="bi bi-robot" /> 批量AI评分
                </button>
              </div>
              <div className="mt-2">
                <small className="text-muted">
                  <i className="bi bi-info-circle" /> 请选择文件夹以启用批量操作。
                </small>
              </div>
              <div id="batch-grade-progress-wrapper" className="mt-2" style={{ display: 'none' }}>
                <div
                  className="progress"
                  role="progressbar"
                  aria-label="批量登分进度"
                  aria-valuenow="0"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div
                    id="batch-grade-progress-bar"
                    className="progress-bar progress-bar-striped progress-bar-animated"
                    style={{ width: '0%' }}
                  >
                    准备中...
                  </div>
                </div>
                <div id="batch-grade-progress-text" className="text-muted small mt-1">
                  <i className="bi bi-hourglass-split" /> 就绪
                </div>
              </div>
              <div id="tree-loading" className="mt-2" style={{ display: 'none' }}>
                <div className="d-flex align-items-center">
                  <div className="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span className="visually-hidden">加载中...</span>
                  </div>
                  <span className="text-muted small">正在加载作业目录...</span>
                </div>
              </div>
            </div>
            <div className="card-body">
              <div id="directory-tree" />
            </div>
          </div>
        </div>
        <div className="col-md-9">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="bi bi-file-earmark-text" /> 文件内容
              </h5>
              <div className="file-count-display text-muted small">
                <i className="bi bi-files" /> <span id="directory-file-count">0</span> 个文件
              </div>
            </div>
            <div className="card-body">
              <div id="loading" style={{ display: 'none' }}>
                <div className="d-flex align-items-center justify-content-center py-5">
                  <div className="spinner-border text-primary me-3" role="status">
                    <span className="visually-hidden">加载中...</span>
                  </div>
                  <div>
                    <h5 className="mb-1">正在加载文件...</h5>
                    <p className="text-muted mb-0 small" id="loading-message">
                      请稍候。
                    </p>
                    <div
                      className="progress mt-2"
                      style={{ width: '300px', display: 'none' }}
                      id="loading-progress"
                    >
                      <div
                        className="progress-bar progress-bar-striped progress-bar-animated"
                        role="progressbar"
                        style={{ width: '0%' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div id="file-content" className="mt-3">
                <div className="alert alert-info">
                  <i className="bi bi-info-circle-fill" /> 请在左侧选择文件开始。
                </div>
              </div>
              <div id="preview-hint" className="alert alert-secondary mt-2" style={{ display: 'none' }}>
                <i className="bi bi-lightbulb" /> <span id="preview-hint-text" />
              </div>
            </div>
          </div>

          <div className="card mt-3">
            <div className="card-header">
              <h5 className="card-title mb-0">评分</h5>
            </div>
            <div className="card-body">
              <div className="d-flex justify-content-between mb-3">
                <button type="button" className="btn btn-outline-secondary" id="prev-file">
                  <i className="bi bi-arrow-left" /> 上一份
                </button>
                <button type="button" className="btn btn-outline-secondary" id="next-file">
                  下一份 <i className="bi bi-arrow-right" />
                </button>
              </div>
              <div className="d-flex align-items-center">
                <div className="btn-group me-3" role="group" aria-label="评分模式">
                  <button
                    type="button"
                    className="btn btn-outline-secondary grade-mode-btn active"
                    data-mode="letter"
                  >
                    字母
                  </button>
                  <button type="button" className="btn btn-outline-secondary grade-mode-btn" data-mode="text">
                    文字
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-secondary grade-mode-btn"
                    data-mode="percentage"
                  >
                    百分制
                  </button>
                </div>

                <div
                  className="btn-group me-3"
                  role="group"
                  aria-label="字母评分选项"
                  id="letter-grade-buttons"
                >
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="A">
                    A
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button active" data-grade="B">
                    B
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="C">
                    C
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="D">
                    D
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="E">
                    E
                  </button>
                </div>

                <div
                  className="btn-group me-3"
                  role="group"
                  aria-label="文字评分选项"
                  id="text-grade-buttons"
                  style={{ display: 'none' }}
                >
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="优秀">
                    优秀
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button active" data-grade="良好">
                    良好
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="中等">
                    中等
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="及格">
                    及格
                  </button>
                  <button type="button" className="btn btn-outline-primary grade-button" data-grade="不及格">
                    不及格
                  </button>
                </div>

                <div
                  className="input-group me-3"
                  id="percentage-grade-input"
                  style={{ display: 'none', width: '180px' }}
                >
                  <input
                    type="number"
                    className="form-control"
                    id="percentage-input"
                    min="0"
                    max="100"
                    step="0.5"
                    defaultValue="85"
                    placeholder="0-100"
                    aria-label="百分制评分"
                  />
                  <span className="input-group-text">%</span>
                </div>

                <button type="button" className="btn btn-primary me-2" id="add-grade-to-file" disabled>
                  确认
                </button>
                <button type="button" className="btn btn-outline-secondary" id="cancel-grade">
                  取消
                </button>
                <button type="button" className="btn btn-outline-info ms-2" id="teacher-comment-btn" disabled>
                  <i className="bi bi-chat-text" /> 评语
                </button>
                <button
                  type="button"
                  className="btn btn-outline-success ms-2"
                  id="ai-score-btn"
                  disabled
                  data-ai-grading-disabled="False"
                >
                  <i className="bi bi-robot" /> AI评分
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        className="modal fade"
        id="teacherCommentModal"
        tabIndex="-1"
        aria-labelledby="teacherCommentModalLabel"
        aria-hidden="true"
      >
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="teacherCommentModalLabel">
                教师评语
              </h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close" />
            </div>
            <div className="modal-body">
              <div className="mb-3" id="commentTemplatesContainer" style={{ display: 'none' }}>
                <label className="form-label">常用评语模板</label>
                <div id="commentTemplatesList" className="d-flex flex-wrap gap-2" />
                <small className="text-muted">点击模板插入评语。</small>
              </div>
              <div className="mb-3">
                <label htmlFor="teacherCommentText" className="form-label">
                  评语
                </label>
                <textarea
                  className="form-control"
                  id="teacherCommentText"
                  rows="8"
                  placeholder="输入或更新评语..."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">
                取消
              </button>
              <button type="button" className="btn btn-primary" id="saveTeacherComment">
                保存评语
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
