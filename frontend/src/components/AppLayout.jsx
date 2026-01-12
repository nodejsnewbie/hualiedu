import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { useAuth } from '../auth/AuthProvider.jsx'

const primaryLinks = [
  { to: '/', label: '首页' },
  { to: '/grading', label: '评分' },
  { to: '/course-management', label: '课程管理' },
  { to: '/courses', label: '课程列表' },
  { to: '/classes', label: '班级管理' },
  { to: '/calendar', label: '课程表' },
  { to: '/assignments', label: '作业管理' },
  { to: '/student-submission', label: '作业提交' },
  { to: '/homework-upload', label: '作业上传' },
  { to: '/grade-registry', label: '成绩登记' },
  { to: '/toolbox', label: '工具箱' },
]

const adminLinks = [
  { to: '/semesters', label: '学期管理' },
  { to: '/grade-types', label: '评分类型' },
  { to: '/batch-ai-score', label: '批量AI评分' },
  { to: '/batch-grade', label: '批量登分' },
]

const navLinkClass = ({ isActive }) =>
  `rounded-full px-4 py-2 text-sm font-medium tracking-tight transition ${
    isActive
      ? 'bg-amber-300 text-slate-950 shadow-[0_8px_20px_-12px_rgba(245,158,11,0.9)]'
      : 'text-slate-200 hover:bg-white/10 hover:text-white'
  }`

const dropdownLinkClass = ({ isActive }) =>
  `block rounded-lg px-3 py-2 text-sm transition ${
    isActive ? 'bg-amber-50 text-slate-900' : 'text-slate-700 hover:bg-slate-100'
  }`

export default function AppLayout() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)
  const [userOpen, setUserOpen] = useState(false)

  const handleLogout = async () => {
    await apiFetch('/grading/api/auth/logout/', { method: 'POST' })
    setUser(null)
    navigate('/login')
  }

  return (
    <div className="min-h-screen text-slate-900">
      <nav className="sticky top-0 z-40 border-b border-slate-900/10 bg-slate-950/95 text-slate-100 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <Link className="text-lg font-semibold tracking-tight" to="/">
            <span className="bg-gradient-to-r from-amber-200 via-amber-100 to-cyan-200 bg-clip-text text-transparent">
              作业评分系统
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-full border border-slate-700 px-3 py-2 text-sm font-medium text-slate-100 hover:bg-slate-900/80 sm:hidden"
              onClick={() => setMenuOpen((prev) => !prev)}
              aria-expanded={menuOpen}
            >
              菜单
            </button>
            <div className="relative hidden sm:block">
              <button
                type="button"
                className="flex items-center gap-2 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-100 hover:bg-slate-900/80"
                onClick={() => setUserOpen((prev) => !prev)}
              >
                <span>{user?.username || '用户'}</span>
                <span className="text-xs opacity-70">v</span>
              </button>
              {userOpen ? (
                <div className="absolute right-0 mt-2 w-44 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-xl">
                  <button
                    className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
                    type="button"
                    onClick={handleLogout}
                  >
                    退出登录
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <div className="border-t border-slate-900/20">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:flex-wrap sm:items-center sm:px-6 lg:px-8">
            <div className={`${menuOpen ? 'flex' : 'hidden'} flex-col gap-2 sm:flex sm:flex-row sm:flex-wrap`}>
              {primaryLinks.map((link) => (
                <NavLink key={link.to} to={link.to} className={navLinkClass}>
                  {link.label}
                </NavLink>
              ))}
            </div>
            <div className="relative">
              <button
                type="button"
                className="flex items-center gap-2 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-100 hover:bg-slate-900/80"
                onClick={() => setAdminOpen((prev) => !prev)}
              >
                管理
                <span className="text-xs opacity-70">v</span>
              </button>
              {adminOpen ? (
                <div className="absolute left-0 mt-2 w-52 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-xl">
                  {adminLinks.map((link) => (
                    <NavLink key={link.to} to={link.to} className={dropdownLinkClass}>
                      {link.label}
                    </NavLink>
                  ))}
                  {user?.is_tenant_admin ? (
                    <NavLink to="/tenant-admin" className={dropdownLinkClass}>
                      租户管理
                    </NavLink>
                  ) : null}
                  {user?.is_tenant_admin ? (
                    <NavLink to="/tenant-users" className={dropdownLinkClass}>
                      租户用户
                    </NavLink>
                  ) : null}
                  {user?.is_superuser ? (
                    <NavLink to="/super-admin" className={dropdownLinkClass}>
                      超级管理员
                    </NavLink>
                  ) : null}
                  <a
                    className="mt-2 block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
                    href="/admin/"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Django 后台
                  </a>
                </div>
              ) : null}
            </div>
            <div className="sm:hidden">
              <button
                type="button"
                className="w-full rounded-full border border-slate-700 px-3 py-2 text-left text-sm text-slate-100 hover:bg-slate-900/80"
                onClick={handleLogout}
              >
                退出登录
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto w-full max-w-7xl px-4 pb-12 pt-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
