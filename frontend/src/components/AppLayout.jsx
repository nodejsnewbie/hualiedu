import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client.js'
import { useAuth } from '../auth/AuthProvider.jsx'

export default function AppLayout() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await apiFetch('/grading/api/auth/logout/', { method: 'POST' })
    setUser(null)
    navigate('/login')
  }

  return (
    <div>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">
            作业评分
          </Link>
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarNav"
            aria-controls="navbarNav"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon" />
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav">
              <li className="nav-item">
                <NavLink className="nav-link" to="/">
                  首页
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/grading">
                  评分
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/course-management">
                  课程管理
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/courses">
                  课程列表
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/classes">
                  班级列表
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/calendar">
                  日历
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/assignments">
                  作业管理
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/student-submission">
                  学生作业
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/homework-upload">
                  作业上传
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/grade-registry">
                  成绩登记册
                </NavLink>
              </li>
              <li className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle"
                  href="#"
                  id="adminDropdown"
                  role="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  管理
                </a>
                <ul className="dropdown-menu" aria-labelledby="adminDropdown">
                  <li>
                    <NavLink className="dropdown-item" to="/semesters">
                      学期管理
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/grade-types">
                      评分类型
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/batch-ai-score">
                      批量AI评分
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/batch-grade">
                      批量登分
                    </NavLink>
                  </li>
                  {user?.is_tenant_admin ? (
                    <li>
                      <NavLink className="dropdown-item" to="/tenant-admin">
                        租户管理
                      </NavLink>
                    </li>
                  ) : null}
                  {user?.is_tenant_admin ? (
                    <li>
                      <NavLink className="dropdown-item" to="/tenant-users">
                        租户用户
                      </NavLink>
                    </li>
                  ) : null}
                  {user?.is_superuser ? (
                    <li>
                      <NavLink className="dropdown-item" to="/super-admin">
                        超级管理员
                      </NavLink>
                    </li>
                  ) : null}
                  <li>
                    <hr className="dropdown-divider" />
                  </li>
                  <li>
                    <a className="dropdown-item" href="/admin/" target="_blank" rel="noreferrer">
                      Django 管理后台
                    </a>
                  </li>
                </ul>
              </li>
            </ul>
            <ul className="navbar-nav ms-auto">
              <li className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle"
                  href="#"
                  id="userDropdown"
                  role="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  {user?.username || '用户'}
                </a>
                <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                  <li>
                    <button className="dropdown-item" type="button" onClick={handleLogout}>
                      退出登录
                    </button>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <main className="container mt-4">
        <Outlet />
      </main>
    </div>
  )
}
