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
            Homework Grading
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
                  Home
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/grading">
                  Grading
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/course-management">
                  Course Management
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/courses">
                  Courses
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/classes">
                  Classes
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/calendar">
                  Calendar
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/assignments">
                  Assignments
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/student-submission">
                  Student Submission
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/homework-upload">
                  Homework Upload
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/repositories">
                  Repositories
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink className="nav-link" to="/grade-registry">
                  Grade Registry
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
                  Admin
                </a>
                <ul className="dropdown-menu" aria-labelledby="adminDropdown">
                  <li>
                    <NavLink className="dropdown-item" to="/semesters">
                      Semesters
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/grade-types">
                      Grade Types
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/batch-ai-score">
                      Batch AI Score
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/batch-grade">
                      Batch Grade
                    </NavLink>
                  </li>
                  {user?.is_tenant_admin ? (
                    <li>
                      <NavLink className="dropdown-item" to="/tenant-admin">
                        Tenant Admin
                      </NavLink>
                    </li>
                  ) : null}
                  {user?.is_tenant_admin ? (
                    <li>
                      <NavLink className="dropdown-item" to="/tenant-users">
                        Tenant Users
                      </NavLink>
                    </li>
                  ) : null}
                  {user?.is_superuser ? (
                    <li>
                      <NavLink className="dropdown-item" to="/super-admin">
                        Super Admin
                      </NavLink>
                    </li>
                  ) : null}
                  <li>
                    <hr className="dropdown-divider" />
                  </li>
                  <li>
                    <a className="dropdown-item" href="/admin/" target="_blank" rel="noreferrer">
                      Django Admin
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
                  {user?.username || 'User'}
                </a>
                <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                  <li>
                    <button className="dropdown-item" type="button" onClick={handleLogout}>
                      Logout
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
