import { buildApiUrl } from './config.js'
import { ensureCsrfToken, getCsrfToken } from './csrf.js'

const requiresCsrf = (method) => !['GET', 'HEAD', 'OPTIONS'].includes(method)

export const apiFetch = async (path, options = {}) => {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})

  if (requiresCsrf(method)) {
    await ensureCsrfToken()
    const token = getCsrfToken()
    if (token) {
      headers.set('X-CSRFToken', token)
    }
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    method,
    headers,
    credentials: 'include',
  })

  return response
}
