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
    if (!window.confirm(`确认将 ${classIdentifier} 的评分类型改为 ${newGradeType} 吗？`)) {
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
    <div className="min-h-screen">
      <div className="page-shell max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">评分类型管理</h1>
          <p className="mt-1 text-sm text-slate-500">查看并更新班级的评分类型。</p>
        </header>

        <section className="card-surface p-5">
          {error ? (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          {loading ? (
            <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
              加载中...
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-100 text-slate-600">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">班级标识</th>
                    <th className="px-4 py-2 text-left font-medium">评分类型</th>
                    <th className="px-4 py-2 text-left font-medium">状态</th>
                    <th className="px-4 py-2 text-left font-medium">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {configs.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-4 py-6 text-center text-sm text-slate-500">
                        暂无评分类型配置。
                      </td>
                    </tr>
                  ) : (
                    configs.map((config) => (
                      <tr key={config.class_identifier} className="text-slate-700">
                        <td className="px-4 py-2 font-medium text-slate-800">{config.class_identifier}</td>
                        <td className="px-4 py-2">{config.grade_type_display}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              config.is_locked
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-amber-100 text-amber-700'
                            }`}
                          >
                            {config.is_locked ? '已锁定' : '未锁定'}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          {config.is_locked ? (
                            <button
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-400"
                              disabled
                            >
                              已锁定
                            </button>
                          ) : (
                            <button
                              className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800"
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
        </section>
      </div>
    </div>
  )
}
