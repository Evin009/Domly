import { contextBridge } from 'electron'

// Renderer makes direct fetch() calls to the backend.
// Expose env vars the renderer needs at runtime.
contextBridge.exposeInMainWorld('env', {
  BACKEND_URL: process.env['VITE_BACKEND_URL'] || 'http://localhost:3001',
  PICOVOICE_ACCESS_KEY: process.env['VITE_PICOVOICE_ACCESS_KEY'] || ''
})
