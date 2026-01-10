import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client.js'

export default function GradeTypeManagement() {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadConfigs = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiFetch('/grading/api/grade-types/')
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error((data && data.message) || '加载评分类型失败')
      }
      setConfigs(data.configs || [])
    } catch (err) {
      setError(err.message || '加载评分类型失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfigs()
  }, [])

  const changeGradeType = async (classIdentifier) => {
    const newGradeType = window.prompt('请输入新评分类型：letter、text 或 numeric')
    if (!newGradeType) {
      return
    }
    if (
      !window.confirm(
        `确认将 ${classIdentifier} 的评分类型改为 ${newGradeType} 吗？`,
      )
    ) {
      return
    }

    const response = await apiFetch('/grading/change-grade-type/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        class_identifier: classIdentifier,
        new_grade_type: newGradeType,
      }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || (data && data.status !== 'success')) {
      window.alert((data && data.message) || '更新评分类型失败')
      return
    }
    window.alert(data.message || '已更新')
    loadConfigs()
  }

  return (
    <div className="card">
      <div className="card-header">
        <h4 className="mb-0">评分类型管理</h4>
      </div>
      <div className="card-body">
        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? (
          <div className="alert alert-info">加载中...</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>班级标识</th>
                  <th>评分类型</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {configs.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center">
                      暂无评分类型配置。
                    </td>
                  </tr>
                ) : (
                  configs.map((config) => (
                    <tr key={config.class_identifier}>
                      <td>{config.class_identifier}</td>
                      <td>{config.grade_type_display}</td>
                      <td>
                        {config.is_locked ? (
                          <span className="badge bg-success">已锁定</span>
                        ) : (
                          <span className="badge bg-warning text-dark">未锁定</span>
                        )}
                      </td>
                      <td>
                        {config.is_locked ? (
                          <button className="btn btn-sm btn-secondary" disabled>
                            已锁定
                          </button>
                        ) : (
                          <button
                            className="btn btn-sm btn-primary"
                            type="button"
                            onClick={() => changeGradeType(config.class_identifier)}
                          >
                            修改
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
