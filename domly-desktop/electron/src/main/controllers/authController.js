import { backendService } from '../services/backendService'

export const authController = {
  register(ipcMain) {
    ipcMain.handle('auth:signup', async (_event, payload) => {
      try {
        const { token } = await backendService.signup(payload)
        return { success: true, token }
      } catch (err) {
        return { success: false, error: err.message }
      }
    })

    ipcMain.handle('auth:login', async (_event, payload) => {
      try {
        const { token } = await backendService.login(payload)
        return { success: true, token }
      } catch (err) {
        return { success: false, error: err.message }
      }
    })
  }
}
