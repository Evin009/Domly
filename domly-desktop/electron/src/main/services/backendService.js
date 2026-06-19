import { BACKEND_URL } from '../config/constants'

async function post(path, body) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Request failed')
  return data
}

async function get(path, token) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Request failed')
  return data
}

export const backendService = {
  signup: (payload) => post('/auth/signup', payload),
  login: (payload) => post('/auth/login', payload),
  getCredentials: (token) => get('/auth/credentials', token)
}
