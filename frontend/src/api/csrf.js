import { buildApiUrl } from './config.js'

const getCookie = (name) => {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    return parts.pop().split(';').shift()
  }
  return ''
}

export const getCsrfToken = () => getCookie('csrftoken')

export const ensureCsrfToken = async () => {
  const existing = getCsrfToken()
  if (existing) {
    return existing
  }

  const response = await fetch(buildApiUrl('/grading/api/auth/csrf/'), {
    method: 'GET',
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Failed to initialize CSRF token')
  }

  return getCsrfToken()
}
