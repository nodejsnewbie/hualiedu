import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { useAuth } from '../auth/AuthProvider.jsx'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { setUser } = useAuth()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const response = await apiFetch('/grading/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        setError((data && data.message) || '登录失败')
        return
      }

      setUser(data.user)
      const destination = location.state?.from?.pathname || '/'
      navigate(destination)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-[calc(100vh-120px)] items-center justify-center overflow-hidden px-4 py-12">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-10%] top-[-20%] h-[420px] w-[420px] rounded-full bg-amber-300/30 blur-[120px]" />
        <div className="absolute right-[-15%] top-[10%] h-[520px] w-[520px] rounded-full bg-cyan-300/30 blur-[140px]" />
        <div className="absolute bottom-[-20%] left-[20%] h-[420px] w-[420px] rounded-full bg-rose-300/25 blur-[140px]" />
      </div>
      <div className="relative grid w-full max-w-4xl overflow-hidden rounded-[28px] border border-slate-200/60 bg-white/80 shadow-[0_40px_90px_-55px_rgba(15,23,42,0.65)] backdrop-blur md:grid-cols-[1.1fr_0.9fr]">
        <div className="relative hidden flex-col justify-between gap-10 bg-slate-950 px-8 py-10 text-white md:flex">
          <div className="absolute inset-0">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.35),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(34,211,238,0.3),_transparent_60%)]" />
            <div className="absolute inset-0 bg-[linear-gradient(135deg,_rgba(15,23,42,0.4),_rgba(15,23,42,0.9))]" />
          </div>
          <div className="relative space-y-4">
            <span className="inline-flex items-center rounded-full border border-white/20 px-3 py-1 text-xs uppercase tracking-[0.24em] text-amber-200">
              Practicum Studio
            </span>
            <h1 className="text-3xl font-semibold leading-tight">实训作业评分平台</h1>
            <p className="text-sm text-slate-200">
              统一管理课程、作业与批量评分，让实训流程更清晰、更高效。
            </p>
          </div>
          <div className="relative space-y-3 text-xs text-slate-300">
            <p>- 自动解析课程与班级目录</p>
            <p>- 一键批量解压与导入成绩</p>
            <p>- 评分与评语集中维护</p>
          </div>
        </div>
        <div className="p-8 md:p-10">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-slate-900">登录</h1>
            <p className="text-sm text-slate-500">使用教学平台账号登录评分系统。</p>
          </div>

          {error ? (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
              {error}
            </div>
          ) : null}

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="username">
                用户名
              </label>
              <input
                id="username"
                className="w-full px-3 py-2 text-sm"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="password">
                密码
              </label>
              <input
                id="password"
                type="password"
                className="w-full px-3 py-2 text-sm"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            <button
              className="btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-60"
              type="submit"
              disabled={submitting}
            >
              {submitting ? '正在登录...' : '登录'}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-between text-xs text-slate-400">
            <span>Powered by 实训评分系统</span>
            <a
              className="font-medium text-amber-600 hover:text-amber-700"
              href="/admin/login/"
              target="_blank"
              rel="noreferrer"
            >
              Django 后台登录
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
