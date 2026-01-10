import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout.jsx'
import RequireAuth from './auth/RequireAuth.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'
import Grading from './pages/Grading.jsx'
import RepositoryManagement from './pages/RepositoryManagement.jsx'
import AssignmentManagement from './pages/AssignmentManagement.jsx'
import GradeTypeManagement from './pages/GradeTypeManagement.jsx'
import BatchAiScore from './pages/BatchAiScore.jsx'
import BatchGrade from './pages/BatchGrade.jsx'
import CourseList from './pages/CourseList.jsx'
import ClassList from './pages/ClassList.jsx'
import CourseManagement from './pages/CourseManagement.jsx'
import SemesterManagement from './pages/SemesterManagement.jsx'
import CalendarPage from './pages/CalendarPage.jsx'
import HomeworkUpload from './pages/HomeworkUpload.jsx'
import GradeRegistryWriter from './pages/GradeRegistryWriter.jsx'
import StudentSubmission from './pages/StudentSubmission.jsx'
import SuperAdminDashboard from './pages/SuperAdminDashboard.jsx'
import TenantManagement from './pages/TenantManagement.jsx'
import TenantAdminDashboard from './pages/TenantAdminDashboard.jsx'
import TenantUserManagement from './pages/TenantUserManagement.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="/grading" element={<Grading />} />
          <Route path="/repositories" element={<RepositoryManagement />} />
          <Route path="/assignments" element={<AssignmentManagement />} />
          <Route path="/grade-types" element={<GradeTypeManagement />} />
          <Route path="/batch-ai-score" element={<BatchAiScore />} />
          <Route path="/batch-grade" element={<BatchGrade />} />
          <Route path="/courses" element={<CourseList />} />
          <Route path="/classes" element={<ClassList />} />
          <Route path="/course-management" element={<CourseManagement />} />
          <Route path="/semesters" element={<SemesterManagement />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/homework-upload" element={<HomeworkUpload />} />
          <Route path="/grade-registry" element={<GradeRegistryWriter />} />
          <Route path="/student-submission" element={<StudentSubmission />} />
          <Route path="/super-admin" element={<SuperAdminDashboard />} />
          <Route path="/tenant-management" element={<TenantManagement />} />
          <Route path="/tenant-admin" element={<TenantAdminDashboard />} />
          <Route path="/tenant-users" element={<TenantUserManagement />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
    </Routes>
  )
}
