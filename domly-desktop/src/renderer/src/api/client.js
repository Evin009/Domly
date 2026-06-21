const BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3001'

let _token = null

export const setToken = (t) => { _token = t }
export const getToken = () => _token
export const clearToken = () => { _token = null }

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(_token ? { Authorization: `Bearer ${_token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Request failed')
  return data
}

export const api = {
  login:              (sr_email, sr_password) => request('POST', '/auth/login', { sr_email, sr_password }),
  me:                 ()          => request('GET',  '/auth/me'),
  enrollmentComplete: ()          => request('POST', '/voice/enrollment-complete'),
  runCommand:         (command)   => request('POST', '/commands/run', { command })
}
